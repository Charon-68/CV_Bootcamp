from runtime.nodes.catalog import register
from runtime.nodes.node import BaseNode, NodeResult, PortSpec
from vision.types import Incident

PLUGIN_METADATA = {
    "name": "WebhookAlert",
    "version": "1.0.0",
    "author": "Architect",
    "description": "Send POST requests to external alert webhooks.",
    "supported_inputs": ["Incident"],
    "supported_outputs": [],
}

@register("webhook_alert")
class WebhookAlert(BaseNode):
    """Sends webhook payloads for high-risk incidents."""
    
    inputs = (PortSpec("incident", Incident),)

    def run(self, inputs: dict) -> NodeResult:
        incident: Incident = inputs["incident"]
        webhook_url = self.config.get("url", "http://localhost:9000/alert")
        # Simulate HTTP post request
        return NodeResult(outputs={})
