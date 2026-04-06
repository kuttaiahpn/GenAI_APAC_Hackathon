# TaskNinja: Final Implementation Specification

This document serves as the definitive technical reference for the TaskNinja multi-agent productivity assistant, detailing the architecture, data layer, and integration protocols implemented during the hackathon.

---

## 1. System Architecture Overview

TaskNinja is built on a **Zero-Footprint, Utility-First** architecture on Google Cloud. It leverages a decentralized multi-agent swarm orchestrated by LangGraph and Gemini.

### Core Components:
1.  **Orchestrator Swarm (LangGraph)**: The "Brain" utilizing Gemini 1.5 Pro to coordinate specialized sub-agents.
2.  **MCP Gateway (FastAPI)**: The "Hands" implementing the Model Context Protocol (MCP) for tool discovery and execution.
3.  **AlloyDB AI**: The "Memory" providing relational storage and high-performance vector search (pgvector).
4.  **Vertex AI**: The "Cognition" providing embeddings (`text-embedding-004`) and LLM processing.
5.  **Streamlit Control Center**: The "Face" providing a unified command interface and audit observability.

---

## 2. Data Layer & Knowledge (Phase 1)

### AlloyDB AI & Vector Search
- **Relational Tables**: Managed via SQLAlchemy (`models.py`, `database.py`).
  - `Document`: Metadata for ingested project notes.
  - `Embedding`: chunked text and 768-D vectors.
  - `Task`: Persistent state for user actions.
  - `DecisionLog`: Audit trail for agentic reasoning.
- **Ingestion Engine (`ingest.py`)**:
  - Uses `RecursiveCharacterTextSplitter` with 1000-char chunks and 100-char overlap.
  - Generates 768-D embeddings via Google Vertex AI.
  - **PII Detection**: Built-in regex-based keyword detection for tagging sensitive documents.

---

## 3. Tooling & MCP Gateway (Phase 2)

### Universal Tool Discovery
The `mcp_server.py` implements a dual-ingress FastAPI service:
1.  **MCP SSE Protocol**: Event-driven transport on `/mcp/sse` and `/mcp/messages` for official MCP clients.
2.  **REST API**: Explicit endpoints (`/v1/tools/*`) for sub-agent execution, ensuring reliability in serverless environments.

### Tool Definitions (`tools.py`)
- Strictly typed input schemas using **Pydantic**.
- Capabilities: `RAGQuery`, `MeetingSchedule`, `CalendarFetch`, `Notification`, `CreateTask`, `DecisionLog`.

---

## 4. Intelligence & Orchestration (Phase 3)

### LangGraph State Machine
- **Orchestrator Node**: Uses Gemini 1.5 Pro with a deterministic system prompt to generate an `actions_payload`.
- **Sub-Agent Nodes**: Specialized agents (`RetrieverNode`, `SchedulerNode`, `TaskNode`, `NotifyNode`) that execute tools via the MCP Gateway.
- **Telemetry & Tracing**:
  - **`TelemetryNode`**: Emits the final graph state to a GCP Pub/Sub topic (`taskninja-events`).
  - **Audit Trail**: Every request generates a unique `trace_id` for observability.

---

## 5. Integration Protocols & Fixes (Phase 4)

### Critical Fixes Implemented:
1.  **SSE Deadlock Resolution**: Sub-agents now use REST endpoints (`/v1/tools/`) for gateway calls instead of SSE. This avoids the self-referential network deadlock in single-concurrency Cloud Run instances.
2.  **Deterministic Routing**: Fixed `orchestrator.py` logic to ensure every execution path terminates at the `ResponseNode`, providing a final user-visible response even if tools fail.
3.  **JSON Robustness**: Refined system prompts to minimize markdown noise (backticks) in LLM outputs, ensuring 100% JSON parsing reliability.

---

## 6. Frontend Command Center (Phase 4)

### UI Design System
- **Layout**: Multi-page sidebar navigation replacing the previous popover-only chat.
- **Key Views**:
  - **Dashboard**: High-level task cards and status summaries.
  - **Chat**: Persistent context-aware conversation with integrated **Pulse Trace Expander** for real-time agent monitoring.
  - **Audit Logs**: Deep-dive view of all decision IDs and tool outputs.

---

## 7. Deployment Specification

- **Environment**: Google Cloud Run (Containerized via Multi-Stage Dockerfile).
- **VPC Configuration**: Egress via `taskninja-v1` VPC connector for secure AlloyDB (10.34.0.8) access.
- **Scaling**: Concurrency set to 80 to support multi-step agentic loops without latency spikes.
