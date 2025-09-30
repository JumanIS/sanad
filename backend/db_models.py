from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    full_name = Column(String(160), nullable=False)
    class_name = Column(String(64), nullable=True)
    photo_path = Column(String(255), nullable=True)
    # simple embedding placeholder (comma-separated floats)
    embedding = Column(Text, nullable=True)

    behaviors = relationship(
            "Behavior",
            back_populates="student",
            cascade="all, delete-orphan"
        )


class Behavior(Base):
    __tablename__ = "behaviors"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    behavior = Column(String(32), nullable=False)  # attentive, distracted, etc.
    confidence = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="behaviors")
