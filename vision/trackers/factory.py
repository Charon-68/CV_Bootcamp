from typing import Dict, Any, Type
from vision.trackers.base import BaseTracker
from vision.trackers.bytetrack import ByteTrackTracker
from vision.trackers.centroid import CentroidTracker
from vision.trackers.mock import MockTracker

class TrackerFactory:
    """Factory to dynamically instantiate object trackers from configuration."""

    _trackers: Dict[str, Type[BaseTracker]] = {
        "bytetrack": ByteTrackTracker,
        "centroid": CentroidTracker,
        "mock": MockTracker,
    }

    @classmethod
    def create(cls, tracker_type: str, config: Dict[str, Any] = None) -> BaseTracker:
        """Create and initialize a tracker by its type name."""
        tracker_class = cls._trackers.get(tracker_type.lower())
        if not tracker_class:
            raise ValueError(f"Unknown tracker type: '{tracker_type}'. Supported types: {list(cls._trackers.keys())}")
        
        tracker = tracker_class(config)
        tracker.initialize()
        return tracker

    @classmethod
    def register(cls, tracker_type: str, tracker_class: Type[BaseTracker]) -> None:
        """Register a custom tracker class at runtime."""
        cls._trackers[tracker_type.lower()] = tracker_class
