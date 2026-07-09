"""L1 — Node abstraction.

A Node is a pure, declared transform with a name, typed input schema,
typed output schema, and config. Nodes are the atomic units of the NexusGuard
graph and self-register into the node catalog.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


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


class Node(ABC):
    """Base class for every NexusGuard node.

    Subclasses declare their name, input ports, and output ports, and
    implement `run`. The graph engine uses the declared ports to validate
    edges before execution.
    """

    name: str = "node"
    inputs: tuple[PortSpec, ...] = ()
    outputs: tuple[PortSpec, ...] = ()

    def __init__(self, config: dict[str, Any] | None = None, **kwargs: Any) -> None:
        self.config = config if config is not None else kwargs

    @abstractmethod
    def run(self, inputs: dict[str, Any]) -> NodeResult:
        """Execute the node on validated inputs and return outputs."""
        raise NotImplementedError

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
