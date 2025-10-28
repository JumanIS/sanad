import os, uuid, time, cv2, numpy as np
from datetime import datetime
from fastapi import FastAPI, UploadFile, Form, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SASession
from typing import Optional, Dict, Tuple

from backend.db_models import Base, User, Student, Session as DBSession, Behavior
from backend.auth import verify_jwt, ensure_bootstrap_teacher, create_user, login as auth_login
from backend.helpers import preprocess_face, simple_embedding, cosine_similarity
from backend.detection import FaceDetector, draw_boxes
from backend.behavior import classify_behavior
from fastapi.responses import StreamingResponse
import cv2, numpy as np, time
from io import BytesIO

DB_URL = "sqlite:///db.sqlite3"
engine = create_engine(DB_URL, echo=False, future=True)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://192.168.0.166",
    "*"
]

app = FastAPI(title="SANAD")
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
# ===============================
# LOGIN
# ===============================
@app.post("/auth/login")
def login(email: str = Form(...), password: str = Form(...), db: SASession = Depends(get_db)):
    res = auth_login(db, email, password)
    if "error" in res:
        raise HTTPException(401, res["error"])
    return res

# ===============================
# USERS
# ===============================
@app.get("/users")
def list_users(db: SASession = Depends(get_db), u=Depends(get_current_user)):
    if not u.get("is_teacher"):
        raise HTTPException(403, "forbidden")
    users = db.query(User).all()
    return [user.to_dict() for user in users]


@app.get("/users/{user_id}")
def get_user(user_id: int, db: SASession = Depends(get_db), u=Depends(get_current_user)):
    if not u.get("is_teacher"):
        raise HTTPException(403, "forbidden")
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(404, "user not found")
    return user.to_dict()


@app.post("/users")
def create_user_account(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    is_teacher: bool = Form(...),
    db: SASession = Depends(get_db),
    u=Depends(get_current_user)
):
    if not u.get("is_teacher"):
        raise HTTPException(403, "forbidden")
    res = create_user(db, name, email, password, is_teacher)
    if "error" in res:
        raise HTTPException(409, res["error"])
    return res


@app.put("/users/{user_id}")
def update_user(
    user_id: int,
    name: str = Form(None),
    email: str = Form(None),
    password: str = Form(None),
    is_teacher: bool = Form(None),
    db: SASession = Depends(get_db),
    u=Depends(get_current_user)
):
    if not u.get("is_teacher"):
        raise HTTPException(403, "forbidden")
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(404, "user not found")
    if name: user.name = name
    if email: user.email = email
    if password: user.password_hash = hash_password(password)
    if is_teacher is not None: user.is_teacher = is_teacher
    db.commit()
    return user.to_dict()


@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: SASession = Depends(get_db), u=Depends(get_current_user)):
    if not u.get("is_teacher"):
        raise HTTPException(403, "forbidden")
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(404, "user not found")
    db.delete(user)
    db.commit()
    return {"status": "deleted"}

# ===============================
# STUDENTS
# ===============================
@app.get("/students")
def list_students(db: SASession = Depends(get_db), u = Depends(get_current_user)):
    if u.get("is_teacher"):
        studs = db.query(Student).all()
    else:
        studs = db.query(Student).filter(Student.parent_id == u["sub"]).all()
    return [s.to_dict() for s in studs]

@app.get("/students/{student_id}")
def get_student(student_id: int, db: SASession = Depends(get_db), u = Depends(get_current_user)):
    s = db.query(Student).get(student_id)
    if not s:
        raise HTTPException(404, "not found")
    if not u.get("is_teacher") and s.parent_id != u["sub"]:
        raise HTTPException(403, "forbidden")
    return s.to_dict(include_behaviors=True)

@app.post("/students")
def create_student(
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
    filename = f"{uuid.uuid4()}{os.path.splitext(photo.filename or '.jpg')[1]}"
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
            db.add(parent)
            db.flush()
        parent_id = parent.id

    s = Student(
        full_name=full_name,
        class_name=class_name,
        photo_path=path,
        embedding=emb_str,
        parent_id=parent_id
    )
    db.add(s)
    db.commit()
    return s.to_dict()

@app.put("/students/{student_id}")
def update_student(
    student_id: int,
    full_name: str = Form(None),
    class_name: str = Form(None),
    parent_email: str = Form(None),
    photo: UploadFile = None,
    db: SASession = Depends(get_db),
    u = Depends(get_current_user)
):
    if not u.get("is_teacher"):
        raise HTTPException(403, "forbidden")
    s = db.query(Student).get(student_id)
    if not s:
        raise HTTPException(404, "not found")

    if full_name: s.full_name = full_name
    if class_name: s.class_name = class_name

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
            db.add(parent)
            db.flush()
        s.parent_id = parent.id

    if photo:
        img = cv2.imdecode(np.frombuffer(photo.file.read(), np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(400, "invalid image")
        os.makedirs("images", exist_ok=True)
        filename = f"{uuid.uuid4()}{os.path.splitext(photo.filename or '.jpg')[1]}"
        path = os.path.join("images", filename)
        cv2.imwrite(path, img)
        s.photo_path = path

    db.commit()
    return s.to_dict()


@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: SASession = Depends(get_db), u = Depends(get_current_user)):
    if not u.get("is_teacher"):
        raise HTTPException(403, "forbidden")
    s = db.query(Student).get(student_id)
    if not s:
        raise HTTPException(404, "not found")
    db.delete(s)
    db.commit()
    return {"status": "deleted"}

# ===============================
# SESSIONS
# ===============================
@app.post("/sessions/start")
def start_session(
    is_exam: bool = Form(False),
    db: SASession = Depends(get_db),
    u = Depends(get_current_user),
):
    if not u.get("is_teacher"):
        raise HTTPException(403, "forbidden")
    sess = DBSession(teacher_id=int(u["sub"]), active=True, is_exam=is_exam)  # use sub
    db.add(sess); db.commit(); db.refresh(sess)
    return {"ok": True, "session_id": sess.id, "is_exam": sess.is_exam}


@app.post("/sessions/stop/{session_id}")
def stop_session(session_id: int, db: SASession = Depends(get_db), u = Depends(get_current_user)):
    if not u.get("is_teacher"):
        raise HTTPException(403, "forbidden")

    sess = db.query(DBSession).get(session_id)
    if not sess or not sess.active:
        raise HTTPException(404, "not active")

    # close session
    sess.active = False
    sess.end_time = datetime.utcnow()

    # students that already have any behavior logged in this session
    seen_ids_q = (
        db.query(Behavior.student_id)
          .filter(Behavior.session_id == session_id)
          .distinct()
    )

    # students never detected during this session
    missing_ids = [sid for (sid,) in db.query(Student.id).filter(~Student.id.in_(seen_ids_q)).all()]

    # one “absent” row per missing student
    if missing_ids:
        db.add_all([
            Behavior(session_id=session_id, student_id=sid, behavior="absent", confidence=0.0)
            for sid in missing_ids
        ])

    db.commit()
    return {"ok": True, "absent_added": len(missing_ids)}


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
        "id": s.id,
        "active": s.active,
        "is_exam": s.is_exam,
        "start_time": s.start_time.isoformat(),
        "end_time": s.end_time.isoformat() if s.end_time else None,
    } for s in sess]

@app.get("/detect/stream")
def detect_stream(session_id: int, db: SASession = Depends(get_db)):
    # verify active session
    sess = db.query(DBSession).get(session_id)
    if not sess or not sess.active:
        raise HTTPException(404, "session not active")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise HTTPException(500, "camera not available")

    last_saved = {}
    SAVE_INTERVAL = 5.0  # seconds
    MIN_SIM = 0.6        # require high confidence
    MIN_MARGIN = 0.05     # best - second-best difference

    def gen_frames():
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            faces = detector.predict(frame)  # [{'bbox': (x,y,w,h), 'landmarks': ...}]
            labels = []
            db2 = SessionLocal()
            try:
                students = db2.query(Student).all()

                for f in faces:
                    crop = preprocess_face(frame, f["bbox"])
                    if crop is None:
                        labels.append("unknown")
                        continue

                    emb = simple_embedding(crop)

                    best_student, best_name = None, "unknown"
                    best_sim, second_sim = -1.0, -1.0

                    for s in students:
                        if not s.embedding:
                            continue
                        txt = s.embedding.strip()
                        if txt.startswith("[") and txt.endswith("]"):
                            txt = txt[1:-1]
                        try:
                            ref = np.array(
                                [float(x) for x in txt.replace("\n", " ").split(",")],
                                dtype=np.float32
                            )
                        except Exception:
                            continue

                        sim = cosine_similarity(emb, ref)
                        if sim > best_sim:
                            second_sim = best_sim
                            best_sim = sim
                            best_student = s
                            best_name = s.full_name
                        elif sim > second_sim:
                            second_sim = sim

                    # apply similarity and margin test
                    if best_student and best_sim >= MIN_SIM and (best_sim - second_sim) >= MIN_MARGIN:
                        labels.append(f"{best_name} ({best_sim:.2f})")

                        landmarks = f.get("landmarks", [])
                        behavior = classify_behavior(frame, f["bbox"], landmarks)

                        if behavior != "attentive":
                            key = (best_student.id, behavior)
                            now = time.time()
                            if key not in last_saved or (now - last_saved[key]) > SAVE_INTERVAL:
                                rec = Behavior(
                                    session_id=session_id,
                                    student_id=best_student.id,
                                    behavior=behavior,
                                    confidence=float(best_sim),
                                    timestamp=datetime.utcnow()
                                )
                                try:
                                    db2.add(rec)
                                    db2.commit()
                                except Exception as e:
                                    db2.rollback()
                                    print("DB error:", e)
                                last_saved[key] = now
                    else:
                        labels.append("unknown")
            finally:
                db2.close()

            annotated = draw_boxes(frame.copy(), faces, labels)
            ret, buf = cv2.imencode(".jpg", annotated)
            if not ret:
                continue
            jpg = buf.tobytes()
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n")

        cap.release()

    return StreamingResponse(gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/images/{filename}")
def serve_image(filename: str):
    path = os.path.join("images", filename)
    if not os.path.exists(path):
        raise HTTPException(404, "not found")
    return FileResponse(path)

@app.get("/me")
def me(u = Depends(get_current_user)):
    return u

# Path to your Framework7 built folder
frontend_dir = Path(__file__).parent.parent / "frontend" / "www"

# Serve all files (index.html, js, css, assets, etc.)
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)