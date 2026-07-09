import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class FrameContext:
    """Tracks a frame's lifecycle metadata and execution latencies throughout the pipeline."""
    frame_id: int
    camera_id: str
    timestamp: float = field(default_factory=time.time)
    sequence_number: int = 0
    source: str = ""
    
    # Latencies (in milliseconds)
    detector_latency_ms: float = 0.0
    tracker_latency_ms: float = 0.0
    reasoning_latency_ms: float = 0.0
    storage_latency_ms: float = 0.0
    total_latency_ms: float = 0.0

    # Payloads as they populate
    frame_data: Optional[Any] = None
    detections: Optional[Any] = None
    tracking_result: Optional[Any] = None
    incident: Optional[Any] = None

    def start_timing(self) -> float:
        return time.time()

    def record_stage(self, stage: str, start_time: float) -> None:
        latency = (time.time() - start_time) * 1000
        if stage == "detector":
            self.detector_latency_ms = latency
        elif stage == "tracker":
            self.tracker_latency_ms = latency
        elif stage == "reasoner":
            self.reasoning_latency_ms = latency
        elif stage == "storage":
            self.storage_latency_ms = latency
        
        # Recalculate total latency
        self.total_latency_ms = (time.time() - self.timestamp) * 1000


# --- Pipeline Lifecycle Event Structs ---

@dataclass
class FrameCaptured:
    frame_id: int
    camera_id: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class FrameDropped:
    frame_id: int
    camera_id: str
    reason: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class DetectionCompleted:
    frame_id: int
    camera_id: str
    latency_ms: float
    timestamp: float = field(default_factory=time.time)

@dataclass
class TrackingCompleted:
    frame_id: int
    camera_id: str
    latency_ms: float
    timestamp: float = field(default_factory=time.time)

@dataclass
class ReasoningCompleted:
    frame_id: int
    camera_id: str
    latency_ms: float
    timestamp: float = field(default_factory=time.time)

@dataclass
class StorageCompleted:
    frame_id: int
    camera_id: str
    latency_ms: float
    timestamp: float = field(default_factory=time.time)

@dataclass
class WorkerStarted:
    worker_id: str
    stage: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class WorkerStopped:
    worker_id: str
    stage: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class WorkerRestarted:
    worker_id: str
    stage: str
    reason: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class CameraDisconnected:
    camera_id: str
    reason: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class CameraReconnected:
    camera_id: str
    timestamp: float = field(default_factory=time.time)
