"""Phase 8 tests for the L3 vision engine nodes.

Exercises the S0-S3 pipeline nodes (Capture, Clean, Detect, Validate)
without GPU/model dependencies, relying on the deterministic stub paths.
"""
from __future__ import annotations

from vision.nodes import CaptureNode, CleanNode, DetectNode, ValidateNode
from vision.types import (
    Detection,
    Detections,
    Frame,
    NormalizedFrame,
    VerifiedObjects,
)


def test_capture_emits_frame():
    node = CaptureNode(config={"width": 320, "height": 240})
    result = node.run({})
    frame = result.outputs["frame"]
    assert isinstance(frame, Frame)
    assert frame.index == 0
    assert frame.width == 320
    assert frame.height == 240


def test_capture_increments_index():
    node = CaptureNode()
    first = node.run({}).outputs["frame"]
    second = node.run({}).outputs["frame"]
    assert first.index == 0
    assert second.index == 1


def test_clean_normalizes_frame():
    frame = Frame(index=3, timestamp=1.0, width=1920, height=1080, source="stub")
    node = CleanNode(config={"size": 640})
    normalized = node.run({"frame": frame}).outputs["frame"]
    assert isinstance(normalized, NormalizedFrame)
    assert normalized.width == 640
    assert normalized.height == 640
    assert normalized.index == 3


def test_detect_empty_without_backend():
    frame = NormalizedFrame(index=0, timestamp=1.0, width=640, height=640)
    detections = DetectNode().run({"frame": frame}).outputs["detections"]
    assert isinstance(detections, Detections)
    assert detections.items == []


def test_detect_uses_injected_detector():
    frame = NormalizedFrame(index=7, timestamp=1.0, width=640, height=640)

    def detector(_frame):
        return [Detection(label="person", confidence=0.9, bbox=(0.0, 0.0, 1.0, 1.0))]

    detections = DetectNode(config={"detector": detector}).run(
        {"frame": frame}
    ).outputs["detections"]
    assert len(detections.items) == 1
    assert detections.items[0].label == "person"
    assert detections.frame_index == 7


def test_validate_drops_low_confidence_and_bad_bbox():
    items = [
        Detection(label="a", confidence=0.9, bbox=(0.0, 0.0, 1.0, 1.0)),
        Detection(label="b", confidence=0.1, bbox=(0.0, 0.0, 1.0, 1.0)),
        Detection(label="c", confidence=0.9, bbox=(1.0, 1.0, 0.0, 0.0)),
    ]
    detections = Detections(frame_index=2, items=items)
    node = ValidateNode(config={"min_confidence": 0.25})
    validated = node.run({"detections": detections}).outputs["detections"]
    assert isinstance(validated, VerifiedObjects)
    assert len(validated.items) == 1
    assert validated.dropped == 2
    assert validated.frame_index == 2
