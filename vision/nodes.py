"""L3 — Vision engine nodes (S0-S3).

Concrete, registered Node subclasses implementing the front half of the
pipeline: Ingest (Capture), Process (Clean), Analyze (Detect), Verify (Validate).
They delegate heavy operations to modular Camera, Detector, and Tracker objects.
"""
from __future__ import annotations

import time
from typing import Any

from runtime.nodes import Node, NodeResult, PortSpec, register
from vision.types import (
    Detection,
    Detections,
    Frame,
    NormalizedFrame,
    VerifiedObjects,
)
from vision.cameras.factory import CameraFactory
from vision.detectors.factory import DetectorFactory


@register()
class CaptureNode(Node):
    """S0 — Capture: emit a frame from a configured camera source."""

    name = "capture"
    inputs = (PortSpec("source", str, required=False),)
    outputs = (PortSpec("frame", Frame),)

    def __init__(self, config: dict[str, Any] | None = None, **kwargs: Any) -> None:
        super().__init__(config, **kwargs)
        self._camera = None

    def _get_camera(self, source: str) -> Any:
        if self._camera is not None:
            return self._camera

        # Check if config has an explicit camera type or default to mock
        cam_type = self.config.get("type")
        if not cam_type:
            # Resolve from source format
            if source.startswith("rtsp://"):
                cam_type = "rtsp"
            elif source.endswith((".mp4", ".avi", ".mkv")):
                cam_type = "video"
            else:
                cam_type = "mock"

        # Merge config
        cam_config = {
            "source": source,
            "width": int(self.config.get("width", 640)),
            "height": int(self.config.get("height", 480)),
        }
        self._camera = CameraFactory.create(cam_type, cam_config)
        return self._camera

    def run(self, inputs: dict[str, Any]) -> NodeResult:
        source = inputs.get("source", self.config.get("source", "stub://camera"))
        
        # Open camera source and read frame
        camera = self._get_camera(source)
        frame = camera.read()

        if frame is None:
            # Fallback frame on camera read failure
            idx = int(self.config.get("_index", 0))
            self.config["_index"] = idx + 1
            frame = Frame(
                index=idx,
                timestamp=time.time(),
                width=int(self.config.get("width", 640)),
                height=int(self.config.get("height", 480)),
                source=source,
            )

        return NodeResult(outputs={"frame": frame})


@register()
class CleanNode(Node):
    """S1 — Clean: resize/normalize a frame for inference."""

    name = "clean"
    inputs = (PortSpec("frame", Frame),)
    outputs = (PortSpec("frame", NormalizedFrame),)

    def run(self, inputs: dict[str, Any]) -> NodeResult:
        frame: Frame = inputs["frame"]
        target = int(self.config.get("size", 640))
        normalized = NormalizedFrame(
            index=frame.index,
            timestamp=frame.timestamp,
            width=target,
            height=target,
            data=frame.data,
            source=frame.source,
            color_space=self.config.get("color_space", "RGB"),
        )
        return NodeResult(outputs={"frame": normalized})


@register()
class DetectNode(Node):
    """S2 — Detect: run object detection on a normalized frame."""

    name = "detect"
    inputs = (PortSpec("frame", NormalizedFrame),)
    outputs = (PortSpec("detections", Detections),)

    def __init__(self, config: dict[str, Any] | None = None, **kwargs: Any) -> None:
        super().__init__(config, **kwargs)
        self._detector = None

    def _get_detector(self) -> Any:
        if self._detector is not None:
            return self._detector

        detector_type = self.config.get("type", "mock")
        # Use factory to initialize detector
        self._detector = DetectorFactory.create(detector_type, self.config)
        return self._detector

    def run(self, inputs: dict[str, Any]) -> NodeResult:
        frame: NormalizedFrame = inputs["frame"]
        detector = self._get_detector()
        detection_result = detector.detect(frame)
        detections = Detections(
            frame_index=frame.index,
            items=detection_result.detections,
        )
        return NodeResult(outputs={"detections": detections})


@register()
class ValidateNode(Node):
    """S3 — Validate: drop low-confidence / malformed detections."""

    name = "validate"
    inputs = (PortSpec("detections", Detections),)
    outputs = (PortSpec("detections", VerifiedObjects),)

    def run(self, inputs: dict[str, Any]) -> NodeResult:
        detections: Detections = inputs["detections"]
        min_conf = float(self.config.get("min_confidence", 0.25))
        kept: list[Detection] = []
        dropped = 0
        for det in detections.items:
            if det.confidence < min_conf or not _valid_bbox(det.bbox):
                dropped += 1
                continue
            kept.append(det)
        validated = VerifiedObjects(
            frame_index=detections.frame_index,
            items=kept,
            dropped=dropped,
        )
        return NodeResult(outputs={"detections": validated})


def _valid_bbox(bbox: tuple[float, float, float, float]) -> bool:
    x1, y1, x2, y2 = bbox
    return x2 > x1 and y2 > y1
