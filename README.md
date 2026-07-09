<div align="center">

# ⚡ NexusGuard

### Asynchronous Event-Driven Intelligent Vision Platform

**A real-time computer-vision platform driven by a directed acyclic graph (DAG) of nodes, featuring a pluggable agentic reasoning engine for scene understanding.**

*Turn any camera stream into risk-scored, human-readable, auditable incidents — through a robust pipeline of inspectable operations.*

<br/>

[![License](https://img.shields.io/badge/license-Apache_2.0-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.10_%7C_3.11_%7C_3.12-3776AB?logo=python&logoColor=white)](./pyproject.toml)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)](./api)
[![Status](https://img.shields.io/badge/status-active-brightgreen.svg)](#-project-status)

</div>

---

## 📍 Table of Contents

- [What is NexusGuard?](#-what-is-nexusguard)
- [System Architecture](#-system-architecture)
- [The Pipeline (Ingest to Broadcast)](#-the-pipeline)
- [The Agentic Reasoning Engine](#-the-agentic-reasoning-engine)
- [Features](#-features)
- [Quickstart](#-quickstart)
- [Repository Layout](#-repository-layout)
- [Project Status](#-project-status)
- [License & Attribution](#-license--attribution)

---

## 🧭 What is NexusGuard?

NexusGuard is an **asynchronous, event-driven** computer vision framework. It processes live camera feeds through a validated directed acyclic graph (DAG) of interchangeable nodes: `Ingest → Process → Analyze → Verify → Synthesize → Broadcast`. 

Unlike traditional monolithic architectures that load enormous end-to-end models, NexusGuard orchestrates a pipeline of small, highly-specialized stages. The perception layer handles pixel-perfect object detection locally, while a dedicated, swappable Agentic Reasoning Engine provides high-level scene understanding and anomaly detection. 

NexusGuard outputs a bounded, evidence-carrying `Incident` at the end of every evaluation cycle.

---

## 🏗️ System Architecture

NexusGuard is partitioned into a layered architecture for maximum extensibility and testability:

```mermaid
mindmap
  root((NexusGuard))
    Runtime
      Nodes
      Catalog
      State
    Execution
      Graph Builder
      DAG Validator
      Router
    Vision
      Ingest (Cameras)
      Processing
      Detection & Tracking
    API Layer
      FastAPI
      WebSockets
      Metrics (Prometheus)
    Reasoning
      LLM Provider Client
      Pydantic Schemas
      Safety Guardrails
```

The system is rigorously validated before execution. Every node connection is checked against strongly-typed input/output schemas. If a pipeline is misconfigured, it fails at initialization—never mid-stream during critical camera analysis.

---

## 🔁 The Pipeline

A single pass over a camera frame involves fast local perception and asynchronous deliberation.

| Stage | Node | Responsibility |
|:-----:|-------|-----------|
| **Ingest** | `CaptureNode` | Ring buffers for frame polling, monotonic indexing, async capture from RTSP/USB. |
| **Process** | `CleanNode` | Geometry normalization, color space correction for downstream inference. |
| **Analyze** | `DetectNode` | Pluggable interface for object detection (e.g., YOLO) and tracking abstractions (ByteTrack). |
| **Verify** | `ValidateNode` | Drops low-confidence/malformed bounding boxes, reporting telemetry on dropped items. |
| **Synthesize** | `Adjudicator` | Asynchronous reasoning via LLM integration; synthesizes detections into a risk-scored `Incident`. |
| **Broadcast** | `Router` | Emits the `Incident` to a SQLite database, structured logs, and over WebSockets to dashboards. |

---

## 🧠 The Agentic Reasoning Engine

The core innovation in NexusGuard is its separation of *fast perception* and *slow deliberation*. 

NexusGuard employs a swappable `PluggableLlmProvider` to synthesize validated tracking data into actionable insights. Through structured prompt templates and Pydantic schema validation, the agentic layer assigns a unified risk score (0.0 to 1.0) and generates human-readable incident summaries. 

The reasoning engine implements memory, Tenacity-based retry logic, and fallback heuristic adjudication if the LLM backend is unavailable, ensuring high availability in edge deployments.

---

## 🚀 Features

NexusGuard includes several production-grade ML infrastructure features:

- **Asynchronous Pipeline Execution**: Non-blocking I/O operations for frame capture and database persistence.
- **Configurable Workflows**: Declarative YAML-based graph routing.
- **Event Bus & Storage**: SQLite-backed incident persistence.
- **Telemetry**: Prometheus metrics endpoint (`/metrics`) and structured JSON logging.
- **Pluggable Architecture**: Easily swap in new tracking algorithms or detection models.
- **Live Dashboard**: Web UI with live WebSocket stream, timeline filters, and latency/FPS telemetry.
- **Safety Guardrails**: Prompt injection defense and bounded output clamping.

---

## 🛠️ Quickstart

```bash
# 1. Configure your environment
cp .env.example .env

# 2. Run with Docker Compose
docker compose up -d

# 3. Validate your node graph locally
python scripts/graph_validator.py

# 4. Open the interactive dashboard
open http://localhost:5173
```

---

## 📂 Repository Layout

```text
nexusguard/
├─ runtime/     # Core node abstraction, DAG validation, and router
├─ vision/      # Computer vision nodes: ingest, process, analyze, verify
├─ reasoning/   # Agentic reasoning engine, memory, adjudicator, safety
├─ api/         # FastAPI, WebSockets, Prometheus metrics, SQLite models
├─ ui/          # Dashboard frontend, live WebSocket streaming, timeline
├─ config/      # Declarative YAML workflow and system settings
├─ scripts/     # Utility scripts (e.g. graph_validator.py)
├─ tests/       # Pytest unit tests for all components
└─ README.md
```

---

## 📊 Project Status

NexusGuard is actively maintained as an ML Systems reference architecture. It demonstrates patterns for building reliable, observable, and modular AI infrastructure. 

---

## 📜 License & Attribution

NexusGuard is licensed under the **[Apache-2.0](./LICENSE)** license. 

*Attribution: This project was originally inspired by the architectural concepts found in roboflow/inference, pysource-com/VisoNode, SharpAI/DeepCamera, and GetStream/Vision-Agents. It has been extensively reimagined and independently implemented to serve as a robust ML infrastructure reference project.*
