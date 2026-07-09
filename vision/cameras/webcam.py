import time
from typing import Dict, Any, Optional
from vision.cameras.base import BaseCamera, logger
from vision.types import Frame

class WebcamCamera(BaseCamera):
    """Webcam Camera source (using OpenCV internally)."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.device_id = self.config.get("device_id", 0)
        self.width = self.config.get("width", 640)
        self.height = self.config.get("height", 480)
        self.connected = False

    def open(self) -> bool:
        logger.info(f"Opening WebcamCamera device {self.device_id}")
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
            source=f"webcam://{self.device_id}",
        )

    def close(self) -> None:
        logger.info(f"Closing WebcamCamera device {self.device_id}")
        self.connected = False

    def is_alive(self) -> bool:
        return self.connected

    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "WebcamCamera",
            "device_id": self.device_id,
            "width": self.width,
            "height": self.height,
        }
