# TaskNinja UI Specification (Streamlit Implementation)

## 1. Authentication / Landing Layer
- [cite_start]**Layout:** Two-column split[cite: 220]. [cite_start]Left column for Hero/Value Prop[cite: 220]; [cite_start]Right column for Authentication[cite: 223].
- **Components:** - `st.title("TaskNinja")`
  - `st.markdown("Context-aware multi-agent task manager")`
  - [cite_start]`st.button("Demo Login")` to instantly bypass OAuth for hackathon judges[cite: 227].

## 2. Main Dashboard Layout
- [cite_start]**Sidebar (Navigation):** Menu options for Chat, Tasks, Calendar, and Audit[cite: 230]. Include user avatar and a badge displaying current `model_used`.

## 3. Core Views
### View A: Chat Interface (Primary)
- [cite_start]**Main Pane:** `st.chat_message` stream for User and Agent bubbles[cite: 231]. 
- [cite_start]**Agent Bubbles:** MUST include an `st.expander` titled "Actions & Decision Data" to show the raw JSON, `decision_id`, and `audit_id` for technical transparency[cite: 232, 241].
- **Sidebar Context Pane:** Use `st.sidebar` to display:
  - Current `session_summary`.
  - [cite_start]Top 3 RAG document hits with highlights[cite: 234].

### View B: Task Management
- [cite_start]**Main Pane:** Filterable table/dataframe showing Task Status (New, Ongoing, Completed)[cite: 235].
- [cite_start]**Row Expansion:** Clicking a task reveals `execution_report`, `idempotency_key`, and a "Replay Task" button[cite: 236, 243].

### View C: Audit & Observability
- [cite_start]**Main Pane:** A searchable dataframe rendering the `audit_logs` table[cite: 239].
- [cite_start]**Details:** Expandable rows showing the full JSON payload of MCP tool requests and responses[cite: 240].