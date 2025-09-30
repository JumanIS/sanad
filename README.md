# School Behavior AI

A Flask + YOLOv5-Face based system to detect student behaviors (attentive, distracted, sleeping, talking, absent) in real time from a webcam.

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/deepcam-cn/yolov5-face.git
```

### 2. Create Python environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Linux / macOS:
source venv/bin/activate
# On Windows (PowerShell):
.\venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 4. Verify YOLOv5-Face clone

The directory structure should look like:

```
school-behavior-ai/
├── backend/
├── frontend/
├── yolov5-face/   <-- cloned repo
├── images/
└── db.sqlite3
```

---

## Running the server

From the project root:

```bash
# Run Flask backend
python -m backend.app
```

Open your browser at:
[http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## First user credentials

The backend seeds one admin user in the database:

```
Email: admin@example.com
Password: admin123
```

Use these credentials to log in via the frontend login page.

---

## Behavior detection

Once logged in:

1. Go to the dashboard.
2. Start the webcam stream (`/detect/stream`).
3. The system will classify behaviors in real time and log non-attentive behaviors into the database.