import os, uuid, time, cv2, numpy as np
from datetime import datetime
from fastapi import FastAPI, UploadFile, Form, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SASession
from typing import Optional, Dict, Tuple

from backend.db_models import Base, User, Student, Session as DBSession, Behavior
from backend.auth import verify_jwt, ensure_bootstrap_teacher, create_user, login as auth_login
from backend.helpers import preprocess_face, simple_embedding, cosine_similarity
from backend.detection import FaceDetector, draw_boxes
from backend.behavior import classify_behavior

DB_URL = "sqlite:///db.sqlite3"
engine = create_engine(DB_URL, echo=False, future=True)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "*"
]

app = FastAPI(title="School Behavior AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

detector = FaceDetector()

# once per session tracking: attentive/absent
_saved_once: Dict[Tuple[int,int,str], bool] = {}
SAVE_INTERVAL = 30
_last_saved: Dict[Tuple[int,int,str], float] = {}

def get_db():
    db = SessionLocal()
    try:
        ensure_bootstrap_teacher(db)
        yield db
    finally:
        db.close()

# ---- Auth (inner style) ------------------------------------------------------

def require_auth(request: Request, token: str = Query(None, alias="auth")):
    if not token:
        hdr = request.headers.get("Authorization", "")
        if hdr.startswith("Bearer "):
            token = hdr.replace("Bearer ", "").strip()
    if token and token.startswith("Bearer "):
        token = token.replace("Bearer ", "").strip()
    return token

def get_user(token: Optional[str] = Depends(require_auth)):
    def inner(request: Request):
        t = token
        if not t:
            hdr = request.headers.get("Authorization", "")
            if hdr.startswith("Bearer "):
                t = hdr.replace("Bearer ", "").strip()
        if not t:
            raise HTTPException(401, "Unauthorized")
        try:
            return verify_jwt(t)
        except Exception:
            raise HTTPException(401, "Unauthorized")
    return inner

# convenience dependency to resolve the inner()
def get_current_user(request: Request, get_user_fn = Depends(get_user)):
    return get_user_fn(request)

# ---- Routes ------------------------------------------------------------------

@app.post("/auth/login")
def login(email: str = Form(...), password: str = Form(...), db: SASession = Depends(get_db)):
    res = auth_login(db, email, password)
    if "error" in res:
        raise HTTPException(401, res["error"])
    return res

@app.post("/users")  # teacher creates teachers or parents
def create_user_account(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    is_teacher: bool = Form(...),
    db: SASession = Depends(get_db),
    u = Depends(get_current_user)
):
    if not u.get("is_teacher"):
        raise HTTPException(403, "forbidden")
    res = create_user(db, name, email, password, is_teacher)
    if "error" in res:
        raise HTTPException(409, res["error"])
    return res

@app.post("/students")
def add_student(
    full_name: str = Form(...),
    class_name: str = Form(""),
    parent_email: str = Form(""),
    photo: UploadFile = None,
    db: SASession = Depends(get_db),
    u = Depends(get_current_user)
):
    if not u.get("is_teacher"):
        raise HTTPException(403, "forbidden")
    if not photo:
        raise HTTPException(422, "photo required")

    img = cv2.imdecode(np.frombuffer(photo.file.read(), np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "invalid image")

    face = cv2.resize(img, (112, 112))
    emb = simple_embedding(face)
    emb_str = ",".join([f"{v:.6f}" for v in emb])

    os.makedirs("images", exist_ok=True)
    filename = f"{uuid.uuid4()}{os.path.splitext(photo.filename or '.jpg')[1] or '.jpg'}"
    path = os.path.join("images", filename)
    cv2.imwrite(path, img)

    parent_id = None
    if parent_email:
        parent = db.query(User).filter(User.email == parent_email).first()
        if not parent:
            from backend.auth import hash_pw
            rand_pw = uuid.uuid4().hex[:10]
            parent = User(
                name=parent_email.split("@")[0],
                email=parent_email,
                password_hash=hash_pw(rand_pw),
                is_teacher=False
            )
            db.add(parent); db.flush()
        parent_id = parent.id

    s = Student(full_name=full_name, class_name=class_name, photo_path=path, embedding=emb_str, parent_id=parent_id)
    db.add(s); db.commit()
    return {"id": s.id, "full_name": s.full_name, "photo": os.path.basename(s.photo_path)}

@app.get("/students")
def list_students(db: SASession = Depends(get_db), u = Depends(get_current_user)):
    if u.get("is_teacher"):
        studs = db.query(Student).all()
    else:
        me = db.query(User).get(u["sub"])
        studs = db.query(Student).filter(Student.parent_id == me.id).all()
    return [{
        "id": s.id,
        "full_name": s.full_name,
        "class_name": s.class_name,
        "photo": os.path.basename(s.photo_path) if s.photo_path else None
    } for s in studs]

@app.get("/students/{student_id}")
def get_student(student_id: int, db: SASession = Depends(get_db), u = Depends(get_current_user)):
    s = db.query(Student).get(student_id)
    if not s:
        raise HTTPException(404, "not found")
    if not u.get("is_teacher") and s.parent_id != u["sub"]:
        raise HTTPException(403, "forbidden")
    return {
        "id": s.id,
        "full_name": s.full_name,
        "class_name": s.class_name,
        "photo": os.path.basename(s.photo_path) if s.photo_path else None,
        "parent_id": s.parent_id,
        "behaviors": [
            {"id": b.id, "session_id": b.session_id, "behavior": b.behavior,
             "confidence": b.confidence, "timestamp": b.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
            for b in s.behaviors
        ]
    }

@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: SASession = Depends(get_db), u = Depends(get_current_user)):
    if not u.get("is_teacher"):
        raise HTTPException(403, "forbidden")
    s = db.query(Student).get(student_id)
    if not s:
        raise HTTPException(404, "not found")
    for b in s.behaviors:
        db.delete(b)
    db.delete(s); db.commit()
    return {"ok": True}

@app.post("/sessions/start")
def start_session(db: SASession = Depends(get_db), u = Depends(get_current_user)):
    if not u.get("is_teacher"):
        raise HTTPException(403, "forbidden")
    sess = DBSession(teacher_id=u["sub"], active=True)
    db.add(sess); db.commit()
    return {"session_id": sess.id, "start_time": sess.start_time.isoformat()}

@app.post("/sessions/stop/{session_id}")
def stop_session(session_id: int, db: SASession = Depends(get_db), u = Depends(get_current_user)):
    if not u.get("is_teacher"):
        raise HTTPException(403, "forbidden")
    sess = db.query(DBSession).get(session_id)
    if not sess or not sess.active:
        raise HTTPException(404, "not active")
    sess.active = False
    sess.end_time = datetime.utcnow()
    db.commit()
    return {"ok": True}

@app.get("/sessions")
def my_sessions(db: SASession = Depends(get_db), u = Depends(get_current_user)):
    if not u.get("is_teacher"):
        sid_list = (
            db.query(Behavior.session_id)
              .join(Student, Student.id == Behavior.student_id)
              .filter(Student.parent_id == u["sub"])
              .distinct()
              .all()
        )
        ids = [sid for (sid,) in sid_list]
        sess = db.query(DBSession).filter(DBSession.id.in_(ids)).all()
    else:
        sess = db.query(DBSession).filter(DBSession.teacher_id == u["sub"]).all()
    return [{
        "id": s.id, "active": s.active,
        "start_time": s.start_time.isoformat(),
        "end_time": s.end_time.isoformat() if s.end_time else None
    } for s in sess]

@app.get("/detect/stream")
def detect_stream(
    session_id: int = Query(...),
    db: SASession = Depends(get_db),
    u = Depends(get_current_user)
):
    if not u.get("is_teacher"):
        raise HTTPException(403, "forbidden")
    sess = db.query(DBSession).get(session_id)
    if not sess or not sess.active:
        raise HTTPException(404, "session not active")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise HTTPException(500, "camera not available")

    def gen():
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            faces = detector.predict(frame)

            labels = []
            studs = db.query(Student).all()
            for f in faces:
                crop = preprocess_face(frame, f["bbox"])
                if crop is None:
                    labels.append("unknown")
                    continue
                emb = simple_embedding(crop)

                best, best_name, best_sim = None, "unknown", 0.0
                for s in studs:
                    if not s.embedding:
                        continue
                    ref = np.array([float(x) for x in s.embedding.split(",")], dtype=np.float32)
                    sim = cosine_similarity(emb, ref)
                    if sim > best_sim:
                        best_sim, best, best_name = sim, s, s.full_name

                if best and best_sim > 0.5:
                    labels.append(f"{best_name} ({best_sim:.2f})")
                    behavior = classify_behavior(frame, f["bbox"], f.get("landmarks", []), student_key=str(best.id))

                    key_once = (session_id, best.id, behavior)
                    if behavior in ("attentive", "absent"):
                        if not _saved_once.get(key_once):
                            db.add(Behavior(session_id=session_id, student_id=best.id,
                                            behavior=behavior, confidence=float(best_sim)))
                            db.commit()
                            _saved_once[key_once] = True
                    else:
                        key_ts = (session_id, best.id, behavior)
                        now = time.time()
                        last = _last_saved.get(key_ts, 0.0)
                        if now - last > SAVE_INTERVAL:
                            db.add(Behavior(session_id=session_id, student_id=best.id,
                                            behavior=behavior, confidence=float(best_sim)))
                            db.commit()
                            _last_saved[key_ts] = now
                else:
                    labels.append("unknown")

            annotated = draw_boxes(frame.copy(), faces, labels)
            ok2, buf = cv2.imencode(".jpg", annotated)
            if not ok2:
                continue
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")

    return StreamingResponse(gen(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/images/{filename}")
def serve_image(filename: str):
    path = os.path.join("images", filename)
    if not os.path.exists(path):
        raise HTTPException(404, "not found")
    return FileResponse(path)

@app.get("/me")
def me(u = Depends(get_current_user)):
    return u

@app.get("/")
def root():
    return HTMLResponse("<h3>School Behavior AI API</h3>")
