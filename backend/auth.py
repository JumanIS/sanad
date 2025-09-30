import os, time, bcrypt, jwt
from sqlalchemy.orm import Session
from backend.db_models import Teacher

JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_EXP_SECONDS = 60 * 60 * 12

def hash_pw(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def check_pw(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def issue_jwt(teacher_id: int, email: str) -> str:
    now = int(time.time())
    payload = {"sub": teacher_id, "email": email, "iat": now, "exp": now + JWT_EXP_SECONDS}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_jwt(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

def ensure_admin(db: Session):
    # bootstrap a default teacher if none exists
    if not db.query(Teacher).first():
        t = Teacher(name="Admin", email="admin@example.com", password_hash=hash_pw("admin123"))
        db.add(t); db.commit()
