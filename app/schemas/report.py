from pydantic import BaseModel
from typing import List, Optional, Tuple, Any, Dict


class Detection(BaseModel):
    class_name: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]
    centroid: List[float]  # [cx, cy]


class Track(BaseModel):
    track_id: int
    bbox: List[float]
    centroid: List[float]
    class_name: str
    history: List[List[Any]] = []  # list of [timestamp, [cx, cy]]


class StoppedEvent(BaseModel):
    track_id: int
    start_time: float
    end_time: float
    duration: float
    class_name: str = "vehicle"


class InspectionResult(BaseModel):
    plan: List[str]
    summary: str
    events: List[StoppedEvent]
    metadata: Dict[str, Any] = {}
