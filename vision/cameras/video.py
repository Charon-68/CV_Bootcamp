import time
from typing import Dict, Any, Optional
from vision.cameras.base import BaseCamera, logger
from vision.types import Frame

class VideoCamera(BaseCamera):
    """Video File Camera source."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.path = self.config.get("path", "video.mp4")
        self.width = self.config.get("width", 1280)
        self.height = self.config.get("height", 720)
        self.connected = False

    def open(self) -> bool:
        logger.info(f"Opening Video file: {self.path}")
        self.connected = True
        return True

    def read(self) -> Optional[Frame]:
        if not self.connected:
            self.dropped_frames += 1
            return None
        
        idx = self.frame_count
        self.frame_count += 1
        return Frame(
            index=idx,
            timestamp=time.time(),
            width=self.width,
            height=self.height,
            source=self.path,
        )

    def close(self) -> None:
        logger.info(f"Closing Video file: {self.path}")
        self.connected = False

    def is_alive(self) -> bool:
        return self.connected

    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "VideoCamera",
            "path": self.path,
            "width": self.width,
            "height": self.height,
        }
