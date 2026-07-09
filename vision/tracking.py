from abc import ABC, abstractmethod
from typing import List
from vision.types import Detection, Frame

class TrackerInterface(ABC):
    """Abstract interface for object tracking algorithms."""
    
    @abstractmethod
    def update(self, detections: List[Detection], frame: Frame) -> List[Detection]:
        """Update tracker with new detections and return detections with track_ids."""
        pass

class ByteTrackStub(TrackerInterface):
    """Lightweight ByteTrack stub implementation for tracking objects across frames."""
    
    def __init__(self, track_thresh=0.5, match_thresh=0.8):
        self.track_thresh = track_thresh
        self.match_thresh = match_thresh
        self.next_id = 1
        self.active_tracks = {}

    def update(self, detections: List[Detection], frame: Frame) -> List[Detection]:
        # A simple naive IoU or centroid tracking stub
        # In a real system, this would wrap ByteTrack or DeepSORT
        tracked_detections = []
        for det in detections:
            if det.confidence < self.track_thresh:
                continue
            
            # Very naive mock matching
            matched_id = None
            for tid, tdet in self.active_tracks.items():
                if tdet.label == det.label:
                    matched_id = tid
                    break
                    
            if matched_id is None:
                matched_id = self.next_id
                self.next_id += 1
                
            det.track_id = matched_id
            self.active_tracks[matched_id] = det
            tracked_detections.append(det)
            
        return tracked_detections
