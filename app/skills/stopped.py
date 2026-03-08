"""Skill: detect_stopped_vehicles — Flag tracked vehicles that remain stationary."""
import math
from typing import Dict, List

from app.config import settings
from app.schemas.report import Track, StoppedEvent


class StoppedVehicleDetector:
    """
    Analyses track histories to identify vehicles that have been stationary
    for longer than a configurable time threshold.
    """

    def check(
        self,
        tracks: Dict[int, Track],
        motion_threshold: int = None,
        min_stop_duration: float = None,
    ) -> List[StoppedEvent]:
        """
        For each track, check whether the vehicle has been stopped.

        A vehicle is considered stopped if the maximum displacement between any
        two centroid positions within a rolling window is below motion_threshold
        for at least min_stop_duration seconds.

        Returns a list of StoppedEvent objects.
        """
        threshold = motion_threshold if motion_threshold is not None else settings.MOTION_THRESHOLD
        min_duration = min_stop_duration if min_stop_duration is not None else settings.MIN_STOP_DURATION

        events: List[StoppedEvent] = []

        for tid, track in tracks.items():
            history = track.history  # list of [timestamp, [cx, cy]]
            if len(history) < 2:
                continue

            event = self._find_stop_event(history, threshold, min_duration)
            if event:
                event.track_id = tid
                event.class_name = track.class_name
                events.append(event)

        return events

    def _find_stop_event(
        self,
        history: List,
        threshold: int,
        min_duration: float,
    ) -> StoppedEvent | None:
        """
        Scan history for the longest contiguous stopped window.
        Returns StoppedEvent if any window exceeds min_duration, else None.
        """
        if len(history) < 2:
            return None

        best_start_idx = None
        best_end_idx = None
        best_duration = 0.0

        window_start = 0

        for i in range(1, len(history)):
            # Check displacement from window_start to i
            ts_start, c_start = history[window_start]
            ts_end, c_end = history[i]
            max_disp = self._max_displacement(history[window_start:i + 1])

            if max_disp <= threshold:
                duration = ts_end - ts_start
                if duration > best_duration:
                    best_duration = duration
                    best_start_idx = window_start
                    best_end_idx = i
            else:
                # Move window start forward to shrink the window
                window_start = i

        if best_duration >= min_duration and best_start_idx is not None:
            return StoppedEvent(
                track_id=-1,  # filled by caller
                start_time=history[best_start_idx][0],
                end_time=history[best_end_idx][0],
                duration=best_duration,
                class_name="vehicle",
            )
        return None

    @staticmethod
    def _max_displacement(history_slice: List) -> float:
        """Compute the maximum pairwise distance among centroids in history_slice."""
        centroids = [h[1] for h in history_slice]
        if len(centroids) < 2:
            return 0.0
        max_d = 0.0
        ref = centroids[0]
        for c in centroids[1:]:
            d = math.hypot(c[0] - ref[0], c[1] - ref[1])
            if d > max_d:
                max_d = d
        return max_d
