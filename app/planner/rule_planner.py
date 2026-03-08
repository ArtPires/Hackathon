"""Rule-based planner: maps keyword patterns in user prompts to skill chains."""
from app.schemas.plan import InspectionPlan

BASE_CHAIN = [
    "capture_stream",
    "sample_frames",
    "detect_vehicles",
    "track_objects",
    "detect_stopped_vehicles",
    "generate_report",
]

ROI_KEYWORDS = {"stopped", "restricted", "zone", "area", "curb", "curbside", "loading", "parking"}
RENDER_KEYWORDS = {"visual", "overlay", "annotate", "annotated", "draw", "show", "display"}


class RulePlanner:
    """
    Parses a natural-language prompt and builds an InspectionPlan
    by matching keywords to skill chain modifications.
    """

    def plan(self, prompt: str) -> InspectionPlan:
        words = set(prompt.lower().split())

        use_roi = bool(words & ROI_KEYWORDS)
        use_render = bool(words & RENDER_KEYWORDS)

        chain = list(BASE_CHAIN)

        # Insert filter_by_roi before generate_report
        if use_roi:
            chain.insert(chain.index("generate_report"), "filter_by_roi")

        # Insert render_overlay before generate_report
        if use_render:
            chain.insert(chain.index("generate_report"), "render_overlay")

        return InspectionPlan(skill_chain=chain, use_roi=use_roi, use_render=use_render)
