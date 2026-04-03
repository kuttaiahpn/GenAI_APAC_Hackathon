# TaskNinja UI Specification (Streamlit Implementation)

## 1. Authentication / Landing Layer
- [cite_start]**Layout:** Two-column split[cite: 220]. [cite_start]Left column for Hero/Value Prop[cite: 220]; [cite_start]Right column for Authentication[cite: 223].
- **Components:** - `st.title("TaskNinja")`
  - `st.markdown("Context-aware multi-agent Productivity Assistant Task Manager")`
  - [cite_start]`st.button("Demo Login")` to instantly bypass OAuth for hackathon judges[cite: 227].

## 2. Main Dashboard Layout
- [cite_start]**Sidebar (Navigation):** Menu options for Chat, Tasks, Calendar, and Audit[cite: 230]. Include user avatar and a badge displaying current `model_used`. Add cards in the screen to show Today's Tasks, Upcoming Tasks, and Completed Tasks.
On all screens (Main Dashboard, View A, B, C, D), the top bar should have the TaskNinja logo, the current model used, and a button to switch models. Also the chat icon should hover at the bottom right corner which user can click to pop up the chat interface bar that can be collapsed after use. The current page remains in the background

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

### View C: Calendar
- [cite_start]**Main Pane:** A standard calendar view showing the tasks in a calendar format.
- [cite_start]**Details:** Button to add new tasks and view task details and edit them.

### View D: Audit & Observability
- [cite_start]**Main Pane:** A searchable dataframe rendering the `audit_logs` table[cite: 239].
- [cite_start]**Details:** Expandable rows showing the full JSON payload of MCP tool requests and responses[cite: 240].