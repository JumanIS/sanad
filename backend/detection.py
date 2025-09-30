import os, sys, time, cv2, torch
import numpy as np

YOLO_FACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "yolov5-face"))
if YOLO_FACE_DIR not in sys.path:
    sys.path.insert(0, YOLO_FACE_DIR)

from models.experimental import attempt_load
from utils.general import non_max_suppression, non_max_suppression_face
from backend.behavior import classify_behavior, classify_eye_state_on_roi, classify_mouth_state, classify_head_pose

class FaceDetector:
    def __init__(self, weights_rel=None, img_size=640, conf_thres=0.25, iou_thres=0.45):
        if weights_rel is None:
            weights = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "models", "yolov5m-face.pt")
            )

        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        # older yolov5-face API
        self.model = attempt_load(weights, map_location=self.device)
        self.model.eval()
        self.img_size = img_size
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres

    def predict(self, bgr):
        im = cv2.resize(bgr, (self.img_size, self.img_size))
        im_rgb = im[:, :, ::-1].transpose(2, 0, 1)
        im_rgb = np.ascontiguousarray(im_rgb)
        im_tensor = torch.from_numpy(im_rgb).to(self.device).float()
        im_tensor /= 255.0
        if im_tensor.ndimension() == 3:
            im_tensor = im_tensor.unsqueeze(0)

        pred = self.model(im_tensor, augment=False)[0]
        # YOLOv5-face uses special NMS
        det = non_max_suppression_face(pred, conf_thres=self.conf_thres, iou_thres=self.iou_thres)[0]

        results = []
        if det is not None and len(det):
            det = det.cpu().numpy()
            for d in det:
                x1, y1, x2, y2 = d[0:4]
                conf = d[4]
                # you can also grab landmarks if needed: d[6:16]
                results.append({
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "conf": float(conf)
                })
        return results

def draw_boxes(img, faces, labels=None):
    """
    img: full frame (BGR)
    faces: list of dicts from YOLOv5-Face [{"bbox":[x1,y1,x2,y2],"conf":..,"landmarks":[...]}]
    labels: optional list of names (same length as faces)
    """
    for i, f in enumerate(faces):
        x1, y1, x2, y2 = f["bbox"]
        bbox = f["bbox"]
        landmarks = f.get("landmarks", [])

        # --- classify behavior ---
        behavior = classify_behavior(img, bbox, landmarks,
                                     has_phone=False,  # TODO: hook in phone detector
                                     student_id=str(i))

        # --- individual metrics for debug ---
        eye_state, ear = classify_eye_state_on_roi(img, bbox)
        mouth_state, mar = classify_mouth_state(img, bbox)
        head_state, yaw = classify_head_pose(landmarks, img.shape)

        # --- draw bounding box ---
        cv2.rectangle(img, (x1, y1), (x2, y2), (0,255,0), 2)

        # --- labels ---
        base_txt = labels[i] if labels and i < len(labels) else f"conf {f['conf']:.2f}"
        beh_txt = f"behavior: {behavior}"
        dbg_txt = f"EAR:{ear:.2f} | MAR:{mar:.2f} | Yaw:{yaw:.1f}"

        # First line: name/conf
        cv2.putText(img, base_txt, (x1, max(0, y1-35)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
        # Second line: behavior
        cv2.putText(img, beh_txt, (x1, max(0, y1-20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,165,255), 2)
        # Third line: debug metrics
        cv2.putText(img, dbg_txt, (x1, max(0, y1-5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)

    return img
