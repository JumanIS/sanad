import os, time, bcrypt, jwt
from sqlalchemy.orm import Session
from backend.db_models import User

JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_EXP_SECONDS = 60 * 60 * 12  # 12 hours


def hash_pw(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def check_pw(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def issue_jwt(user_id: int, email: str, is_teacher: bool) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
        "is_teacher": is_teacher,
        "iat": now,
        "exp": now + JWT_EXP_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_jwt(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])


def ensure_bootstrap_teacher(db: Session):
    """Create default teacher if no teachers exist."""
    if not db.query(User).filter(User.is_teacher == True).first():
        t = User(
            name="Admin",
            email="admin@example.com",
            password_hash=hash_pw("admin123"),
            is_teacher=True,
        )
        db.add(t)
        db.commit()


def create_user(db: Session, name: str, email: str, password: str, is_teacher: bool):
    if db.query(User).filter(User.email == email).first():
        return {"error": "email exists"}
    u = User(name=name, email=email, password_hash=hash_pw(password), is_teacher=is_teacher)
    db.add(u)
    db.commit()
    return {"ok": True, "id": u.id}


def login(db: Session, email: str, password: str):
    ensure_bootstrap_teacher(db)
    u = db.query(User).filter(User.email == email).first()
    if not u or not check_pw(password, u.password_hash):
        return {"error": "invalid credentials"}
    token = issue_jwt(u.id, u.email, u.is_teacher)
    return {"token": token, "user": u.to_dict()}
