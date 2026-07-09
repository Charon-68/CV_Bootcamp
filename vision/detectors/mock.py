import time
from typing import Dict, Any, List
from vision.detectors.base import BaseDetector, logger
from vision.types import (
    NormalizedFrame,
    Detection,
    DetectionResult,
    FrameMetadata,
    DetectionStats,
)

class MockDetector(BaseDetector):
    """Deterministic Mock Detector for testing and edge running."""

    def initialize(self) -> None:
        logger.info("Initializing MockDetector")

    def warmup(self) -> None:
        logger.info("Warming up MockDetector")

    def detect(self, frame: NormalizedFrame) -> DetectionResult:
        start = time.time()
        self.frame_count += 1

        # Return a simple mock detection (e.g. person) for demonstration/testing
        detections = []
        if self.config.get("mock_detections"):
            for mock_det in self.config["mock_detections"]:
                detections.append(Detection(
                    label=mock_det.get("label", "person"),
                    confidence=mock_det.get("confidence", 0.9),
                    bbox=tuple(mock_det.get("bbox", (0.0, 0.0, 1.0, 1.0))),
                ))
        else:
            # Default mock behavior
            # Check if there is a custom detector function passed in config (for unit tests compatibility)
            detector_fn = self.config.get("detector")
            if callable(detector_fn):
                detections = list(detector_fn(frame))
            else:
                detections = []

        self.total_detections += len(detections)
        inf_time = time.time() - start
        self.inference_times.append(inf_time)

        metadata = FrameMetadata(
            frame_id=frame.index,
            timestamp=frame.timestamp,
            width=frame.width,
            height=frame.height,
            source=frame.source,
        )
        avg_conf = sum(d.confidence for d in detections) / len(detections) if detections else 0.0
        stats = DetectionStats(
            inference_time_ms=inf_time * 1000,
            detection_count=len(detections),
            average_confidence=avg_conf,
        )
        return DetectionResult(metadata=metadata, detections=detections, stats=stats)

    def shutdown(self) -> None:
        logger.info("Shutting down MockDetector")

    def metadata(self) -> Dict[str, Any]:
        return {"name": "MockDetector", "type": "stub", "version": "1.0.0"}
