# NexusGuard Architecture

> An asynchronous, event-driven intelligent vision platform powered by a pluggable agentic reasoning engine.

This document describes the system architecture and the canonical pipeline, expressed as a directed acyclic graph (DAG) of typed `Node` instances.

---

## 1. Design Principles

- **Node-Graph First**: Every unit of work is a `Node` with strongly-typed inputs and outputs. Pipelines are DAGs, validated before execution to prevent runtime failures.
- **Swappable Reasoning Engine**: The AI layer is an interface, not a tightly coupled vendor. The LLM backend is abstracted and supports retry policies, memory, and Pydantic validation.
- **Event-Driven & Asynchronous**: The system embraces asynchronous patterns for I/O operations. Incident events are broadcast over WebSockets and persisted to a SQLite/Postgres database.
- **Observability**: Prometheus metrics, structured JSON logs, and health endpoints are integrated at the API layer.
- **Human-Readable Output**: The system emits risk-scored, actionable `Incident` events rather than just bounding box coordinates.

---

## 2. Component Layers

| Module | Responsibility | Key Components |
|-------|----------------|-------------|
| `runtime/` | Core abstraction | Node contract, Catalog, DAG validator, Graph execution router |
| `vision/` | Visual perception | Ingest, Process, Analyze, Track, Verify nodes |
| `api/` | Serving & Telemetry | FastAPI, SQLite DB, Prometheus, WebSockets, Rate limiting |
| `reasoning/` | Intelligence | LLM provider client, Adjudicator, Memory, Schemas, Safety |
| `ui/` | Dashboard | React Flow integration, WebSocket feed, FPS/Latency graphs |

### `runtime/`
Defines the atomic `Node` interface. Nodes self-register into a `Catalog`. The graph engine compiles the DAG, checks for cycles, validates type schemas across ports, and handles the execution routing.

### `vision/`
Contains concrete nodes that interact with hardware (cameras/RTSP) and computer vision models. By abstracting detection into nodes, heavy libraries like YOLO or ByteTrack remain isolated from the core logic.

### `api/`
The API layer exposes REST endpoints, health checks, metrics, and manages the database session. It also maintains active WebSocket connections to push live `Incident` events to the UI.

### `reasoning/`
The agentic layer. It takes `VerifiedObjects` and context from the pipeline, sanitizes it, and queries the LLM provider. It enforces a strict output contract (`Incident`) with clamping on risk scores and constraints on summaries.

---

## 3. The Canonical Pipeline

The standard processing flow is configured via `config/workflow.yaml`.

```
[Ingest] -> [Process] -> [Analyze] -> [Verify] -> [Synthesize] -> [Broadcast]
```

- **Ingest (`CaptureNode`)**: Asynchronously pulls frames from RTSP streams, maintaining monotonic indexes.
- **Process (`CleanNode`)**: Geometry/color normalizations.
- **Analyze (`DetectNode`)**: Generates initial bounding boxes and optionally tracking IDs.
- **Verify (`ValidateNode`)**: Applies thresholds and physical geometry constraints.
- **Synthesize (`Adjudicator`)**: The Reasoning Engine determines the context and risk of the frame.
- **Broadcast (`Router`)**: Persists the event to the database and streams to connected WebSocket clients.

---

## 4. Reasoning Engine Contract

The reasoning engine exposes a simple protocol to the pipeline:

```python
class PluggableLlmProvider(Protocol):
    def adjudicate(self, detections: VerifiedObjects, context: dict) -> Incident: ...
```

The system uses Pydantic schemas under the hood to force the LLM to return valid JSON matching the `Incident` schema. Fallback heuristics automatically trigger if the LLM provider times out or fails, guaranteeing uptime.

---

## 5. Deployment Topology

```text
            +-------------+        +-----------------+
  camera -->|  api (FastAPI)|<------>|  LLM Provider   |
            +------+------+        +-----------------+
                   |
         +---------+---------+
         |                   |
   +-----v-----+       +-----v-----+
   |  SQLite   |       |    UI     |
   | (Events)  |       | Dashboard |
   +-----------+       +-----------+
         |
   +-----v----------------+
   | prometheus metrics   |
   +----------------------+
```

All services are orchestrated via `docker-compose.yml` for simplified deployment and reproducible environments.
