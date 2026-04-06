# TaskNinja: Project Evolution & Master Walkthrough

This document chronologically details the technical journey of TaskNinja, highlighting the key integration points and how we cross-checked each phase to build a unified multi-agent system.

---

## 🟢 Phase 1: The Bedrock (Data & Memory)
**Objective**: Establish persistent vector memory so Gemini "remembers" project notes.

### What We Built:
- **`ingest.py`**: A custom ingestion engine for 768-D embeddings using Google Vertex AI.
- **AlloyDB AI**: Provisioned the primary memory bank at **`10.34.0.8`**.
- **Bedrock Verification**: Tested PII detection on sensitive notes, ensuring PII flags were correctly stored in the `embeddings` table metadata.

---

## 🔵 Phase 2: Tooling & The MCP Gateway (The "Hands")
**Objective**: Build a universal execution bridge for Gemini.

### What We Built:
- **`mcp_server.py`**: A FastAPI service enabling standardized Model Context Protocol (MCP) access to local and external tools.
- **`tools.py`**: Defined Pydantic-validated functions for RAG querying, scheduling, and task management.
- **Integration Check**: Verified that the MCP gateway could be discovered by external clients via the `/mcp/sse` endpoint.

---

## 🟡 Phase 3: LangGraph Swarm & Intelligence (The "Brain")
**Objective**: Wire the brains for multi-step reasoning and delegation.

### What We Built:
- **Orchestrator Node**: A Gemini 1.5 Pro-powered routing node that generates JSON-based `actions_payload`.
- **Sub-Agent Nodes**: Specialized LangChain nodes (`RetrieverNode`, `SchedulerNode`, `TaskNode`, `NotifyNode`).
- **Telemetry Hook**: Integrated a `TelemetryNode` that emits the final decision traces to GCP Pub/Sub (`taskninja-events`).

---

## 🔴 Phase 4: Integration Turning Point & Frontend Renaissance
**Objective**: Resolve real-world friction and polish the UX.

### The SSE Deadlock Fix (Critical Integration Point)
- **Problem**: During deployment, we discovered that the sub-agents running inside the Cloud Run backend would deadlock when trying to call the SAME service's SSE endpoint (self-referential loop).
- **The "Check & Connection"**: We restructured the `nodes.py` to use a dedicated REST protocol (`/v1/tools/`) for internal agent-to-gateway calls, while maintaining standard MCP SSE for external tool discovery. This ensured 100% reliability in serverless environments.

### The Missing Tables Check
- **Problem**: In Phase 4, we identified that certain tables (like `task` and `session`) were missing from the initial AlloyDB setup, even though Phase 1 had focused on `embeddings`.
- **The "Check & Connection"**: We audited the `alloydb_setup.sql` and updated the `models.py` to ensure all core productivity tables were properly instantiated and mapped via SQLAlchemy.

### The Frontend Rebuild
- **Evolution**: We moved from a simple "Popover Chat" to a **Complete Multi-Page Sidebar Layout**.
- **Why?**: The popover UI was too restricted for managing complex traces. The new UI allows for a full-screen Chat window with integrated **Pulse Trace Expanders** for real-time monitoring of the agentic swarm.

---

## 🚀 Phase 5: Future Road Map

### 1. Multi-modal Integration
- Enable the **`NoteAgent`** to process images of physical whiteboards and ingest them directly into the RAG vector memory using Gemini Pro Vision.

### 2. Proactive Notifications
- Build a persistent cron-based "Nudge Agent" that monitors the `Task` table and triggers the `NotifyNode` via GCP Pub/Sub for upcoming deadlines.

### 3. Cost & Performance Optimization
- Implement an **Intelligence Tiering** system: Use Gemini 2.5 Flash for routine routing and only escalate to Gemini 1.5 Pro for complex orchestration tasks.

### 4. Edge Tooling
- Support for on-device MCP servers, allowing the TaskNinja orchestrator to interact with a user's local terminal or desktop applications securely.
