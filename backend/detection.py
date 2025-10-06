import os, sys, cv2, torch
import numpy as np

# yolov5-face repo path and weight file at project root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
Y5_FACE_DIR = os.path.join(ROOT, "yolov5-face")
if Y5_FACE_DIR not in sys.path:
    sys.path.insert(0, Y5_FACE_DIR)

WEIGHTS = os.path.join(ROOT, "yolov5m-face.pt")

from models.experimental import attempt_load
from utils.general import non_max_suppression_face
from backend.behavior import (
    classify_behavior, classify_eye_state_on_roi,
    classify_mouth_state, classify_head_pose
)

class FaceDetector:
    def __init__(self, weights=WEIGHTS, img_size=640, conf_thres=0.25, iou_thres=0.45):
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model = attempt_load(weights, map_location=self.device)  # yolov5-face
        self.model.eval()
        self.img_size = img_size
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres

    def predict(self, bgr):
        im = cv2.resize(bgr, (self.img_size, self.img_size))
        im_rgb = im[:, :, ::-1].transpose(2, 0, 1)
        im_rgb = np.ascontiguousarray(im_rgb)
        im_tensor = torch.from_numpy(im_rgb).to(self.device).float() / 255.0
        if im_tensor.ndimension() == 3:
            im_tensor = im_tensor.unsqueeze(0)

        pred = self.model(im_tensor, augment=False)[0]
        det = non_max_suppression_face(pred, conf_thres=self.conf_thres, iou_thres=self.iou_thres)[0]

        results = []
        if det is not None and len(det):
            det = det.cpu().numpy()
            for d in det:
                x1, y1, x2, y2 = d[0:4]
                conf = d[4]
                # yolov5-face can output landmarks at indices 5..14 (optional per build)
                landmarks = []
                if d.shape[0] >= 15:
                    # x5,y5 pairs
                    landmarks = [
                        (float(d[5]), float(d[6])),
                        (float(d[7]), float(d[8])),
                        (float(d[9]), float(d[10])),
                        (float(d[11]), float(d[12])),
                        (float(d[13]), float(d[14])),
                    ]
                results.append({
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "conf": float(conf),
                    "landmarks": landmarks
                })
        return results

def draw_boxes(img, faces, labels=None):
    for i, f in enumerate(faces):
        x1, y1, x2, y2 = f["bbox"]
        bbox = f["bbox"]
        landmarks = f.get("landmarks", [])

        behavior = classify_behavior(img, bbox, landmarks, has_phone=False, student_key=str(i))
        eye_state, ear = classify_eye_state_on_roi(img, bbox)
        mouth_state, mar = classify_mouth_state(img, bbox)
        head_state, yaw = classify_head_pose(landmarks, img.shape)

        cv2.rectangle(img, (x1, y1), (x2, y2), (0,255,0), 2)

        base_txt = labels[i] if labels and i < len(labels) else f"conf {f['conf']:.2f}"
        beh_txt = f"behavior: {behavior}"
        dbg_txt = f"EAR:{ear:.2f} | MAR:{mar:.2f} | Yaw:{yaw:.1f}"

        cv2.putText(img, base_txt, (x1, max(0, y1-35)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
        cv2.putText(img, beh_txt, (x1, max(0, y1-20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,165,255), 2)
        cv2.putText(img, dbg_txt, (x1, max(0, y1-5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
    return img
