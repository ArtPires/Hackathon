"""Skill: detect_vehicles — Detect cars, motorcycles, buses, and trucks using YOLOv8."""
from typing import List, Dict, Any
import numpy as np

from app.config import settings
from app.schemas.report import Detection


# COCO class names for vehicle classes
VEHICLE_CLASS_NAMES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


class VehicleDetector:
    """Loads a YOLOv8 model and detects vehicles in frames."""

    def __init__(self, model_path: str = None, confidence: float = None):
        self.model_path = model_path or settings.YOLO_MODEL
        self.confidence = confidence or settings.CONFIDENCE_THRESHOLD
        self.vehicle_classes = settings.VEHICLE_CLASSES
        self._model = None

    def _load_model(self):
        if self._model is None:
            from ultralytics import YOLO
            self._model = YOLO(self.model_path)

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Run vehicle detection on a single frame.

        Returns a list of Detection objects with class_name, confidence, bbox, centroid.
        """
        self._load_model()
        results = self._model(frame, conf=self.confidence, verbose=False)
        detections = []

        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                if cls_id not in self.vehicle_classes:
                    continue
                conf = float(box.conf[0])
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                detections.append(Detection(
                    class_name=VEHICLE_CLASS_NAMES.get(cls_id, "vehicle"),
                    confidence=conf,
                    bbox=[x1, y1, x2, y2],
                    centroid=[cx, cy],
                ))

        return detections
