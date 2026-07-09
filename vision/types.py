"""L3 — Shared vision data types.

These lightweight, dependency-free dataclasses are the payloads that flow
along graph edges between vision nodes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Tuple, Dict, Optional


@dataclass
class BoundingBox:
    """Strongly typed bounding box."""
    x1: float
    y1: float
    x2: float
    y2: float

    def to_tuple(self) -> Tuple[float, float, float, float]:
        return (self.x1, self.y1, self.x2, self.y2)

    @classmethod
    def from_tuple(cls, bbox: Tuple[float, float, float, float]) -> BoundingBox:
        return cls(bbox[0], bbox[1], bbox[2], bbox[3])


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
    bbox: Tuple[float, float, float, float]  # Preserve tuple format for backward compatibility
    track_id: Optional[int] = None
    text: Optional[str] = None  # optional OCR result


@dataclass
class Detections:
    """All detections for a frame."""
    frame_index: int
    items: List[Detection] = field(default_factory=list)


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
    detections: List[Detection] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)


# --- New Production Subsystem Schema Models ---

@dataclass
class FrameMetadata:
    """Metadata of the processed frame."""
    frame_id: int
    timestamp: float
    width: int
    height: int
    source: str


@dataclass
class DetectionStats:
    """Telemetry/metrics for detections."""
    inference_time_ms: float
    detection_count: int
    average_confidence: float


@dataclass
class DetectionResult:
    """Unified result containing the detections and performance metadata."""
    metadata: FrameMetadata
    detections: List[Detection]
    stats: DetectionStats


@dataclass
class TrackedObject:
    """Production tracked object containing trajectory, age, and kinematics."""
    track_id: int
    bbox: Tuple[float, float, float, float]
    class_name: str
    confidence: float
    velocity: Tuple[float, float] = (0.0, 0.0)
    first_seen: float = 0.0
    last_seen: float = 0.0
    age: int = 0
    trajectory: List[Tuple[float, float]] = field(default_factory=list)


@dataclass
class TrackResult:
    """Result returned by a tracker run."""
    frame_id: int
    tracked_objects: List[TrackedObject]
    active_tracks_count: int
    lost_tracks_count: int
