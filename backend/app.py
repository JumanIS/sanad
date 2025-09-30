import os, io, cv2, json, uuid, time
import numpy as np
from functools import wraps
from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.db_models import Base, Teacher, Student, Behavior
from backend.auth import issue_jwt, verify_jwt, hash_pw, check_pw, ensure_admin
from backend.detection import FaceDetector, draw_boxes
from backend.helpers import preprocess_face, simple_embedding, cosine_similarity
from backend.behavior import classify_behavior

DB_URL = "sqlite:///db.sqlite3"
engine = create_engine(DB_URL, echo=False, future=True)
JWT_COOKIE = "token"

engine = create_engine(DB_URL, echo=False, future=True)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

app = Flask(__name__, static_folder="static")
CORS(app)

detector = FaceDetector()

last_saved = {}
SAVE_INTERVAL = 30

def auth_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        token = None
        # 1) Check Authorization header
        hdr = request.headers.get("Authorization", "")
        if hdr.startswith("Bearer "):
            token = hdr.replace("Bearer ", "").strip()
        # 2) Check cookie
        if not token and JWT_COOKIE in request.cookies:
            token = request.cookies.get(JWT_COOKIE)
        # 3) Check query param (for <img> and <video>)
        if not token and "auth" in request.args:
            q = request.args.get("auth")
            if q.startswith("Bearer "):
                token = q.replace("Bearer ", "").strip()
            else:
                token = q
        if not token:
            return jsonify({"message":"Unauthorized"}), 401
        try:
            request.user = verify_jwt(token)
        except Exception:
            return jsonify({"message":"Unauthorized"}), 401
        return f(*args, **kwargs)
    return wrap


@app.post("/auth/register")
def register():
    data = request.get_json(force=True)
    name = data.get("name"); email = data.get("email"); pw = data.get("password")
    if not all([name, email, pw]):
        return jsonify({"message":"name, email, password required"}), 422
    db = SessionLocal()
    try:
        if db.query(Teacher).filter(Teacher.email==email).first():
            return jsonify({"message":"email exists"}), 409
        t = Teacher(name=name, email=email, password_hash=hash_pw(pw))
        db.add(t); db.commit()
        return jsonify({"ok": True})
    finally:
        db.close()

@app.post("/auth/login")
def login():
    data = request.get_json(force=True)
    email = data.get("email"); pw = data.get("password")
    db = SessionLocal()
    try:
        ensure_admin(db)
        t = db.query(Teacher).filter(Teacher.email==email).first()
        if not t or not check_pw(pw, t.password_hash):
            return jsonify({"message":"invalid credentials"}), 401
        token = issue_jwt(t.id, t.email)
        return jsonify({"token": token})
    finally:
        db.close()

@app.post("/students")
@auth_required
def add_student():
    # multipart form: full_name, class_name, photo (file)
    full_name = request.form.get("full_name")
    class_name = request.form.get("class_name")
    photo = request.files.get("photo")
    if not full_name or not photo:
        return jsonify({"message": "full_name and photo required"}), 422

    # read image into OpenCV
    img = cv2.imdecode(np.frombuffer(photo.read(), np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return jsonify({"message": "invalid image"}), 400

    # embed full face (placeholder embedding for now)
    face = cv2.resize(img, (112, 112))
    emb = simple_embedding(face)
    emb_str = ",".join([f"{v:.6f}" for v in emb])

    # ensure images dir exists
    os.makedirs("images", exist_ok=True)

    # generate unique filename using UUID
    ext = os.path.splitext(photo.filename)[1].lower() or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    save_path = os.path.join("images", filename)

    # save image
    cv2.imwrite(save_path, img)

    # save to DB
    db = SessionLocal()
    try:
        s = Student(
            full_name=full_name,
            class_name=class_name,
            photo_path=save_path,
            embedding=emb_str
        )
        db.add(s)
        db.commit()
        return jsonify({"id": s.id, "full_name": s.full_name, "photo": filename})
    finally:
        db.close()

@app.get("/students")
@auth_required
def list_students():
    db = SessionLocal()
    try:
        studs = db.query(Student).all()
        return jsonify([{
            "id": s.id,
            "full_name": s.full_name,
            "class_name": s.class_name,
            "photo": os.path.basename(s.photo_path)
        } for s in studs])
    finally:
        db.close()

@app.get("/students/<int:student_id>")
@auth_required
def get_student(student_id):
    db = SessionLocal()
    try:
        s = db.query(Student).filter(Student.id==student_id).first()
        if not s:
            return jsonify({"message":"not found"}), 404
        return jsonify({
            "id": s.id,
            "full_name": s.full_name,
            "class_name": s.class_name,
            "photo": os.path.basename(s.photo_path),
            "behaviors": [
                {"id": b.id, "behavior": b.behavior, "confidence": b.confidence, "timestamp": b.timestamp.isoformat()}
                for b in s.behaviors
            ]
        })
    finally:
        db.close()

@app.delete("/students/<int:student_id>")
@auth_required
def delete_student(student_id):
    db = SessionLocal()
    try:
        s = db.query(Student).filter(Student.id==student_id).first()
        if not s:
            return jsonify({"message":"not found"}), 404
        for b in s.behaviors:
            db.delete(b)
        db.delete(s); db.commit()
        return jsonify({"ok":True})
    finally:
        db.close()

@app.get("/detect/stream")
@auth_required
def stream():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return jsonify({"message":"camera not available"}), 500

    def gen():
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            faces = detector.predict(frame)

            labels = []
            # naive recognition: compare simple embedding with stored student embeddings
            db = SessionLocal()
            try:
                studs = db.query(Student).all()
                for f in faces:
                    crop = preprocess_face(frame, f["bbox"])
                    if crop is None:
                        labels.append("unknown")
                        continue
                    emb = simple_embedding(crop)
                    best_student, best_name, best_sim = None, "unknown", 0.0
                    for s in studs:
                        if not s.embedding:
                            continue
                        ref = np.array([float(x) for x in s.embedding.split(",")], dtype=np.float32)
                        sim = cosine_similarity(emb, ref)
                        if sim > best_sim:
                            best_sim, best_student, best_name = sim, s, s.full_name

                    if best_student and best_sim > 0.5:  # threshold
                        labels.append(f"{best_name} ({best_sim:.2f})")

                        # classify behavior
                        landmarks = f.get("landmarks", [])
                        behavior = classify_behavior(frame, f["bbox"], landmarks)

                        # save if not attentive
                        if behavior != "attentive":
                            key = (best_student.id, behavior)
                            now = time.time()

                            if key not in last_saved or (now - last_saved[key]) > SAVE_INTERVAL:
                                rec = Behavior(
                                    student_id=best_student.id,
                                    behavior=behavior,
                                    confidence=float(best_sim)
                                )
                                db.add(rec)
                                db.commit()
                                last_saved[key] = now
                    else:
                        labels.append("unknown")
#                     labels.append(f"{best_name} ({best_sim:.2f})" if best_name!="unknown" else "unknown")
            finally:
                db.close()

            annotated = draw_boxes(frame.copy(), faces, labels)
            ret, buf = cv2.imencode(".jpg", annotated)
            if not ret:
                continue
            jpg = buf.tobytes()
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n")
    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.get("/")
def root():
    return send_from_directory("../frontend", "index.html")

@app.get("/<path:filename>")
def frontend_files(filename):
    return send_from_directory("../frontend", filename)

@app.get("/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), "..", "images"),
        filename
    )
if __name__ == "__main__":
    app.run(host="localhost", port=8000)
