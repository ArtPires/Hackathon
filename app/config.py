from dataclasses import dataclass, field
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    SAMPLE_FPS: float = 3.0
    MOTION_THRESHOLD: int = 10
    MIN_STOP_DURATION: float = 5.0
    YOLO_MODEL: str = "yolov8n.pt"
    CONFIDENCE_THRESHOLD: float = 0.4
    # COCO class IDs: 2=car, 3=motorcycle, 5=bus, 7=truck
    VEHICLE_CLASSES: List[int] = field(default_factory=lambda: [2, 3, 5, 7])
    MAX_TRACK_DISTANCE: int = 150
    MAX_LOST_FRAMES: int = 30
    DEFAULT_ROI: Optional[List] = None
    ANTHROPIC_API_KEY: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))


settings = Settings()
