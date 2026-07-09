"""L3 — Shared vision data types.

These lightweight, dependency-free dataclasses are the payloads that flow
along graph edges between vision nodes. They intentionally avoid importing
numpy/opencv so the graph contract stays importable in any environment;
concrete engines attach heavy arrays via the `data` field.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Frame:
    """A single captured frame."""

    index: int
    timestamp: float
    width: int
    height: int
    data: Any = None  # raw pixel buffer (e.g. numpy array) when available
    source: str = ""


@dataclass
class NormalizedFrame(Frame):
    """A cleaned/normalized frame ready for inference."""

    color_space: str = "RGB"


@dataclass
class Detection:
    """A single detected object."""

    label: str
    confidence: float
    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2
    track_id: int | None = None
    text: str | None = None  # optional OCR result


@dataclass
class Detections:
    """All detections for a frame."""

    frame_index: int
    items: list[Detection] = field(default_factory=list)


@dataclass
class VerifiedObjects(Detections):
    """Detections that passed schema/confidence/geometry validation."""

    dropped: int = 0


@dataclass
class Incident:
    """The reasoning core's human-readable, risk-scored output."""

    frame_index: int
    risk: float  # 0.0 (none) .. 1.0 (critical)
    label: str
    summary: str
    detections: list[Detection] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
