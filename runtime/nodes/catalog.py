"""L1 — Node catalog/registry."""
from __future__ import annotations

from typing import Callable, TypeVar, Dict, List, Type
from runtime.nodes.node import Node

_REGISTRY: dict[str, type[Node]] = {}
B = TypeVar("B", bound=type[Node])


class NodeRegistry:
    """Registry to manage and instantiate workflow Node classes."""

    @classmethod
    def register(cls, name: str | None = None) -> Callable[[B], B]:
        """Class decorator that registers a Node subclass under `name`."""
        def _decorator(node_cls: B) -> B:
            key = name or getattr(node_cls, "name", None)
            if not key:
                raise ValueError(f"{node_cls.__name__}: node must declare a name")
            if key in _REGISTRY:
                # Allow re-registration for dynamic reloading / plugin replacement
                pass
            _REGISTRY[key] = node_cls
            return node_cls
        return _decorator

    @classmethod
    def get(cls, name: str) -> type[Node]:
        """Return the registered Node class for `name`."""
        try:
            return _REGISTRY[name]
        except KeyError as exc:
            raise KeyError(f"unknown node: {name!r}") from exc

    @classmethod
    def create(cls, name: str, **config: object) -> Node:
        """Instantiate a registered node by name with the given config."""
        return cls.get(name)(**config)

    @classmethod
    def available(cls) -> list[str]:
        """Return the sorted list of registered node names."""
        return sorted(_REGISTRY)


# Expose decorator and helper functions for backward compatibility
register = NodeRegistry.register
get = NodeRegistry.get
create = NodeRegistry.create
available = NodeRegistry.available
