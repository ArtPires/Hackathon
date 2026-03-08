"""Skill: track_objects — Centroid-based multi-object tracker."""
import math
from typing import Dict, List, Tuple, Optional
from collections import OrderedDict

from app.config import settings
from app.schemas.report import Detection, Track


class CentroidTracker:
    """
    Simple centroid tracker that assigns persistent IDs to detections.

    Matches new detections to existing tracks by nearest centroid distance.
    Maintains a history of centroid positions and timestamps per track.
    """

    def __init__(
        self,
        max_distance: int = None,
        max_lost_frames: int = None,
    ):
        self.max_distance = max_distance or settings.MAX_TRACK_DISTANCE
        self.max_lost_frames = max_lost_frames or settings.MAX_LOST_FRAMES
        self._next_id = 0
        # track_id → Track
        self._tracks: Dict[int, Track] = {}
        # track_id → frames since last matched
        self._lost_count: Dict[int, int] = {}

    def update(
        self,
        detections: List[Detection],
        timestamp: float,
    ) -> Dict[int, Track]:
        """
        Update tracker with new detections at the given timestamp.

        Returns the current active tracks (dict: track_id → Track).
        """
        # Increment lost counters for all existing tracks
        for tid in list(self._lost_count.keys()):
            self._lost_count[tid] += 1

        if not detections:
            # Remove stale tracks
            self._prune_lost()
            return dict(self._tracks)

        # If no existing tracks, register all detections
        if not self._tracks:
            for det in detections:
                self._register(det, timestamp)
            return dict(self._tracks)

        # Build cost matrix: existing tracks × new detections
        track_ids = list(self._tracks.keys())
        track_centroids = [self._tracks[tid].centroid for tid in track_ids]
        det_centroids = [det.centroid for det in detections]

        matched_tracks = set()
        matched_dets = set()

        # Greedy nearest-neighbour matching
        distances = []
        for ti, tc in enumerate(track_centroids):
            for di, dc in enumerate(det_centroids):
                dist = math.hypot(tc[0] - dc[0], tc[1] - dc[1])
                distances.append((dist, ti, di))
        distances.sort()

        for dist, ti, di in distances:
            if dist > self.max_distance:
                break
            if ti in matched_tracks or di in matched_dets:
                continue
            tid = track_ids[ti]
            self._update_track(tid, detections[di], timestamp)
            self._lost_count[tid] = 0
            matched_tracks.add(ti)
            matched_dets.add(di)

        # Register unmatched detections as new tracks
        for di, det in enumerate(detections):
            if di not in matched_dets:
                self._register(det, timestamp)

        self._prune_lost()
        return dict(self._tracks)

    def _register(self, det: Detection, timestamp: float):
        tid = self._next_id
        self._next_id += 1
        self._tracks[tid] = Track(
            track_id=tid,
            bbox=det.bbox,
            centroid=det.centroid,
            class_name=det.class_name,
            history=[[timestamp, det.centroid]],
        )
        self._lost_count[tid] = 0

    def _update_track(self, tid: int, det: Detection, timestamp: float):
        track = self._tracks[tid]
        track.bbox = det.bbox
        track.centroid = det.centroid
        track.class_name = det.class_name
        track.history.append([timestamp, det.centroid])

    def _prune_lost(self):
        to_delete = [
            tid for tid, count in self._lost_count.items()
            if count > self.max_lost_frames
        ]
        for tid in to_delete:
            del self._tracks[tid]
            del self._lost_count[tid]

    def reset(self):
        self._next_id = 0
        self._tracks.clear()
        self._lost_count.clear()
