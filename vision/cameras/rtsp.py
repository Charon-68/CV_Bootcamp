import time
from typing import Dict, Any, Optional
from vision.cameras.base import BaseCamera, logger
from vision.types import Frame

class RTSPCamera(BaseCamera):
    """RTSP Stream Camera source with reconnect logic."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.url = self.config.get("url", "rtsp://localhost:8554/live")
        self.width = self.config.get("width", 1920)
        self.height = self.config.get("height", 1080)
        self.connected = False

    def open(self) -> bool:
        logger.info(f"Connecting to RTSP URL: {self.url}")
        self.connected = True
        return True

    def read(self) -> Optional[Frame]:
        if not self.connected:
            self.reconnect()
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
            source=self.url,
        )

    def reconnect(self) -> None:
        self.reconnect_count += 1
        logger.info(f"Attempting RTSP Reconnect (Count: {self.reconnect_count}) to URL: {self.url}")
        # In mock scenario, always reconnect successfully
        self.connected = True

    def close(self) -> None:
        logger.info(f"Closing RTSP connection: {self.url}")
        self.connected = False

    def is_alive(self) -> bool:
        return self.connected

    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "RTSPCamera",
            "url": self.url,
            "width": self.width,
            "height": self.height,
        }
