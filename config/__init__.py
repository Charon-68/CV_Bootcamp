"""Configuration package.

Exposes the env-driven `Settings` object plus the path to the default pipeline
DAG spec so other layers can load runtime config from one place.
"""
from __future__ import annotations

from config.settings import DEFAULT_PIPELINE, REPO_ROOT, Settings, get_settings

__all__ = ["Settings", "get_settings", "DEFAULT_PIPELINE", "REPO_ROOT"]
