from typing import List, Dict, Any
from collections import deque
from vision.types import VerifiedObjects
from runtime.logger import get_logger

logger = get_logger("nexusguard.memory")

class ConversationMemory:
    """Short-term conversational memory for the reasoning engine."""
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history = deque(maxlen=max_history)
        
    def add_interaction(self, detections: VerifiedObjects, context: dict, response: dict):
        """Record an interaction for context in future requests."""
        self.history.append({
            "frame_index": detections.frame_index,
            "detected_objects": len(detections.items),
            "context": context,
            "response_risk": response.get("risk", 0.0),
            "response_label": response.get("label", "unknown")
        })
        
    def get_context(self) -> List[Dict[str, Any]]:
        """Retrieve recent context for prompt augmentation."""
        return list(self.history)
        
    def clear(self):
        self.history.clear()
