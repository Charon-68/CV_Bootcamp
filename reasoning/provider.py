"""L5 — Reasoning provider interface.

The reasoning core is accessed through a single, narrow interface so the
LLM backend can be swapped without touching the graph. The default
implementation targets `reasoner` (a free-tier gateway), but any object
satisfying `ReasoningProvider` can be injected.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from vision.types import Incident, VerifiedObjects


@runtime_checkable
class ReasoningProvider(Protocol):
    """Adjudicate validated detections into a risk-scored event."""

    def adjudicate(
        self, detections: VerifiedObjects, context: dict
    ) -> Incident: ...


def heuristic_risk(detections: VerifiedObjects) -> float:
    """A dependency-free fallback risk score in [0, 1].

    Used when no LLM backend is configured so the pipeline still produces
    a meaningful, monotonic signal (more/high-confidence detections =>
    higher risk).
    """
    if not detections.items:
        return 0.0
    top = max(d.confidence for d in detections.items)
    count_factor = min(len(detections.items) / 5.0, 1.0)
    return round(min(0.5 * top + 0.5 * count_factor, 1.0), 3)
