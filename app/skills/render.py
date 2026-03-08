"""Skill: render_overlay — Draw bounding boxes, track IDs, ROI, and labels on frames."""
from typing import Dict, List, Optional
import numpy as np
import cv2

from app.schemas.report import Track, StoppedEvent


# Colours (BGR)
COLOR_MOVING = (0, 255, 0)      # green
COLOR_STOPPED = (0, 0, 255)     # red
COLOR_ROI = (255, 165, 0)       # orange
COLOR_TEXT = (255, 255, 255)    # white
FONT = cv2.FONT_HERSHEY_SIMPLEX


def draw_detections(
    frame: np.ndarray,
    tracks: Dict[int, Track],
    stopped_ids: Optional[set] = None,
) -> np.ndarray:
    """Draw bounding boxes and track IDs on the frame."""
    out = frame.copy()
    stopped_ids = stopped_ids or set()

    for tid, track in tracks.items():
        x1, y1, x2, y2 = [int(v) for v in track.bbox]
        color = COLOR_STOPPED if tid in stopped_ids else COLOR_MOVING
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        label = f"#{tid} {track.class_name}"
        cv2.putText(out, label, (x1, max(y1 - 6, 10)), FONT, 0.5, color, 1, cv2.LINE_AA)

    return out


def draw_roi(
    frame: np.ndarray,
    roi_polygon: List[List[int]],
) -> np.ndarray:
    """Draw the ROI polygon on the frame."""
    out = frame.copy()
    pts = np.array(roi_polygon, dtype=np.int32).reshape((-1, 1, 2))
    cv2.polylines(out, [pts], isClosed=True, color=COLOR_ROI, thickness=2)

    # Semi-transparent fill
    overlay = out.copy()
    cv2.fillPoly(overlay, [pts], COLOR_ROI)
    cv2.addWeighted(overlay, 0.1, out, 0.9, 0, out)
    return out


def draw_stopped_labels(
    frame: np.ndarray,
    stopped_events: List[StoppedEvent],
    tracks: Dict[int, Track],
) -> np.ndarray:
    """Draw STOPPED labels on stopped vehicle bounding boxes."""
    out = frame.copy()
    for event in stopped_events:
        track = tracks.get(event.track_id)
        if track is None:
            continue
        x1, y1, x2, y2 = [int(v) for v in track.bbox]
        cx = int(track.centroid[0])
        cy = int(track.centroid[1])
        label = f"STOPPED {event.duration:.1f}s"
        (tw, th), _ = cv2.getTextSize(label, FONT, 0.6, 2)
        cv2.rectangle(out, (cx - 4, cy - th - 4), (cx + tw + 4, cy + 4), (0, 0, 180), -1)
        cv2.putText(out, label, (cx, cy), FONT, 0.6, COLOR_TEXT, 2, cv2.LINE_AA)
    return out


def annotate_frame(
    frame: np.ndarray,
    tracks: Dict[int, Track],
    stopped_events: List[StoppedEvent],
    roi_polygon: Optional[List[List[int]]] = None,
) -> np.ndarray:
    """Convenience function: apply all overlays in the correct order."""
    stopped_ids = {e.track_id for e in stopped_events}
    out = frame
    if roi_polygon:
        out = draw_roi(out, roi_polygon)
    out = draw_detections(out, tracks, stopped_ids)
    out = draw_stopped_labels(out, stopped_events, tracks)
    return out
