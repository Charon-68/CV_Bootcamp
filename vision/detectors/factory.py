from typing import Dict, Any, Type
from vision.detectors.base import BaseDetector
from vision.detectors.yolo import YOLODetector
from vision.detectors.opencv import OpenCVDetector
from vision.detectors.mock import MockDetector

class DetectorFactory:
    """Factory to dynamically instantiate object detectors from configuration."""

    _detectors: Dict[str, Type[BaseDetector]] = {
        "yolo": YOLODetector,
        "opencv": OpenCVDetector,
        "mock": MockDetector,
    }

    @classmethod
    def create(cls, detector_type: str, config: Dict[str, Any] = None) -> BaseDetector:
        """Create and initialize a detector by its type name."""
        detector_class = cls._detectors.get(detector_type.lower())
        if not detector_class:
            raise ValueError(f"Unknown detector type: '{detector_type}'. Supported types: {list(cls._detectors.keys())}")
        
        detector = detector_class(config)
        detector.initialize()
        return detector

    @classmethod
    def register(cls, detector_type: str, detector_class: Type[BaseDetector]) -> None:
        """Register a custom detector class at runtime."""
        cls._detectors[detector_type.lower()] = detector_class
