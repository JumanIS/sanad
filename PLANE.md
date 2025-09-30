# Project Plan

## 1. Overview

A Raspberry Pi + Webcam system for teachers to register students, capture face data, and monitor classroom behavior in real time. Flask provides the backend, HTML/CSS/JS handles the frontend, YOLOv5-Face detects faces, and SQLite stores information. Teachers see bounding boxes around students with names and behavior states. Everything runs **offline**.

## 2. Users & Roles

* **Teacher**
    * Login / logout
    * Register students with profile + photo
    * Start/stop live monitoring
    * View real-time detections
    * View behavior history and reports

* **Student**
    * Stored in database only (id, name, class, face embedding, picture)
    * Identified automatically during detection

* **Parent**
    * Login / logout
    * View related student(s) reports only
    * Cannot access live detection

## 3. Hardware

* Raspberry Pi 4 (4–8 GB RAM)
* USB Webcam (1080p or better)
* Local Wi-Fi network
* Storage: microSD / SSD

## 4. Software

* **Backend**: Flask (Python API)
* **Frontend**: HTML + CSS + JS (simple UI)
* **Database**: SQLite
* **Models**:
    * **YOLOv5-Face** (offline cloned repo for face detection: `yolov5-face`)
    * Face recognition (InsightFace/Facenet embeddings)
    * Head pose estimation (attention check)
    * Eye state detection (sleep detection)

* **Deployment**:
    * Nginx configured as a reverse proxy to keep Flask running continuously.
    * Flask served using Gunicorn/uWSGI behind Nginx.
    * Raspberry Pi configured with static IP and router setup for network access.

## 5. Database Design (SQLite)

**Teachers**
- id, name, email, password_hash

**Students**
- id, full_name, class, photo, embedding

**Detections**
- id, student_id, teacher_id, timestamp, behavior, confidence

## 6. Features & Flow

### Registration
* Teacher logs in → adds students → uploads face image → embedding stored.

### Live Detection
* Teacher starts session.
* Webcam feed → YOLOv5-Face detects faces offline.
* Face embedding compared to DB → student identified.
* Behavior classified (attentive, distracted, sleeping, absent).
* Bounding box + label shown in frontend.
* Detection saved in DB.

### Reports
* Teacher views history per student/class.
* Export option (CSV/PDF).
* Parents can log in and view reports related only to their registered children.
* Teachers and parents can filter reports by:
    * Student
    * Timestamp (date/time range)
    * Behavior type (attentive, distracted, sleeping, absent)
* Reports can be exported in multiple formats:
    * Excel (XLSX)
    * PDF

## 7. Testing

* Unit testing for Flask endpoints.
* Black-box testing of login, registration, detection.
* Performance: FPS on Raspberry Pi.
* Accuracy: % correct detections and behaviors.

## 8. Deliverables

* Working Raspberry Pi system with Flask server.
* Simple web UI for teachers.
* SQLite DB with students and logs.
* Offline YOLOv5-Face detection integrated in `detection.py`.
* Final project report (with results, screenshots, diagrams).

## 9. Future Improvements

* Optimize YOLOv5-Face with TensorRT / YOLOv8 Nano.
* Add emotion & voice analysis.
* Cloud-based dashboard for multiple classes.
* Federated learning for privacy-preserving improvements.
* Multi-role management for administrators, teachers, and parents.
* Secure remote access using HTTPS with Nginx and Certbot SSL certificates.

# Files Structure

```
school-behavior-ai/
├── backend/                          # Backend (Flask API + AI integration)
│   ├── __init__.py                   # Marks this folder as a Python package
│   ├── app.py                        # Flask main app (routes, APIs, student mgmt, streaming)
│   ├── auth.py                       # Authentication & JWT handling
│   ├── behavior.py                   # Behavior classification (attentive, distracted, etc.)
│   ├── db_models.py                  # SQLite ORM models (SQLAlchemy: Student, Behavior, User)
│   ├── detection.py                  # YOLOv5-Face + recognition + behavior logic
│   ├── helpers.py                    # Utility functions (embedding, similarity, preprocessing)
│   └── requirements.txt              # Python dependencies for backend
│
├── frontend/                         # Simple frontend (HTML/CSS/JS)
│   ├── index.html                    # Login, dashboard, students list, stream page
│   ├── style.css                     # Frontend styling (navbar, tables, forms, stream view)
│   └── app.js                        # Frontend logic: login, API calls, students CRUD, streaming
│
├── yolov5-face/                      # Cloned repo from deepcam-cn/yolov5-face (model code)
│
├── models/                           # Pretrained weights (.pt) for YOLOv5-Face
│   ├── yolov5m-face.pt               # Medium model, main one used
│   ├── yolov5n-0.5.pt                # Nano model (lighter, less accurate)
│   └── yolov5s-face.pt               # Small model alternative
│
├── images/                           # Uploaded student photos (UUID filenames)
│
├── db.sqlite3                        # SQLite database (auto-generated)
│
├── README.md                         # Setup and usage guide
├── PLANE.md                          # Full project plan (design + goals)
└── MILESTONES.md                     # Timeline of implementation steps
```