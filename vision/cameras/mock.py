import time
from typing import Dict, Any, Optional
from vision.cameras.base import BaseCamera, logger
from vision.types import Frame

class MockCamera(BaseCamera):
    """Mock Camera generating dummy frames for testing/pipelines."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.width = self.config.get("width", 640)
        self.height = self.config.get("height", 480)
        self.source = self.config.get("source", "mock://camera")
        self.connected = False

    def open(self) -> bool:
        logger.info("Opening MockCamera source")
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
            source=self.source,
        )

    def close(self) -> None:
        logger.info("Closing MockCamera")
        self.connected = False

    def is_alive(self) -> bool:
        return self.connected

    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "MockCamera",
            "width": self.width,
            "height": self.height,
            "source": self.source,
        }
