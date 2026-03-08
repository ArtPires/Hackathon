"""Skill: capture_stream — Open a video source and yield frames."""
import cv2
from typing import Generator, Tuple, Dict, Any, Union


class CaptureStream:
    """Opens a camera, video file, or RTSP stream and provides frame iteration."""

    def __init__(self):
        self.cap = None
        self.metadata: Dict[str, Any] = {}

    def open(self, source: Union[int, str]) -> "CaptureStream":
        """Open the video source. source can be webcam index, file path, or RTSP URL."""
        if isinstance(source, str) and source.isdigit():
            source = int(source)

        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open video source: {source!r}")

        self.metadata = {
            "fps": self.cap.get(cv2.CAP_PROP_FPS) or 25.0,
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "source": source,
        }
        return self

    def frames(self) -> Generator[Tuple[Any, Dict[str, Any]], None, None]:
        """Yield (frame, metadata) tuples until the source ends."""
        if self.cap is None:
            raise RuntimeError("Call open() before iterating frames.")
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            yield frame, self.metadata

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.release()
