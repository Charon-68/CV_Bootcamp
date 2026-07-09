"""L4 — FastAPI application factory.

`create_app()` builds the ASGI app, selects a reasoning backend from the
environment, and injects a single shared `Adjudicator` into the router via a 
dependency override.
"""
from __future__ import annotations

import os

from fastapi import FastAPI

from reasoning import Adjudicator, PluggableLlmProvider
from api.routes import get_adjudicator, router
from api.metrics import router as metrics_router


def build_adjudicator() -> Adjudicator:
  """Wire the reasoning backend based on environment configuration."""
  if os.getenv("FREELLMAPI_BASE_URL"):
    return Adjudicator(provider=PluggableLlmProvider())
  return Adjudicator(provider=None)


def create_app() -> FastAPI:
  app = FastAPI(
    title="NexusGuard",
    version="0.2.0",
    description="Asynchronous event-driven intelligent vision platform API.",
  )

  adjudicator = build_adjudicator()
  app.dependency_overrides[get_adjudicator] = lambda: adjudicator
  
  app.include_router(router, prefix="/v1")
  app.include_router(metrics_router)

  @app.get("/", tags=["ops"])
  def root() -> dict:
    return {"service": "nexusguard", "docs": "/docs", "api": "/v1", "metrics": "/metrics"}

  return app


app = create_app()
