"""L1 — Node catalog.

Nodes register themselves by name so graphs can be built by reference
(e.g. from a declarative spec) without importing concrete classes directly.
"""
from __future__ import annotations

from typing import Callable, TypeVar

from runtime.nodes.node import Node

_REGISTRY: dict[str, type[Node]] = {}

B = TypeVar("B", bound=type[Node])


def register(name: str | None = None) -> Callable[[B], B]:
    """Class decorator that registers a Node subclass under `name`.

    If `name` is omitted, the node's `name` attribute is used.
    """

    def _decorator(cls: B) -> B:
        key = name or getattr(cls, "name", None)
        if not key:
            raise ValueError(f"{cls.__name__}: node must declare a name")
        if key in _REGISTRY:
            raise ValueError(f"duplicate node name: {key!r}")
        _REGISTRY[key] = cls
        return cls

    return _decorator


def get(name: str) -> type[Node]:
    """Return the registered Node class for `name`."""
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"unknown node: {name!r}") from exc


def create(name: str, **config: object) -> Node:
    """Instantiate a registered node by name with the given config."""
    return get(name)(**config)


def available() -> list[str]:
    """Return the sorted list of registered node names."""
    return sorted(_REGISTRY)
