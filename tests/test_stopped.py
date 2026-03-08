"""Tests for stopped vehicle detection logic."""
import pytest
from app.skills.stopped import StoppedVehicleDetector
from app.schemas.report import Track


@pytest.fixture
def detector():
    return StoppedVehicleDetector()


def make_track(track_id, centroid_history):
    """Helper: centroid_history is list of (timestamp, [cx, cy])."""
    history = [[ts, c] for ts, c in centroid_history]
    first_c = centroid_history[0][1]
    return Track(
        track_id=track_id,
        bbox=[0.0, 0.0, 50.0, 50.0],
        centroid=list(first_c),
        class_name="car",
        history=history,
    )


def test_static_vehicle_flagged(detector):
    """A vehicle that doesn't move should be flagged as stopped."""
    history = [(float(i), [100.0, 200.0]) for i in range(20)]  # 20 seconds, no movement
    track = make_track(1, history)
    events = detector.check({1: track}, motion_threshold=10, min_stop_duration=5.0)
    assert len(events) == 1
    assert events[0].track_id == 1
    assert events[0].duration >= 5.0


def test_moving_vehicle_not_flagged(detector):
    """A vehicle moving steadily should NOT be flagged."""
    # Moving 20px per second — well above threshold
    history = [(float(i), [float(i * 20), 100.0]) for i in range(20)]
    track = make_track(2, history)
    events = detector.check({2: track}, motion_threshold=10, min_stop_duration=5.0)
    assert len(events) == 0


def test_briefly_stopped_not_flagged(detector):
    """A vehicle stopped for less than min_stop_duration is NOT flagged."""
    history = [(float(i), [50.0, 50.0]) for i in range(3)]  # only 3 seconds
    track = make_track(3, history)
    events = detector.check({3: track}, motion_threshold=10, min_stop_duration=5.0)
    assert len(events) == 0


def test_multiple_tracks(detector):
    """Multiple tracks processed: static → flagged, moving → not."""
    static_history = [(float(i), [100.0, 100.0]) for i in range(10)]
    moving_history = [(float(i), [float(i * 15), 100.0]) for i in range(10)]
    tracks = {
        1: make_track(1, static_history),
        2: make_track(2, moving_history),
    }
    events = detector.check(tracks, motion_threshold=10, min_stop_duration=5.0)
    stopped_ids = {e.track_id for e in events}
    assert 1 in stopped_ids
    assert 2 not in stopped_ids


def test_insufficient_history(detector):
    """A track with only one point should never be flagged."""
    history = [(0.0, [100.0, 100.0])]
    track = make_track(4, history)
    events = detector.check({4: track}, motion_threshold=10, min_stop_duration=5.0)
    assert len(events) == 0


def test_event_duration_accuracy(detector):
    """The reported duration should match the actual stopped window."""
    # Static from t=0 to t=12
    history = [(float(i), [200.0, 200.0]) for i in range(13)]
    track = make_track(5, history)
    events = detector.check({5: track}, motion_threshold=10, min_stop_duration=5.0)
    assert len(events) == 1
    assert abs(events[0].duration - 12.0) < 0.1
