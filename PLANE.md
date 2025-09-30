# Project Plan

## 1. Overview

An **offline Raspberry Pi + Webcam system** for teachers to register students, capture face data, and monitor classroom behavior in real time.

* **Backend**: Flask (Python)
* **Frontend**: HTML/CSS/JS
* **Face detection**: YOLOv5-Face (cloned repo)
* **Database**: SQLite (via SQLAlchemy ORM)

Teachers see bounding boxes around students with names + behavior states. Logs are saved to DB for reports.


## 2. Users & Roles

* **Teacher**

    * Login/logout
    * Register students (profile + photo)
    * Start/stop live monitoring
    * View real-time detections
    * View student behavior history & reports

* **Student**

    * Stored in DB (id, name, class, embedding, photo path)
    * Identified automatically during detection

* **Parent**

    * Login/logout
    * View reports of their children only
    * Cannot access live detection


## 3. Hardware

* Raspberry Pi 4 (4–8 GB RAM)
* USB Webcam (1080p or better)
* Local Wi-Fi network
* Storage: microSD / SSD


## 4. Software

* **Backend**: Flask + SQLAlchemy + JWT + bcrypt

* **Frontend**: HTML + CSS + JS (simple UI with navbar, student pages, stream)

* **Database**: SQLite (file: `db.sqlite3`)

* **Models**:

    * YOLOv5-Face (face detection, cloned repo: `yolov5-face/`)
    * Face recognition embeddings (stored in DB)
    * Head pose estimation (yaw detection)
    * Eye state detection (EAR → sleeping detection)
    * Mouth state detection (MAR → talking detection)

* **Deployment**:

    * Flask served with Gunicorn/uWSGI behind Nginx
    * Nginx reverse proxy for continuous service
    * Raspberry Pi configured with static IP + router access


## 5. Database Design (SQLite)

**Teachers**

* id, name, email, password_hash

**Students**

* id, full_name, class_name, photo_path, embedding

**Behaviors**

* id, student_id (FK → Students.id)
* behavior (attentive, distracted, sleeping, talking, absent)
* confidence
* timestamp


## 6. Features & Flow

### Registration

* Teacher logs in
* Adds student with name + class + photo
* Photo saved in `/images/` with UUID filename
* Face embedding extracted + stored in DB

### Live Detection

* Teacher starts stream
* Webcam feed processed by YOLOv5-Face
* Embedding matched against DB → student identified
* Behavior classified:

    * Attentive
    * Distracted
    * Sleeping
    * Talking
    * Absent
* Bounding box + labels drawn on video
* Behavior logged to DB (with **SAVE_INTERVAL** to avoid spam)

### Reports

* Teacher views per-student behavior history in table
* Behaviors table styled in frontend
* Export to CSV or PDF
* Parents can view their children’s reports only
* Filters:

    * By student
    * By date/time range
    * By behavior type


## 7. Testing

* Unit tests for Flask endpoints (login, register, students CRUD, stream)
* Black-box testing of login/stream flow
* Performance: FPS on Raspberry Pi (goal: 5+ FPS with `yolov5s-face.pt`)
* Accuracy: % correct student recognition + behavior classification


## 8. Deliverables

* Running Raspberry Pi system with Flask backend
* Web frontend with:

    * Login
    * Students list + add/view/delete
    * Behavior history tables
    * Stream with toggle Start/Stop
* SQLite DB with students + behaviors
* Documentation (setup, usage, screenshots, results)


## 9. Future Improvements

* Optimize YOLOv5-Face with TensorRT / YOLOv8 Nano
* Add emotion + voice analysis
* Cloud dashboard for multi-class reporting
* Federated learning for privacy-preserving model updates
* Multi-role system: admins, teachers, parents
* HTTPS with Nginx + Certbot SSL


# File Structure

```
school-behavior-ai/
├── backend/                          # Flask backend
│   ├── __init__.py                   # Python package marker
│   ├── app.py                        # Main app: routes, streaming
│   ├── auth.py                       # Auth + JWT
│   ├── behavior.py                   # Behavior classification logic
│   ├── db_models.py                  # ORM models: Teacher, Student, Behavior
│   ├── detection.py                  # YOLOv5-Face integration
│   ├── helpers.py                    # Embeddings, preprocessing, similarity
│   └── requirements.txt              # Dependencies
│
├── frontend/                         # Web UI
│   ├── index.html                    # Login + Students + Stream
│   ├── style.css                     # Navbar, tables, forms, stream
│   └── app.js                        # API calls, CRUD, stream handling
│
├── yolov5-face/                      # Cloned YOLOv5-Face repo (code only)
│
├── models/                           # Pretrained YOLOv5-Face weights
│   ├── yolov5m-face.pt               # Medium model (default)
│   ├── yolov5n-0.5.pt                # Nano model (fast)
│   └── yolov5s-face.pt               # Small model
│
├── images/                           # Student photos (UUID filenames)
│
├── db.sqlite3                        # SQLite database (auto-generated)
│
├── README.md                         # Setup + usage guide
├── PLANE.md                          # Project plan
└── MILESTONES.md                     # Timeline of implementation steps
```