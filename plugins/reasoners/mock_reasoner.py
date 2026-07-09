from runtime.nodes.catalog import register
from runtime.nodes.node import BaseNode, NodeResult, PortSpec
from vision.types import VerifiedObjects, Incident

PLUGIN_METADATA = {
    "name": "MockReasoner",
    "version": "1.0.0",
    "author": "Architect",
    "description": "Mock reasoning plugin scoring incidents heuristically.",
    "supported_inputs": ["VerifiedObjects"],
    "supported_outputs": ["Incident"],
}

@register("mock_reasoner")
class MockReasoner(BaseNode):
    """Fallback Mock Reasoner using heuristic risk logic."""
    
    inputs = (PortSpec("detections", VerifiedObjects),)
    outputs = (PortSpec("incident", Incident),)

    def run(self, inputs: dict) -> NodeResult:
        detections: VerifiedObjects = inputs["detections"]
        
        # Heuristic risk calculation
        risk = 0.0
        if detections.items:
            top = max(d.confidence for d in detections.items)
            count_factor = min(len(detections.items) / 5.0, 1.0)
            risk = round(min(0.5 * top + 0.5 * count_factor, 1.0), 3)

        incident = Incident(
            frame_index=detections.frame_index,
            risk=risk,
            label="mock_heuristics",
            summary=f"Pluggable mock reasoner scored risk at {risk * 100}%.",
            detections=detections.items,
        )
        return NodeResult(outputs={"incident": incident})
