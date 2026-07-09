import time
from typing import Dict, Any, Optional
from vision.cameras.base import BaseCamera, logger
from vision.types import Frame

class ImageFolderCamera(BaseCamera):
    """Camera source reading from a folder of images."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.folder_path = self.config.get("folder_path", "images/")
        self.width = self.config.get("width", 640)
        self.height = self.config.get("height", 480)
        self.connected = False

    def open(self) -> bool:
        logger.info(f"Opening Image Folder: {self.folder_path}")
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
            source=f"{self.folder_path}/image_{idx}.jpg",
        )

    def close(self) -> None:
        logger.info(f"Closing Image Folder: {self.folder_path}")
        self.connected = False

    def is_alive(self) -> bool:
        return self.connected

    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "ImageFolderCamera",
            "folder_path": self.folder_path,
            "width": self.width,
            "height": self.height,
        }
