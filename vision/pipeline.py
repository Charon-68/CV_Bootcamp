import time
from typing import Dict, Any, Optional
from vision.cameras.base import BaseCamera
from vision.detectors.base import BaseDetector
from vision.trackers.base import BaseTracker
from vision.types import Frame, NormalizedFrame, DetectionResult, TrackResult
from runtime.logger import get_logger

logger = get_logger("nexusguard.vision.pipeline")

class VisionPipeline:
    """Production-style modular Vision Pipeline executing camera -> detector -> tracker."""

    def __init__(
        self,
        camera: Optional[BaseCamera] = None,
        detector: Optional[BaseDetector] = None,
        tracker: Optional[BaseTracker] = None,
    ):
        self.camera = camera
        self.detector = detector
        self.tracker = tracker

    def run_once(self) -> Optional[dict]:
        """Execute a single processing step of the vision pipeline.

        Returns:
            Dict containing metadata, detections, tracking results, or None.
        """
        if not self.camera or not self.detector:
            logger.warning("Pipeline executed without initialized camera or detector.")
            return None

        try:
            # 1. Camera Ingest
            frame = self.camera.read()
            if frame is None:
                logger.warning("Camera read returned empty frame.")
                return None

            # 2. Normalize frame (for model input format compatibility)
            normalized_frame = NormalizedFrame(
                index=frame.index,
                timestamp=frame.timestamp,
                width=frame.width,
                height=frame.height,
                data=frame.data,
                source=frame.source,
            )

            # 3. Object Detection
            detection_result = self.detector.detect(normalized_frame)

            # 4. Object Tracking
            track_result = None
            if self.tracker:
                track_result = self.tracker.update(detection_result.detections, frame.index)

            return {
                "frame": frame,
                "detection_result": detection_result,
                "track_result": track_result,
            }

        except Exception as e:
            logger.error(f"Error executing pipeline step: {e}", exc_info=True)
            return None
