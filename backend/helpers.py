import cv2
import numpy as np

def preprocess_face(img, bbox, size=112):
    x1, y1, x2, y2 = [int(v) for v in bbox]
    x1 = max(0, x1); y1 = max(0, y1)
    face = img[y1:y2, x1:x2]
    if face.size == 0:
        return None
    face = cv2.resize(face, (size, size))
    return face

def simple_embedding(face):
    # Placeholder embedding: normalize and flatten.
    vec = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    return vec.flatten()

def cosine_similarity(a, b):
    a = a.astype(np.float32); b = b.astype(np.float32)
    denom = (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)
    return float(np.dot(a, b) / denom)
