import cv2
import numpy as np
import time
import mediapipe as mp

# ========================
# Thresholds / constants
# ========================
EAR_THRESHOLD = 0.25        # below = closed
SLEEP_SECONDS = 5.0         # if closed > this → sleeping
YAW_THRESHOLD = 25.0        # degrees away → distracted
MAR_THRESHOLD = 0.6         # mouth aspect ratio → talking
ABSENT_SECONDS = 3.0        # no face detected → absent

# Track timing of eyes for sleep detection
_last_eye_open_time = {}
# Track last seen time per student
_last_seen_time = {}

# MediaPipe FaceMesh (for EAR, MAR)
_mp = mp.solutions.face_mesh
_face_mesh = _mp.FaceMesh(static_image_mode=False,
                          refine_landmarks=True,
                          max_num_faces=1,
                          min_detection_confidence=0.5,
                          min_tracking_confidence=0.5)

# Eye landmarks (6 points each)
LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]
# Mouth landmarks
MOUTH_IDX = [61, 81, 311, 291, 13, 14]  # upper/lower + corners


# ========================
# Helpers
# ========================
def _eye_aspect_ratio(pts):
    A = np.linalg.norm(pts[1] - pts[5])
    B = np.linalg.norm(pts[2] - pts[4])
    C = np.linalg.norm(pts[0] - pts[3])
    return (A + B) / (2.0 * C + 1e-6)


def _mouth_aspect_ratio(pts):
    # pts: [left_corner, right_corner, upper, lower]
    A = np.linalg.norm(pts[2] - pts[3])  # vertical
    C = np.linalg.norm(pts[0] - pts[1])  # horizontal
    return A / (C + 1e-6)


def _face_key_from_bbox(bbox):
    x1, y1, x2, y2 = bbox
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    return f"{cx//20}-{cy//20}"


# ========================
# Eye state (EAR)
# ========================
def classify_eye_state_on_roi(frame_bgr, bbox):
    h, w = frame_bgr.shape[:2]
    x1, y1, x2, y2 = bbox
    x1 = max(0, x1); y1 = max(0, y1)
    x2 = min(w - 1, x2); y2 = min(h - 1, y2)

    if x2 <= x1 or y2 <= y1:
        return "open", 1.0

    roi = frame_bgr[y1:y2, x1:x2]
    if roi.size == 0:
        return "open", 1.0

    rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
    res = _face_mesh.process(rgb)
    if not res.multi_face_landmarks:
        return "open", 1.0

    lm = res.multi_face_landmarks[0].landmark
    rh, rw = roi.shape[:2]

    def gather(idx_list):
        return np.array([[lm[i].x * rw, lm[i].y * rh] for i in idx_list], dtype=np.float32)

    left_pts = gather(LEFT_EYE_IDX)
    right_pts = gather(RIGHT_EYE_IDX)
    ear = (_eye_aspect_ratio(left_pts) + _eye_aspect_ratio(right_pts)) / 2.0

    key = _face_key_from_bbox(bbox)
    now = time.time()

    if ear < EAR_THRESHOLD:
        if key not in _last_eye_open_time:
            _last_eye_open_time[key] = now
        elapsed = now - _last_eye_open_time[key]
        return ("sleeping" if elapsed >= SLEEP_SECONDS else "closed", ear)
    else:
        _last_eye_open_time[key] = now
        return "open", ear


# ========================
# Head pose (yaw)
# ========================
MODEL_POINTS = np.array([
    (0.0, 0.0, 0.0),        # Nose tip
    (-30.0, -125.0, -30.0), # Left eye
    (30.0, -125.0, -30.0),  # Right eye
    (-60.0, -70.0, -60.0),  # Left mouth
    (60.0, -70.0, -60.0)    # Right mouth
], dtype=np.float32)

def classify_head_pose(landmarks, frame_shape):
    h, w = frame_shape[:2]
    if len(landmarks) < 5:
        return "forward", 0.0

    image_points = np.array([
        landmarks[2],  # Nose
        landmarks[0],  # Left eye
        landmarks[1],  # Right eye
        landmarks[3],  # Left mouth
        landmarks[4],  # Right mouth
    ], dtype=np.float32)

    focal_length = w
    center = (w/2, h/2)
    camera_matrix = np.array([[focal_length,0,center[0]],
                              [0,focal_length,center[1]],
                              [0,0,1]], dtype="double")
    dist_coeffs = np.zeros((4,1))

    success, rvec, tvec = cv2.solvePnP(MODEL_POINTS, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE)
    if not success:
        return "forward", 0.0

    rmat, _ = cv2.Rodrigues(rvec)
    proj = np.hstack((rmat, tvec))
    _, _, _, _, _, _, euler = cv2.decomposeProjectionMatrix(proj)
    yaw = float(euler[1])

    return ("away" if abs(yaw) > YAW_THRESHOLD else "forward", yaw)


# ========================
# Mouth state (MAR)
# ========================
def classify_mouth_state(frame_bgr, bbox):
    h, w = frame_bgr.shape[:2]
    x1,y1,x2,y2 = bbox
    roi = frame_bgr[y1:y2, x1:x2]
    if roi.size == 0:
        return "closed", 0.0

    rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
    res = _face_mesh.process(rgb)
    if not res.multi_face_landmarks:
        return "closed", 0.0

    lm = res.multi_face_landmarks[0].landmark
    rh,rw = roi.shape[:2]
    pts = np.array([[lm[i].x * rw, lm[i].y * rh] for i in MOUTH_IDX], dtype=np.float32)
    # reorder to [left_corner, right_corner, upper, lower]
    mar = _mouth_aspect_ratio([pts[0], pts[3], pts[4], pts[5]])
    return ("talking" if mar > MAR_THRESHOLD else "closed", mar)


# ========================
# Behavior classification
# ========================
def classify_behavior(frame, bbox, landmarks, has_phone=False, student_id="unknown"):
    """
    frame: full frame BGR
    bbox: [x1,y1,x2,y2]
    landmarks: [left_eye, right_eye, nose, left_mouth, right_mouth]
    has_phone: bool, if phone/laptop detected
    student_id: optional, to track last_seen
    """
    now = time.time()
    if student_id:
        _last_seen_time[student_id] = now

    # check absence
    if student_id in _last_seen_time:
        if now - _last_seen_time[student_id] > ABSENT_SECONDS:
            return "absent"

    # eye state
    eye_state, ear = classify_eye_state_on_roi(frame, bbox)
    if eye_state == "sleeping" or eye_state == "closed":
        return "sleeping"

    # mouth state
    mouth_state, mar = classify_mouth_state(frame, bbox)
    if mouth_state == "talking":
        return "talking"

    # head pose
    head_state, yaw = classify_head_pose(landmarks, frame.shape)
    if head_state == "away" or has_phone:
        return "distracted"

    # default
    return "attentive"
