from runtime.nodes.catalog import register
from runtime.nodes.node import BaseNode, NodeResult, PortSpec
from vision.types import NormalizedFrame, Detections, Detection

PLUGIN_METADATA = {
    "name": "EdgeDetector",
    "version": "1.0.0",
    "author": "Architect",
    "description": "Pluggable Sobel/Canny Edge Detection simulator.",
    "supported_inputs": ["NormalizedFrame"],
    "supported_outputs": ["Detections"],
}

@register("edge_detector")
class EdgeDetector(BaseNode):
    """Simulated Edge Detector plugin."""
    
    inputs = (PortSpec("frame", NormalizedFrame),)
    outputs = (PortSpec("detections", Detections),)

    def run(self, inputs: dict) -> NodeResult:
        frame: NormalizedFrame = inputs["frame"]
        # Simulate finding edge contours as person/object detections
        detections = Detections(
            frame_index=frame.index,
            items=[
                Detection(label="edge_contour", confidence=0.91, bbox=(50.0, 50.0, 150.0, 150.0))
            ]
        )
        return NodeResult(outputs={"detections": detections})
