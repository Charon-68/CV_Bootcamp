import time
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List

@dataclass
class ExecutionContext:
    """Carries runtime information, shared variables, configuration, and logs for a workflow execution run."""
    workflow_id: str
    execution_id: str
    frame_id: int
    camera_id: str
    timestamp: float = field(default_factory=time.time)
    shared_state: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("nexusguard.execution"))


# --- Workflow Lifecycle Events ---

@dataclass
class WorkflowStarted:
    workflow_id: str
    execution_id: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class WorkflowStopped:
    workflow_id: str
    execution_id: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class WorkflowPaused:
    workflow_id: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class NodeStarted:
    node_name: str
    workflow_id: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class NodeFinished:
    node_name: str
    workflow_id: str
    latency_ms: float
    timestamp: float = field(default_factory=time.time)

@dataclass
class NodeFailed:
    node_name: str
    workflow_id: str
    error: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class ValidationFailed:
    workflow_id: str
    errors: List[str]
    timestamp: float = field(default_factory=time.time)

@dataclass
class PluginLoaded:
    plugin_name: str
    version: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class PluginUnloaded:
    plugin_name: str
    timestamp: float = field(default_factory=time.time)
