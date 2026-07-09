"""L1 — Node abstraction.

A BaseNode is a pure, declared transform with a name, typed input schema,
typed output schema, and config. Nodes are the atomic units of the NexusGuard
graph and self-register into the node catalog.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class PortSpec:
    """Typed I/O port: a logical name mapped to a Python type."""

    name: str
    type_: type
    required: bool = True


@dataclass
class NodeResult:
    """Output of a single node execution."""

    outputs: dict[str, Any]
    meta: dict[str, Any] = field(default_factory=dict)


class BaseNode(ABC):
    """Base class for all NexusGuard workflow nodes."""

    name: str = "node"
    inputs: Tuple[PortSpec, ...] = ()
    outputs: Tuple[PortSpec, ...] = ()

    def __init__(self, config: dict[str, Any] | None = None, **kwargs: Any) -> None:
        self.config = config if config is not None else kwargs

    def initialize(self) -> None:
        """Initialize resources, load weight files, etc."""
        pass

    @abstractmethod
    def run(self, inputs: dict[str, Any]) -> NodeResult:
        """Run the legacy graph execution logic. Subclasses implement this."""
        raise NotImplementedError

    def execute(self, inputs: dict[str, Any], context: Any = None) -> NodeResult:
        """Execute the node on validated inputs under an ExecutionContext."""
        self.validate_inputs(inputs)
        return self.run(inputs)

    def shutdown(self) -> None:
        """Shutdown node and release any allocated system resources."""
        pass

    def metadata(self) -> dict[str, Any]:
        """Return metadata about the node."""
        return {
            "name": self.name,
            "inputs": [p.name for p in self.inputs],
            "outputs": [p.name for p in self.outputs],
        }

    def validate(self) -> Tuple[bool, list[str]]:
        """Validate node configuration parameters."""
        return True, []

    def health(self) -> str:
        """Return the current node health state ('Healthy', 'Warning', 'Failed')."""
        return "Healthy"

    def validate_inputs(self, inputs: dict[str, Any]) -> None:
        """Check that required input ports are present and typed correctly."""
        for port in self.inputs:
            if port.required and port.name not in inputs:
                raise ValueError(f"{self.name}: missing required input '{port.name}'")
            if port.name in inputs and not isinstance(inputs[port.name], port.type_):
                raise TypeError(
                    f"{self.name}: input '{port.name}' expected {port.type_.__name__}"
                )

    def __repr__(self) -> str:
        return f"<Node {self.name}>"


# Alias Node to BaseNode to guarantee 100% backward compatibility with all existing nodes and tests
Node = BaseNode
