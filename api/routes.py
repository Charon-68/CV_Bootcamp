"""L4 — HTTP routes.

The router validates input via pydantic, converts to the L3 domain types, 
delegates reasoning to the L5 `Adjudicator`, persists to the SQLite database, 
and broadcasts the event via WebSockets.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from reasoning import Adjudicator
from api.schemas import (
  AnalyzeRequest,
  AnalyzeResponse,
  HealthResponse,
  IncidentOut,
)
from api.database import db
from api.metrics import metrics_store
from api.websocket import manager

router = APIRouter()


def get_adjudicator() -> Adjudicator:
  """Dependency placeholder; overridden at app startup with a wired instance."""
  raise RuntimeError("Adjudicator dependency is not configured")


@router.get("/health", response_model=HealthResponse, tags=["ops"])
def health(adjudicator: Adjudicator = Depends(get_adjudicator)) -> HealthResponse:
  backend = "heuristic" if adjudicator._provider is None else "reasoner"
  return HealthResponse(status="ok", reasoning_backend=backend)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
  await manager.connect(websocket)
  try:
    while True:
      # Keep connection alive
      await websocket.receive_text()
  except WebSocketDisconnect:
    manager.disconnect(websocket)


@router.post("/analyze", response_model=AnalyzeResponse, tags=["pipeline"])
async def analyze(
  request: AnalyzeRequest,
  adjudicator: Adjudicator = Depends(get_adjudicator),
) -> AnalyzeResponse:
  
  metrics_store.record_frame()
  
  # Run reasoning block
  decision = adjudicator.decide(request.to_domain(), request.context())
  event = decision.event
  
  metrics_store.record_incident(event.risk)
  db.insert_incident(event)
  
  out_event = IncidentOut(
    frame_index=getattr(event, "frame_index", request.frame_index),
    risk=event.risk,
    label=event.label,
    summary=event.summary,
  )
  
  # Broadcast event asynchronously to all connected websocket clients
  await manager.broadcast_incident(out_event.model_dump())
  
  return AnalyzeResponse(
    event=out_event,
    sanitized=decision.sanitized,
    used_fallback=decision.used_fallback,
  )
