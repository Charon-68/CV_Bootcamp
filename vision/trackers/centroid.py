from typing import List, Dict, Any
from vision.trackers.base import BaseTracker, logger
from vision.types import Detection, TrackResult, TrackedObject

class CentroidTracker(BaseTracker):
    """Centroid-based Object Tracker."""

    def initialize(self) -> None:
        logger.info("Initializing CentroidTracker")
        self.next_id = 1
        self.active_tracks: Dict[int, TrackedObject] = {}

    def update(self, detections: List[Detection], frame_id: int) -> TrackResult:
        tracked_objects = []

        for det in detections:
            matched_id = None
            for tid, tobj in self.active_tracks.items():
                if tobj.class_name == det.label:
                    matched_id = tid
                    break

            if matched_id is None:
                matched_id = self.next_id
                self.next_id += 1
                self.total_tracks += 1

            self.track_lifetimes[matched_id] = self.track_lifetimes.get(matched_id, 0) + 1

            tobj = TrackedObject(
                track_id=matched_id,
                bbox=det.bbox,
                class_name=det.label,
                confidence=det.confidence,
                age=self.track_lifetimes[matched_id],
                trajectory=[(det.bbox[0], det.bbox[1])],
            )
            self.active_tracks[matched_id] = tobj
            tracked_objects.append(tobj)

        updated_ids = {t.track_id for t in tracked_objects}
        lost_ids = set(self.active_tracks.keys()) - updated_ids
        for lid in lost_ids:
            del self.active_tracks[lid]
            self.lost_tracks_count += 1

        self.active_tracks_count = len(tracked_objects)
        return TrackResult(
            frame_id=frame_id,
            tracked_objects=tracked_objects,
            active_tracks_count=self.active_tracks_count,
            lost_tracks_count=self.lost_tracks_count,
        )

    def reset(self) -> None:
        logger.info("Resetting CentroidTracker")
        self.next_id = 1
        self.active_tracks.clear()
        self.track_lifetimes.clear()

    def shutdown(self) -> None:
        logger.info("Shutting down CentroidTracker")
