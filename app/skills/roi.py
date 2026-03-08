"""Skill: filter_by_roi — Restrict analysis to a region of interest polygon."""
from typing import List, Optional, Tuple
import numpy as np
import cv2

from app.schemas.report import Detection, StoppedEvent, Track


class ROIFilter:
    """
    Filters detections, tracks, or stopped events to only include
    objects whose centroid falls inside a given polygon ROI.
    """

    def default_roi(self, frame_shape: Tuple[int, int]) -> List[List[int]]:
        """Return a polygon covering the center 60% of the frame."""
        h, w = frame_shape[:2]
        x_margin = int(w * 0.2)
        y_margin = int(h * 0.2)
        return [
            [x_margin, y_margin],
            [w - x_margin, y_margin],
            [w - x_margin, h - y_margin],
            [x_margin, h - y_margin],
        ]

    def point_in_roi(
        self,
        point: List[float],
        roi_polygon: List[List[int]],
    ) -> bool:
        """Return True if the (x, y) point lies inside the roi_polygon."""
        poly = np.array(roi_polygon, dtype=np.int32)
        result = cv2.pointPolygonTest(poly, (float(point[0]), float(point[1])), False)
        return result >= 0  # 1 = inside, 0 = on edge, -1 = outside

    def filter_detections(
        self,
        detections: List[Detection],
        roi_polygon: List[List[int]],
    ) -> List[Detection]:
        """Return only detections whose centroid is inside the ROI."""
        return [d for d in detections if self.point_in_roi(d.centroid, roi_polygon)]

    def filter_events(
        self,
        events: List[StoppedEvent],
        tracks: dict,
        roi_polygon: List[List[int]],
        frame_shape: Optional[Tuple[int, int]] = None,
    ) -> List[StoppedEvent]:
        """
        Return only stopped events where the track's last centroid is inside the ROI.
        If roi_polygon is None and frame_shape is provided, use default ROI.
        """
        if roi_polygon is None:
            if frame_shape is None:
                return events
            roi_polygon = self.default_roi(frame_shape)

        filtered = []
        for event in events:
            track = tracks.get(event.track_id)
            if track is None:
                # No track data; include by default
                filtered.append(event)
                continue
            if self.point_in_roi(track.centroid, roi_polygon):
                filtered.append(event)
        return filtered
