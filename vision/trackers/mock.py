from typing import List, Dict, Any
from vision.trackers.base import BaseTracker, logger
from vision.types import Detection, TrackResult, TrackedObject

class MockTracker(BaseTracker):
    """Mock tracker that assigns sequential IDs to detections."""

    def initialize(self) -> None:
        logger.info("Initializing MockTracker")
        self.next_id = 1

    def update(self, detections: List[Detection], frame_id: int) -> TrackResult:
        tracked_objects = []
        for det in detections:
            track_id = det.track_id
            if track_id is None:
                track_id = self.next_id
                self.next_id += 1
                self.total_tracks += 1

            # Update tracked object stats
            self.track_lifetimes[track_id] = self.track_lifetimes.get(track_id, 0) + 1

            tracked_objects.append(TrackedObject(
                track_id=track_id,
                bbox=det.bbox,
                class_name=det.label,
                confidence=det.confidence,
                age=self.track_lifetimes[track_id],
            ))

        self.active_tracks_count = len(tracked_objects)
        return TrackResult(
            frame_id=frame_id,
            tracked_objects=tracked_objects,
            active_tracks_count=self.active_tracks_count,
            lost_tracks_count=self.lost_tracks_count,
        )

    def reset(self) -> None:
        logger.info("Resetting MockTracker")
        self.next_id = 1
        self.track_lifetimes.clear()

    def shutdown(self) -> None:
        logger.info("Shutting down MockTracker")
