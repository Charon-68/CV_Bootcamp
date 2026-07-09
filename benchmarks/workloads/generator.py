from typing import List, Dict, Any
import time
import uuid
import numpy as np
from vision.types import NormalizedFrame, Detection, Detections, VerifiedObjects, Incident

class SyntheticLoadGenerator:
    """Generates synthetic payloads for isolated stage benchmarking."""

    @staticmethod
    def generate_frames(count: int, width: int = 640, height: int = 480) -> List[NormalizedFrame]:
        """Generate synthetic RGB frames (numpy arrays)."""
        frames = []
        for i in range(count):
            # Create a synthetic image payload (e.g. random noise or a blank frame with a shape)
            data = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
            frames.append(NormalizedFrame(
                index=i,
                data=data,
                source=f"synthetic_cam_{uuid.uuid4().hex[:6]}",
                timestamp=time.time(),
                width=width,
                height=height
            ))
        return frames

    @staticmethod
    def generate_detections(count: int, items_per_frame: int = 5) -> List[Detections]:
        """Generate synthetic detection payloads."""
        payloads = []
        for i in range(count):
            items = []
            for j in range(items_per_frame):
                items.append(Detection(
                    label="synthetic_object",
                    confidence=0.95,
                    bbox=(10.0, 10.0, 50.0, 50.0)
                ))
            payloads.append(Detections(frame_index=i, items=items))
        return payloads

    @staticmethod
    def generate_verified_objects(count: int, items_per_frame: int = 5) -> List[VerifiedObjects]:
        """Generate synthetic verified objects for reasoning tests."""
        payloads = []
        for i in range(count):
            items = []
            for j in range(items_per_frame):
                items.append(Detection(
                    label="verified_synthetic",
                    confidence=0.99,
                    bbox=(10.0, 10.0, 50.0, 50.0),
                    track_id=str(uuid.uuid4())
                ))
            payloads.append(VerifiedObjects(frame_index=i, items=items))
        return payloads

    @staticmethod
    def generate_incidents(count: int) -> List[Incident]:
        """Generate synthetic incident payloads for storage tests."""
        payloads = []
        for i in range(count):
            payloads.append(Incident(
                frame_index=i,
                risk=0.85,
                label="synthetic_alert",
                summary=f"Synthetic test alert #{i}",
                detections=[]
            ))
        return payloads
