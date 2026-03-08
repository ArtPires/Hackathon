"""Tests for ROI filter."""
import pytest
from app.skills.roi import ROIFilter
from app.schemas.report import StoppedEvent, Track


@pytest.fixture
def roi_filter():
    return ROIFilter()


SQUARE_ROI = [[100, 100], [400, 100], [400, 400], [100, 400]]


def test_point_inside_roi(roi_filter):
    assert roi_filter.point_in_roi([250, 250], SQUARE_ROI) is True


def test_point_outside_roi(roi_filter):
    assert roi_filter.point_in_roi([50, 50], SQUARE_ROI) is False


def test_point_on_edge_roi(roi_filter):
    # On boundary is considered inside
    assert roi_filter.point_in_roi([100, 250], SQUARE_ROI) is True


def test_default_roi_coverage(roi_filter):
    """Default ROI should cover the center region of the frame."""
    frame_shape = (480, 640)
    roi = roi_filter.default_roi(frame_shape)
    # Center of frame should be inside
    assert roi_filter.point_in_roi([320, 240], roi) is True
    # Corners should be outside
    assert roi_filter.point_in_roi([1, 1], roi) is False
    assert roi_filter.point_in_roi([639, 479], roi) is False


def test_filter_events_inside(roi_filter):
    track = Track(track_id=1, bbox=[150.0, 150.0, 300.0, 300.0], centroid=[225.0, 225.0], class_name="car")
    event = StoppedEvent(track_id=1, start_time=0.0, end_time=10.0, duration=10.0)
    tracks = {1: track}
    filtered = roi_filter.filter_events([event], tracks, SQUARE_ROI)
    assert len(filtered) == 1


def test_filter_events_outside(roi_filter):
    track = Track(track_id=2, bbox=[10.0, 10.0, 50.0, 50.0], centroid=[30.0, 30.0], class_name="car")
    event = StoppedEvent(track_id=2, start_time=0.0, end_time=10.0, duration=10.0)
    tracks = {2: track}
    filtered = roi_filter.filter_events([event], tracks, SQUARE_ROI)
    assert len(filtered) == 0


def test_filter_events_mixed(roi_filter):
    track_in = Track(track_id=1, bbox=[150.0, 150.0, 300.0, 300.0], centroid=[225.0, 225.0], class_name="car")
    track_out = Track(track_id=2, bbox=[10.0, 10.0, 50.0, 50.0], centroid=[30.0, 30.0], class_name="bus")
    events = [
        StoppedEvent(track_id=1, start_time=0.0, end_time=10.0, duration=10.0),
        StoppedEvent(track_id=2, start_time=0.0, end_time=8.0, duration=8.0),
    ]
    tracks = {1: track_in, 2: track_out}
    filtered = roi_filter.filter_events(events, tracks, SQUARE_ROI)
    assert len(filtered) == 1
    assert filtered[0].track_id == 1
