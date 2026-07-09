"""L5 — Agent (reasoning) layer public API.

Exposes the narrow surface the L4 server depends on:
  * `Adjudicator` / `Decision` — the orchestration entry point,
  * `ReasoningProvider` — the swappable backend protocol,
  * `PluggableLlmProvider` / `FreeLlmApiConfig` — the default reasoner backend,
  * `heuristic_risk` — the dependency-free fallback scorer.
"""
from __future__ import annotations

from reasoning.adjudicator import Adjudicator, Decision
from reasoning.provider import ReasoningProvider, heuristic_risk
from reasoning.llm_client import FreeLlmApiConfig, PluggableLlmProvider
from reasoning.safety import enforce_output, looks_like_injection, sanitize_text

__all__ = [
  "Adjudicator",
  "Decision",
  "ReasoningProvider",
  "heuristic_risk",
  "FreeLlmApiConfig",
  "PluggableLlmProvider",
  "enforce_output",
  "looks_like_injection",
  "sanitize_text",
]
