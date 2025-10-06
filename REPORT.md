System overview:

An on-premise **AI classroom monitoring system** built with **FastAPI + Framework7**, running on a **Raspberry Pi + webcam**. It identifies students, tracks behaviors, and separates teacher and parent roles.

---

### **1. Purpose**

Automate classroom observation.
Teachers register students and monitor their behavior (attentive, distracted, sleeping, talking, absent) in real time.
Each monitoring run is a “session.” Parents log in later to review reports only.

---

### **2. Users and Roles**

| Role        | Capabilities                                                                                                                                                                                          |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Teacher** | • Register/login.<br>• Create other teachers and parents.<br>• Add/edit/delete students.<br>• Assign each student to a parent.<br>• Start and stop monitoring sessions.<br>• View and export reports. |
| **Parent**  | • Login only.<br>• View list of their children and their behavior reports.<br>• Cannot start sessions, modify students, or edit data.                                                                 |

Teachers control user creation and student-parent links. Parents are passive viewers.

---

### **3. Components**

* **Hardware:** Raspberry Pi 4 (4–8 GB RAM), USB webcam, local storage.
* **Software:**

    * **Backend:** FastAPI (Python 3.11)
    * **Frontend:** Framework7 + HTML/CSS/JS
    * **Database:** SQLite via SQLAlchemy
    * **AI:** YOLOv5-Face + Mediapipe for face, eyes, mouth, and head-pose.

---

### **4. Database Schema**

#### **users**

| Field           | Type     | Notes                          |
| --------------- | -------- | ------------------------------ |
| `id`            | int      | Primary key                    |
| `name`          | str      | Full name                      |
| `email`         | str      | Unique                         |
| `password_hash` | str      | bcrypt                         |
| `is_teacher`    | bool     | True → teacher, False → parent |
| `created_at`    | datetime | Auto timestamp                 |

Relationships:

* Teacher → sessions (one-to-many)
* Parent → students (one-to-many)

---

#### **students**

| Field        | Type          | Notes           |
| ------------ | ------------- | --------------- |
| `id`         | int           | PK              |
| `full_name`  | str           |                 |
| `class_name` | str           |                 |
| `photo_path` | str           | Stored image    |
| `embedding`  | text          | Face vector     |
| `parent_id`  | FK → users.id | Optional parent |

Relationships:

* Behaviors (one-to-many)

---

#### **sessions**

| Field        | Type          | Notes              |
| ------------ | ------------- | ------------------ |
| `id`         | int           | PK                 |
| `teacher_id` | FK → users.id | Creator            |
| `start_time` | datetime      |                    |
| `end_time`   | datetime      | nullable           |
| `active`     | bool          | True while running |

Each press of “Start Stream” creates a new session.
On stop, `end_time` is filled and `active=False`.

---

#### **behaviors**

| Field        | Type             | Notes                                                |
| ------------ | ---------------- | ---------------------------------------------------- |
| `id`         | int              | PK                                                   |
| `session_id` | FK → sessions.id |                                                      |
| `student_id` | FK → students.id |                                                      |
| `behavior`   | str              | attentive / distracted / sleeping / talking / absent |
| `confidence` | float            | similarity or certainty                              |
| `timestamp`  | datetime         | logged moment                                        |

Rules:

* **Attentive** and **Absent** recorded **once per session per student**.
* Other behaviors (sleeping, talking, distracted) can repeat as they occur.

---

### **5. Behavior Logic**

* **Attentive:** Face forward, eyes open, mouth closed, no phone detected.
* **Distracted:** Head turned > 25° or phone/laptop near face.
* **Sleeping:** Eyes closed > 5 s.
* **Talking:** Mouth open ratio > threshold (MAR > 0.6).
* **Absent:** Face not detected for > 3 s.

Each detection frame checks these states; entries written following above rules.

---

### **6. Workflow**

#### **Teacher Setup**

1. Teacher logs in (JWT-based).
2. Can create additional teachers or parents via a simple form.
3. Adds students with photo and class, assigns existing or new parent.

#### **Session Operation**

1. Click **Start Stream** → new `session` record.
2. Webcam opens; YOLOv5 detects faces.
3. For each recognized student:

    * Compute cosine similarity with stored embedding.
    * Determine behavior using Mediapipe landmarks.
    * Write or update behavior rows in DB.
4. Video stream shows bounding boxes and labels in browser.
5. Click **Stop Stream** → finalize session.

#### **Reports**

* Teachers view all sessions, students, and statistics.
* Filters: student, class, behavior, date/time.
* Export CSV/PDF.
* Parents log in to see only their linked students and cannot alter data.

---

### **7. Frontend (Framework7)**

* Responsive single-page app.
* Tabs: **Users**, **Students**, **Stream**, **Reports**.
* Teachers see management buttons; parents see read-only lists.
* Stream tab embeds `<img>` with MJPEG from `/detect/stream`.
* Reports tab summarizes behaviors with color-coded badges.

---

### **8. Deployment**

* Run FastAPI via **Uvicorn** under **Nginx** reverse proxy.
* SQLite stored locally.
* Static IP allows LAN access for classroom tablets or PCs.
* System service auto-starts on boot.

---

### **9. Output**

* Real-time labeled video stream.
* Persistent session and behavior history.
* Exportable attendance/attention reports.
* Secure, offline-ready monitoring solution.

---

### **10. Summary**

A compact, privacy-controlled AI classroom tool.
Teachers manage users, students, and sessions; parents only observe.
Behaviors—**attentive, distracted, sleeping, talking, absent**—are detected automatically, logged once or as events per session, and summarized for review and reporting.

### **11. Files Structure

```
school-behavior-ai/
├── backend/
│   ├── main.py               # FastAPI main app (routes, sessions, detection)
│   ├── auth.py               # Authentication & JWT helpers (teachers only)
│   ├── db_models.py          # SQLAlchemy ORM models (users, students, sessions, behaviors)
│   ├── detection.py          # YOLOv5-Face detection + drawing utilities
│   ├── behavior.py           # EAR, MAR, yaw, and full behavior classification logic
│   ├── helpers.py            # Image preprocessing, embeddings, cosine similarity
│   ├── requirements.txt      # Python dependencies
│   ├── db.sqlite3            # SQLite database (auto-created)
│   └── __init__.py
│
├── frontend/
│   ├── index.html                # main Framework7 entry
│   ├── css/
│   │   └── style.css             # custom styles
│   ├── js/
│   │   ├── app.js                # Framework7 initialization
│   │   ├── api.js                # all API calls
│   │   ├── auth.js               # login/logout/token logic
│   │   ├── students.js           # student CRUD
│   │   ├── sessions.js           # session start/stop + stream
│   │   └── reports.js            # reports & filters
│   ├── pages/
│   │   ├── login.html
│   │   ├── students.html
│   │   ├── users.html
│   │   ├── stream.html
│   │   └── reports.html
│   ├── assets/
│   │    ├── avatar.png
│   │    └── icons/
│   └── libs/
│       └── framework7/
│           ├── framework7-bundle.min.css
│           └── framework7-bundle.min.js
│
├── yolov5-face/              # Cloned YOLOv5-Face repo (https://github.com/deepcam-cn/yolov5-face)
├── yolov5m-face.pt           # Trained YOLOv5-Face model
│
├── images/                   # Uploaded student photos
│   └── .gitignore            # Just to keep folder empty incase using git
│
├── PLANE.md                  # Project plan and overview
├── MILESTONES.md             # 4-week milestone plan
├── README.md                 # Installation, usage, and deployment guide
│
└── run.sh                    # Bash script to start FastAPI (uvicorn backend.main:app --host 0.0.0.0 --port 8000)
```
