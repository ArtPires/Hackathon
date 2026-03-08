from pydantic import BaseModel
from typing import List


ALLOWED_SKILLS = [
    "capture_stream",
    "sample_frames",
    "detect_vehicles",
    "track_objects",
    "detect_stopped_vehicles",
    "filter_by_roi",
    "render_overlay",
    "generate_report",
]


class InspectionPlan(BaseModel):
    skill_chain: List[str]
    use_roi: bool = False
    use_render: bool = False
