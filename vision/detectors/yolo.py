import time
from typing import Dict, Any
from vision.detectors.base import BaseDetector, logger
from vision.types import (
    NormalizedFrame,
    Detection,
    DetectionResult,
    FrameMetadata,
    DetectionStats,
)

class YOLODetector(BaseDetector):
    """YOLO Object Detector (with lightweight fallback)."""

    def initialize(self) -> None:
        logger.info(f"Initializing YOLODetector with weights: {self.config.get('weights', 'yolov8n.pt')}")

    def warmup(self) -> None:
        logger.info("Warming up YOLODetector")

    def detect(self, frame: NormalizedFrame) -> DetectionResult:
        start = time.time()
        self.frame_count += 1

        # Stub implementation to mimic YOLO run
        detections = [
            Detection(label="car", confidence=0.92, bbox=(100.0, 80.0, 300.0, 250.0)),
            Detection(label="person", confidence=0.78, bbox=(250.0, 150.0, 320.0, 350.0)),
        ]

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
        logger.info("Shutting down YOLODetector")

    def metadata(self) -> Dict[str, Any]:
        return {"name": "YOLODetector", "type": "yolo", "version": "8.0.0"}
