# TaskNinja: Master UAT Execution Plan

This document serves as the "Proof of Testing" for the TaskNinja Hackathon Submission. Each scenario is designed to showcase the **Brain** (Orchestrator), **Hands** (Tools), and **Bedrock** (AlloyDB) in a "Concordant" real-world workflow.

---

## 🔐 Login Screen
- **[UAT-1.1] Auth Entrance (Mandatory)**
  - Action: Log in as `judge@hackathon.dev`.
  - Result: Dashboard initializes; "System Pulse" turns green (**🟢 System Pulse: Active**).
- **[UAT-1.2] ID Creation (Mandatory)**
  - Action: Note the `Thread ID` in the sidebar.
  - Result: Thread ID is unique and persistent across the session.
- **[UAT-1.3] Logout Cycle (Good-to-Have)**
  - Action: Click "Logout."
  - Result: App state clears; user returns to secure auth gate.

---

## 🏠 Dashboard
- **[UAT-2.1] Live Stats Sync (Mandatory)**
  - Action: Compare "Live Docs" count in UI to file list in GCS.
  - Result: Numbers match (proving AlloyDB real-time metadata fetch).
- **[UAT-2.2] Notification Toast (Mandatory)**
  - Action: Generate a scheduled meeting (in Chat).
  - Result: UI Toast appears in Dashboard sidebar within 3s.
- **[UAT-2.3] Infrastructure Glance (Good-to-Have)**
  - Action: Verify "Backend" URL tooltip matches current Gateway IP.
  - Result: Transparent view of Cloud-Native deployment for judges.

---

## 💬 Swarm Chat (The "Brain" & "Hands")
- **[UAT-3.1] RAG Deep Query (Mandatory)**
  - Action: Ask: "What are the core objectives and rules of the hackathon?"
  - Result: `RetrieverNode` pulls from `Hackathon.txt`; response cites specific sections.
- **[UAT-3.2] Multi-Step Scheduler (Mandatory)**
  - Action: Ask: "Schedule a sync for tomorrow at 4 PM to review the judges' criteria."
  - Result: `Orchestrator -> SchedulerNode` flow triggered; meeting saved to AlloyDB.
- **[UAT-3.3] Pulse Trace Visualization (Good-to-Have)**
  - Action: View the "🧠 Swarm Trace" under the chat bubble.
  - Result: Visual proof of every sub-agent invoked sequentially.

---

## 📤 Document Vault
- **[UAT-4.1] Batch Ingestion (Mandatory)**
  - Action: Upload 3-5 text/markdown files simultaneously.
  - Result: Multi-file progress bar shows batch status; 100% success balloons.
- **[UAT-4.2] Vector Memory Update (Good-to-Have)**
  - Action: Ingest a new doc, then immediately query it in Chat.
  - Result: Zero-latency RAG—assistant "knows" the new data instantly.

---

## 📋 Task & Calendar Sync
- **[UAT-5.1] Task Queue Persistence (Mandatory)**
  - Action: View "📋 Task Manager" after adding a task in chat.
  - Result: Task appears with `pending` status and "Execution Plan" visibility.
- **[UAT-5.2] Calendar Logic (Mandatory)**
  - Action: View "📅 Calendar."
  - Result: Meeting from [UAT-3.2] is visible with Participants and Start/End times.

---

## 🛡️ Audit Hub (The "Trace")
- **[UAT-6.1] Telemetry Log Proof (Mandatory)**
  - Action: Locate the `Decision ID` for the Chat query in [UAT-3.1].
  - Result: Full trace available (proves 100% observability for judges).
