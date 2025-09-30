# Milestones & Timeline

## **Week 1 – Setup & Core System (Foundation)**

### Tasks

1. **Environment Setup**

    * Setup development environment (Windows/Linux/Mac with Python 3.11).
    * Create virtual environment and install dependencies (`backend/requirements.txt`).
    * Clone `deepcam-cn/yolov5-face` into `yolov5-face/`.
    * Move pretrained weights into `models/` (`yolov5m-face.pt`, `yolov5s-face.pt`, etc.).
    * Verify OpenCV can access webcam.

2. **Database Setup**

    * Create `teachers`, `students`, `behaviors` tables in SQLite.
    * Implement SQLAlchemy ORM models (`db_models.py`).
    * Verify DB persistence.

3. **Authentication**

    * JWT login API (`auth.py`).
    * Password hashing with bcrypt.
    * Seed first admin user (`admin@example.com / admin123`).
    * Login form in frontend (`index.html`).

4. **Student Registration**

    * Frontend form to add student (name, class, photo upload).
    * Backend: save UUID photo in `images/`, compute embedding, store in DB.
    * Verify multiple student registration and photo saving.

5. **Deployment Setup**

    * Prepare to run Flask with `python -m backend.app`.
    * For Raspberry Pi: install Nginx + Gunicorn for continuous service.
    * Configure Pi static IP + router access.

**Deliverables**:

* Functional DB schema (`students`, `behaviors`).
* Login system with JWT.
* Student registration with embeddings and photos.

## **Week 2 – Face Detection & Recognition (Core AI)**

### Tasks

1. **YOLOv5-Face Integration**

    * Import `attempt_load` and detection functions from `yolov5-face/`.
    * Load weights from `models/yolov5m-face.pt`.
    * Connect webcam with OpenCV, run live detection.

2. **Face Recognition**

    * Extract embeddings for detected faces.
    * Compare with DB embeddings (cosine similarity).
    * Match student if similarity above threshold.

3. **Flask API**

    * `/detect/stream` → MJPEG stream with annotated frames.
    * Log behaviors into DB only if not "attentive".

4. **Frontend**

    * Navbar with **Students** + **Stream**.
    * Students page: list table, add student form, detail view with behaviors.
    * Stream page: toggle Start/Stop stream button.

**Deliverables**:

* Real-time offline face detection & recognition.
* Student names/confidence shown on screen.
* Logs written into DB.

## **Week 3 – Behavior Detection (AI Enhancement)**

### Tasks

1. **Head Pose Estimation**

    * Use landmarks + OpenCV `solvePnP`.
    * Detect yaw angle (forward vs turned).

2. **Eye State Detection**

    * EAR (eye aspect ratio) from landmarks.
    * If eyes closed > X sec → "sleeping".

3. **Mouth State Detection**

    * MAR (mouth aspect ratio).
    * Detect talking vs silent.

4. **Behavior Classification Logic**

    * Attentive → face forward + eyes open + no phone.
    * Distracted → turned away or phone/laptop detected.
    * Sleeping → eyes closed > threshold.
    * Absent → no face detected for X sec.

5. **Database Logging**

    * Save `{student_id, behavior, confidence, timestamp}` into `behaviors`.
    * Apply `SAVE_INTERVAL` (e.g. 30s) to prevent duplicates.

**Deliverables**:

* Behavior classification working in stream.
* Logs stored in `behaviors` table with timestamps.
* Display on frontend behavior table per student.


## **Week 4 – Reports, Testing & Finalization (Polish)**

### Tasks

1. **Teacher Dashboard**

    * Students page shows photo + behavior history.
    * Behaviors displayed in styled table.
    * Add **Back to List** / navigation consistency.

2. **Reports**

    * Export behavior logs to CSV.
    * Option for PDF summary per student/class.

3. **Testing**

    * Unit tests for APIs (login, register, detect).
    * Performance tests: FPS with `yolov5m-face.pt` and `yolov5s-face.pt`.
    * Accuracy tests for recognition + behavior thresholds.
    * Role-based testing (teacher vs parent view-only).

4. **Optimization**

    * Test lighter models (`yolov5n-face.pt`) for speed.
    * Adjust detection interval (every N frames).
    * Tune SAVE_INTERVAL for balanced logging.

5. **Final Documentation**

    * User manual: how to add students, start stream, view logs.
    * Screenshots of UI (login, students, stream).
    * Final project report + presentation slides.

**Deliverables**:

* Fully working system with login, student mgmt, streaming, behavior logging.
* Reports + exports.
* Documented + demo-ready prototype.

# Condensed 4-Week Timeline

| Week | Focus                              | Outputs                                                       |
| ---- | ---------------------------------- | ------------------------------------------------------------- |
| 1    | Setup + DB + Auth + Students       | Environment, DB schema, login, add students/photos/embeddings |
| 2    | Face detection & recognition       | YOLOv5-Face integration, stream, recognition, logging         |
| 3    | Behavior detection                 | Attentive / distracted / sleeping / absent classification     |
| 4    | Dashboard + reports + tests + docs | Student tables, behavior history, CSV/PDF reports, demo-ready |
