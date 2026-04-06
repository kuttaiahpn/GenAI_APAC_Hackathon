# TaskNinja: Full Lifecycle Milestone Tracker

This checklist provides a complete view of the project tasks, from initial bedrock setup to final integration fixes and deployment. Use this to identify phase-to-phase progress and verify the system's overall integrity.

---

## 🟢 Phase 1: Bedrock (Data & Memory)
- [x] Provision AlloyDB AI cluster (IP: `10.34.0.8`)
- [x] Implement `ingest.py` for document ingestion
- [x] Configure Google Vertex AI `text-embedding-004`
- [/] **Critical Check**: Verify all relational tables are created (Fixed in Phase 4)
  - [x] `Document` & `Embedding` tables
  - [x] `Task` & `Session` tables (Initial omission → Resolved)

## 🔵 Phase 2: Tooling & MCP Gateway (The "Hands")
- [x] Build FastAPI-based MCP Connector service
- [x] Define strictly-typed Pydantic schemas in `tools.py`
- [x] Implement dual-ingress (MCP SSE + REST) in `mcp_server.py`
- [x] Containerize and deploy to Google Cloud Run
- [x] Map tool functions: `RAGQuery`, `MeetingSchedule`, `TaskCreate`, `Notify`

## 🟡 Phase 3: LangGraph Swarm & Intelligence (The "Brain")
- [x] Configure `AgentState` TypedDict for centralized context
- [x] Build and test specialized Sub-Agent nodes (`RetrieverNode`, `SchedulerNode`, etc.)
- [x] Implement Master Orchestrator with Gemini 2.5 Pro
- [x] Deploy Pub/Sub Telemetry hook (`taskninja-events` topic)
- [/] **Consistency Check**: Ensure LLM outputs valid JSON schemas (Resolved in Fix Phase)

## 🔴 Phase 4: Frontend Command Center & Integration (The "Face")
- [x] Build Streamlit UI based on `frontend_ui_spec.md`
- [x] Rebuild UI: Transition from Popover-only to Multi-Page Sidebar layout
- [x] Implement **Pulse Trace Expander** for real-time monitoring
- [x] Integrate Frontend with Cloud Run backend via OIDC/REST

## 🛠️ Global Integration & Optimization (The "Final Polish")
- [x] **SSE Deadlock Fix**: Switch internal sub-agent calls to REST endpoints
- [x] **Graph Routing Fix**: Ensure `ResponseNode` is always the terminal path
- [x] **Prompt Engineering**: Simplified system prompts for zero-fail JSON parsing
- [x] **Environment Audit**: Secure all DB credentials in Secret Manager
- [x] Final End-to-End Stress Test (Scenario: "Complex Project Sync")

---

## 🚀 Final Handover
- [ ] Record Final Demo Video
- [ ] Generate Comprehensive README
- [ ] Project Submission to Hackathon Portal
