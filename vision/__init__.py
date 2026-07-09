"""L3 — Vision engines package.

Importing this package registers the S0-S3 vision nodes into the node
catalog so they can be referenced by name in a graph spec.
"""
from vision import nodes  # noqa: F401  (import for registration side effect)
from vision.types import (
    Detection,
    Detections,
    Frame,
    NormalizedFrame,
    Incident,
    VerifiedObjects,
)

__all__ = [
    "Detection",
    "Detections",
    "Frame",
    "NormalizedFrame",
    "Incident",
    "VerifiedObjects",
]
