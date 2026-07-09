from abc import ABC, abstractmethod
from typing import Dict, Any, List
from vision.types import Detection, TrackResult
from runtime.logger import get_logger

logger = get_logger("nexusguard.vision.trackers")

class BaseTracker(ABC):
    """Abstract Base Class for all Object Trackers."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.total_tracks = 0
        self.active_tracks_count = 0
        self.lost_tracks_count = 0
        self.track_lifetimes: Dict[int, int] = {}  # track_id -> frame_count

    @abstractmethod
    def initialize(self) -> None:
        """Initialize tracker structures."""
        pass

    @abstractmethod
    def update(self, detections: List[Detection], frame_id: int) -> TrackResult:
        """Update tracker with new detections and return TrackResult."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset internal tracker state."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown and release resources."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Return runtime statistics for monitoring."""
        avg_lifetime = (
            sum(self.track_lifetimes.values()) / len(self.track_lifetimes)
            if self.track_lifetimes else 0.0
        )
        return {
            "track_count": self.total_tracks,
            "track_lifetime": avg_lifetime,
            "lost_tracks": self.lost_tracks_count,
        }
