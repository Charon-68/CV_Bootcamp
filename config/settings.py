"""Application settings loaded from the environment.

A single, dependency-light settings object read once at startup. Values map
directly onto the `.env.example` keys so local, docker, and CI environments
share one contract. No secrets are hard-coded; everything falls back to safe
defaults so the app boots even with an empty environment.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PIPELINE = REPO_ROOT / "config" / "workflow.yaml"


def _as_bool(value: str | None, default: bool = False) -> bool:
  if value is None:
    return default
  return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
  """Immutable runtime configuration for the NexusGuard service."""

  host: str = "0.0.0.0"
  port: int = 8000
  log_level: str = "info"
  pipeline_path: str = str(DEFAULT_PIPELINE)

  # L5 reasoning backend (empty base_url => heuristic fallback).
  reasoner_base_url: str = ""
  reasoner_model: str = "auto"

  # Vision defaults applied when a node omits them.
  min_confidence: float = 0.25
  frame_size: int = 640

  @classmethod
  def from_env(cls) -> "Settings":
    return cls(
      host=os.getenv("NexusGuard_HOST", "0.0.0.0"),
      port=int(os.getenv("NexusGuard_PORT", "8000")),
      log_level=os.getenv("NexusGuard_LOG_LEVEL", "info"),
      pipeline_path=os.getenv("NexusGuard_PIPELINE", str(DEFAULT_PIPELINE)),
      reasoner_base_url=os.getenv("FREELLMAPI_BASE_URL", "").rstrip("/"),
      reasoner_model=os.getenv("FREELLMAPI_MODEL", "auto"),
      min_confidence=float(os.getenv("NexusGuard_MIN_CONFIDENCE", "0.25")),
      frame_size=int(os.getenv("NexusGuard_FRAME_SIZE", "640")),
    )

  @property
  def reasoning_backend(self) -> str:
    return "reasoner" if self.reasoner_base_url else "heuristic"


def get_settings() -> Settings:
  """Return settings built from the current environment."""
  return Settings.from_env()
