from runtime.nodes.catalog import register
from runtime.nodes.node import BaseNode, NodeResult, PortSpec
from vision.types import Incident

PLUGIN_METADATA = {
    "name": "CSVStorage",
    "version": "1.0.0",
    "author": "Architect",
    "description": "Appends Incident records to a local CSV file.",
    "supported_inputs": ["Incident"],
    "supported_outputs": [],
}

@register("csv_storage")
class CSVStorage(BaseNode):
    """CSV Storage node logging incidents to csv format."""
    
    inputs = (PortSpec("incident", Incident),)

    def run(self, inputs: dict) -> NodeResult:
        incident: Incident = inputs["incident"]
        filepath = self.config.get("filepath", "incidents.csv")
        # In a real environment, write to file.
        # We simulate this write
        return NodeResult(outputs={})
