"""Skill: sample_frames — Reduce frame rate to target FPS."""
from typing import Generator, Tuple, Dict, Any


def sample_frames(
    frame_source: Generator,
    target_fps: float = 3.0,
) -> Generator[Tuple[Any, float, Dict], None, None]:
    """
    Yield (frame, timestamp, metadata) at approximately target_fps.

    Args:
        frame_source: generator yielding (frame, metadata) from CaptureStream
        target_fps: desired output frames per second
    """
    frame_index = 0
    elapsed_time = 0.0

    for frame, metadata in frame_source:
        source_fps = metadata.get("fps", 25.0)
        frame_duration = 1.0 / source_fps
        elapsed_time = frame_index * frame_duration

        # Determine which frames to keep: keep frame if it falls on a sample boundary
        sample_interval = source_fps / target_fps
        if frame_index == 0 or (frame_index % max(1, round(sample_interval))) == 0:
            yield frame, elapsed_time, metadata

        frame_index += 1
