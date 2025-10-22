import os
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, Text, Float,
    DateTime, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# Users: teachers and parents
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    is_teacher = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    students = relationship("Student", back_populates="parent")
    sessions = relationship("Session", back_populates="teacher")

    def to_dict(self):
            return {
                "id": self.id,
                "name": self.name,
                "email": self.email,
                "is_teacher": self.is_teacher,
                "created_at": self.created_at.isoformat() if self.created_at else None
            }



class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    full_name = Column(String(160), nullable=False)
    class_name = Column(String(64))
    photo_path = Column(String(255))
    embedding = Column(Text)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    parent = relationship("User", back_populates="students")
    behaviors = relationship("Behavior", back_populates="student", cascade="all, delete-orphan")

    def to_dict(self, include_behaviors=False):
        data = {
            "id": self.id,
            "full_name": self.full_name,
            "class_name": self.class_name,
            "photo": "images/" + os.path.basename(self.photo_path) if self.photo_path else None,
            "parent_id": self.parent_id,
            "parent_email": self.parent.email if getattr(self, "parent", None) else None,
        }
        if include_behaviors:
            data["behaviors"] = [
                {
                    "id": b.id,
                    "session_id": b.session_id,
                    "behavior": b.behavior,
                    "confidence": b.confidence,
                    "timestamp": b.timestamp.isoformat() if b.timestamp else None,
                }
                for b in self.behaviors
            ]
        return data


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)

    teacher = relationship("User", back_populates="sessions")
    behaviors = relationship("Behavior", back_populates="session", cascade="all, delete-orphan")


class Behavior(Base):
    __tablename__ = "behaviors"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    behavior = Column(String(32), nullable=False)  # attentive/distracted/sleeping/talking/absent
    confidence = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="behaviors")
    student = relationship("Student", back_populates="behaviors")
