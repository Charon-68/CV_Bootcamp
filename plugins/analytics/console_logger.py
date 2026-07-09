from runtime.nodes.catalog import register
from runtime.nodes.node import BaseNode, NodeResult, PortSpec
from vision.types import Incident
from runtime.logger import get_logger

logger = get_logger("nexusguard.plugins.analytics.console_logger")

PLUGIN_METADATA = {
    "name": "ConsoleLogger",
    "version": "1.0.0",
    "author": "Architect",
    "description": "Log incidents formatted as human-readable console alerts.",
    "supported_inputs": ["Incident"],
    "supported_outputs": [],
}

@register("console_logger")
class ConsoleLogger(BaseNode):
    """Outputs incident telemetry directly to framework logger."""
    
    inputs = (PortSpec("incident", Incident),)

    def run(self, inputs: dict) -> NodeResult:
        incident: Incident = inputs["incident"]
        logger.info(f"🚨 [INCIDENT] Risk: {incident.risk * 100}% | Label: {incident.label} | Summary: {incident.summary}")
        return NodeResult(outputs={})
