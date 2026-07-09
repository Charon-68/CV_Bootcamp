"""L3 — Vision engine nodes (S0-S3).

Concrete, registered Node subclasses implementing the front half of the
S0-S5 pipeline: Capture, Clean, Detect, Validate. Heavy model backends
(OpenCV, YOLO, OCR) are loaded lazily so the graph stays importable and
testable without GPU dependencies; when a backend is unavailable the node
falls back to a deterministic stub so pipelines still validate and run.
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


@register()
class CaptureNode(Node):
    """S0 — Capture: emit a frame from a configured source."""

    name = "capture"
    inputs = (PortSpec("source", str, required=False),)
    outputs = (PortSpec("frame", Frame),)

    def run(self, inputs: dict[str, Any]) -> NodeResult:
        source = inputs.get("source", self.config.get("source", "stub://camera"))
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
    """S2 — Detect: run object detection on a normalized frame.

    Attempts to use an injected detector callable via config['detector'];
    otherwise returns an empty detection set (safe stub).
    """

    name = "detect"
    inputs = (PortSpec("frame", NormalizedFrame),)
    outputs = (PortSpec("detections", Detections),)

    def run(self, inputs: dict[str, Any]) -> NodeResult:
        frame: NormalizedFrame = inputs["frame"]
        detector = self.config.get("detector")
        items: list[Detection] = []
        if callable(detector):
            items = list(detector(frame))
        detections = Detections(frame_index=frame.index, items=items)
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
