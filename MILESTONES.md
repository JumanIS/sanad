# Milestones & Timeline

## **Week 1 – Setup & Core System (Foundation)**

### Tasks

1. **Environment Setup**
    * Install Raspberry Pi OS (64-bit).
    * Install Python 3.11, pip, and virtualenv.
    * Install PyTorch (CPU build), Flask, OpenCV, SQLite.
    * Connect and test USB Webcam on Raspberry Pi.

2. **Database Setup**
    * Create `teachers`, `students`, `detections` tables in SQLite.
    * Implement SQLAlchemy models in Flask.
    * Verify DB persistence on Raspberry Pi.

3. **Authentication**
    * Implement teacher login with JWT in Flask.
    * Add password hashing (bcrypt).
    * Simple HTML login form (username/password).

4. **Student Registration**
    * Build HTML form for adding student (name, class, photo upload).
    * Backend: extract face embedding from uploaded image.
    * Save embedding + photo in DB.
    * Verify multiple student registration works.

5. **Deployment Setup**
    * Install and configure Nginx on Raspberry Pi.
    * Run Flask via Gunicorn/uWSGI behind Nginx to ensure continuous service.
    * Configure Raspberry Pi with static IP and router access for remote connectivity.

**Deliverables**:
* Functional database.
* Teacher login system.
* Student registration with saved face embeddings.


## **Week 2 – Face Detection & Recognition (Core AI)**

### Tasks

1. **YOLOv5-Face Integration**
    * Clone `https://github.com/deepcam-cn/yolov5-face` into `models/yolov5-face/`.
    * Install requirements from `yolov5-face/requirements.txt`.
    * Use pretrained weights (e.g., `yolov5s-face.pt`) for detection.
    * Connect webcam stream with OpenCV.
    * Run real-time **offline** face detection on Raspberry Pi.

2. **Face Recognition**
    * Extract embeddings for detected faces.
    * Compare with student embeddings in DB (cosine similarity).
    * Assign student ID if similarity > threshold.

3. **Flask API**
    * Endpoint `/detect` → returns JSON `{student_id, name, bbox, confidence}`.
    * Store detections in DB with timestamp.

4. **Frontend**
    * HTML page with `<video>` feed + `<canvas>` overlay.
    * JS draws bounding boxes with student name.
    * Auto-refresh detection results every second.

**Deliverables**:
* Live offline face detection & recognition.
* Bounding boxes with student names on screen.
* Logs saved in DB.


## **Week 3 – Behavior Detection (AI Enhancement)**

### Tasks

1. **Head Pose Estimation**
    * Use 68 facial landmarks or OpenCV solvePnP.
    * Determine if student is looking forward (attentive) or away (distracted).

2. **Eye State Detection**
    * Use pretrained ONNX eye-state model (open/closed).
    * If eyes closed > 5 sec → student marked as “sleeping”.

3. **Object Detection for Distraction**
    * Use YOLOv5-Face (trained to detect faces) + optional secondary YOLO model for “cell phone” and “laptop”.
    * If found near student face → mark as “distracted”.

4. **Behavior Classification Logic**
    * Attentive: face forward + eyes open + no phone.
    * Distracted: face away OR phone detected.
    * Sleeping: eyes closed.
    * Absent: student embedding not detected for > X sec.

5. **Database Logging**
    * Save `{student_id, behavior, timestamp, confidence}`.
    * Append to `detections` table for reporting.

**Deliverables**:
* Behavior detection working in real time.
* Multiple behavior labels displayed on screen.
* Logs stored in DB with behaviors.


## **Week 4 – Reports, Testing & Finalization (Polish)**

### Tasks

1. **Teacher Dashboard**
    * HTML table: student list + % attentive/distracted/sleeping.
    * Graphs (Chart.js) for visualization.
    * Add filtering options:
        * Filter reports by student
        * Filter reports by timestamp (date/time range)
        * Filter reports by behavior type
    * Introduce parent login role (view-only access to reports of their children).

2. **Reports**
    * Export logs to CSV.
    * Generate simple PDF summary per class.

3. **Testing**
    * **Unit tests**: API endpoints (login, register, detect).
    * **Performance tests**: FPS on Raspberry Pi (target ≥ 5 fps with `yolov5s-face.pt`).
    * **Accuracy tests**: confusion matrix (face ID & behavior).
    * **Role-based Access Testing**:
        * Ensure parents cannot access live detection.
        * Validate that parents only see their children’s reports.

4. **Optimization**
    * Try lighter model (`yolov5n-face.pt`) for faster inference.
    * Adjust detection interval (e.g., process every 3rd frame).

5. **Final Documentation**
    * User manual: setup, add students, start detection, view reports.
    * Screenshots of each feature.
    * Project report (problem, objectives, design, results).
    * Presentation slides for demo.

**Deliverables**:
* Full system (login, registration, live detection, behavior logging, reports).
* Tested and optimized prototype on Raspberry Pi.
* Final documentation + presentation.


# Condensed 4-Week Timeline

| Week | Focus                                    | Detailed Outputs                                                       |
| ---- | ---------------------------------------- | ---------------------------------------------------------------------- |
| 1    | Setup + DB + Auth + Student registration | Environment ready, DB schema, login, student photos/embeddings         |
| 2    | Face detection & recognition (YOLOv5-Face) | Offline real-time detection, recognition, bounding boxes, logs         |
| 3    | Behavior detection                       | Attentive / distracted / sleeping / absent classification, logs        |
| 4    | Reporting + testing + docs               | Dashboard, reports, performance tests, optimization, final report/demo |
