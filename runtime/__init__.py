"""NexusGuard core: Layer 1 (nodes) and Layer 2 (graph engine & async runtime)."""

__version__ = "0.2.0"

from runtime.frame_queue import FrameQueue
from runtime.camera_manager import CameraManager
from runtime.worker_pool import DetectorPool, TrackingPool, ReasoningPool, StoragePool
from runtime.scheduler import PipelineScheduler
from runtime.events import FrameContext
from runtime.profiler import PerformanceProfiler

__all__ = [
    "FrameQueue",
    "CameraManager",
    "DetectorPool",
    "TrackingPool",
    "ReasoningPool",
    "StoragePool",
    "PipelineScheduler",
    "FrameContext",
    "PerformanceProfiler",
]
