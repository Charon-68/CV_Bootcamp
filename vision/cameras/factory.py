from typing import Dict, Any, Type
from vision.cameras.base import BaseCamera
from vision.cameras.webcam import WebcamCamera
from vision.cameras.video import VideoCamera
from vision.cameras.image_folder import ImageFolderCamera
from vision.cameras.rtsp import RTSPCamera
from vision.cameras.mock import MockCamera

class CameraFactory:
    """Factory to dynamically instantiate camera sources from configuration."""

    _cameras: Dict[str, Type[BaseCamera]] = {
        "webcam": WebcamCamera,
        "video": VideoCamera,
        "image_folder": ImageFolderCamera,
        "rtsp": RTSPCamera,
        "mock": MockCamera,
    }

    @classmethod
    def create(cls, camera_type: str, config: Dict[str, Any] = None) -> BaseCamera:
        """Create and open a camera source by its type name."""
        camera_class = cls._cameras.get(camera_type.lower())
        if not camera_class:
            raise ValueError(f"Unknown camera type: '{camera_type}'. Supported types: {list(cls._cameras.keys())}")
        
        camera = camera_class(config)
        camera.open()
        return camera

    @classmethod
    def register(cls, camera_type: str, camera_class: Type[BaseCamera]) -> None:
        """Register a custom camera source class at runtime."""
        cls._cameras[camera_type.lower()] = camera_class
