import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from vision.types import Frame
from runtime.logger import get_logger

logger = get_logger("nexusguard.vision.cameras")

class BaseCamera(ABC):
    """Abstract Base Class for all Camera Sources."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.fps_counter = 0
        self.dropped_frames = 0
        self.reconnect_count = 0
        self.start_time = time.time()
        self.frame_count = 0

    @abstractmethod
    def open(self) -> bool:
        """Open the camera connection/stream."""
        pass

    @abstractmethod
    def read(self) -> Optional[Frame]:
        """Read a single Frame from the camera stream."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close/release the camera resources."""
        pass

    @abstractmethod
    def is_alive(self) -> bool:
        """Check if the camera is currently connected and alive."""
        pass

    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Return metadata about the camera device/stream."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Return runtime statistics for monitoring."""
        elapsed = time.time() - self.start_time
        avg_fps = self.frame_count / elapsed if elapsed > 0 else 0.0
        return {
            "fps": avg_fps,
            "dropped_frames": self.dropped_frames,
            "reconnect_count": self.reconnect_count,
        }
