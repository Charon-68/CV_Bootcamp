import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from vision.types import NormalizedFrame, DetectionResult
from runtime.logger import get_logger

logger = get_logger("nexusguard.vision.detectors")

class BaseDetector(ABC):
    """Abstract Base Class for all Object Detectors."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.inference_times: List[float] = []
        self.total_detections = 0
        self.start_time = time.time()
        self.frame_count = 0

    @abstractmethod
    def initialize(self) -> None:
        """Initialize models, weights, or devices."""
        pass

    @abstractmethod
    def detect(self, frame: NormalizedFrame) -> DetectionResult:
        """Perform object detection on the input frame."""
        pass

    @abstractmethod
    def warmup(self) -> None:
        """Warm up the model (e.g., execute dummy runs)."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Release resources, models, and buffers."""
        pass

    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Return metadata about the detector model."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Return runtime statistics for monitoring."""
        avg_inf_time = sum(self.inference_times) / len(self.inference_times) if self.inference_times else 0.0
        elapsed = time.time() - self.start_time
        avg_fps = self.frame_count / elapsed if elapsed > 0 else 0.0
        return {
            "inference_time_ms": avg_inf_time * 1000,
            "average_fps": avg_fps,
            "detection_count": self.total_detections,
        }
