"""Skill: generate_report — Convert stopped events into a human-readable report."""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Tuple

from app.schemas.report import StoppedEvent


class ReportGenerator:
    """Generates text and JSON reports from stopped vehicle events."""

    def generate(
        self,
        stopped_events: List[StoppedEvent],
        metadata: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a summary string and structured JSON dict.

        Returns: (summary_text, json_dict)
        """
        count = len(stopped_events)
        source = metadata.get("source", "unknown")
        sample_fps = metadata.get("sample_fps", 3.0)
        roi_enabled = metadata.get("use_roi", False)
        min_stop = metadata.get("min_stop_duration", 5.0)

        if count == 0:
            summary = "No stopped vehicles detected in the analyzed footage."
        elif count == 1:
            evt = stopped_events[0]
            summary = (
                f"1 {evt.class_name} remained stopped "
                f"for {evt.duration:.1f} seconds "
                f"(from {evt.start_time:.1f}s to {evt.end_time:.1f}s)."
            )
            if roi_enabled:
                summary += " (inside restricted area)"
        else:
            avg_duration = sum(e.duration for e in stopped_events) / count
            area_note = " in the restricted area" if roi_enabled else ""
            summary = (
                f"{count} vehicles remained stopped{area_note} "
                f"for more than {min_stop:.0f} seconds "
                f"(avg. {avg_duration:.1f}s each)."
            )

        events_json = [e.model_dump() for e in stopped_events]

        result = {
            "summary": summary,
            "events": events_json,
            "metadata": {
                "source": str(source),
                "roi_enabled": roi_enabled,
                "sample_fps": sample_fps,
                "timestamp": datetime.now().isoformat(),
                "total_stopped": count,
            },
        }
        return summary, result

    def save_json(self, report: Dict[str, Any], output_dir: str = "outputs/reports") -> str:
        """Save the JSON report to disk and return the file path."""
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(output_dir, f"report_{ts}.json")
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
        return path
