import streamlit as st
import requests
import uuid
import time
import os
import json
from datetime import datetime, timedelta

# ─── Page Config (MUST be first Streamlit call) ───
st.set_page_config(
    page_title="TaskNinja | Command Center",
    page_icon="🥷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Global CSS Injection ───
st.markdown("""
<style>
    /* Hide default Streamlit chrome */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Top bar */
    .tn-topbar {
        display: flex; justify-content: space-between; align-items: center;
        background: linear-gradient(135deg, #1e1b4b, #312e81);
        padding: 14px 28px; border-radius: 12px; margin-bottom: 20px;
        border: 1px solid #4338ca;
    }
    .tn-topbar-title {
        font-size: 24px; font-weight: 800; color: #e0e7ff;
        display: flex; align-items: center; gap: 10px;
    }
    .tn-topbar-title span { font-size: 13px; font-weight: 400; color: #a5b4fc; }
    .tn-badge {
        background: #7c3aed; color: white; padding: 5px 14px;
        border-radius: 20px; font-size: 12px; font-weight: 700;
    }
    
    /* Login page */
    .login-hero { text-align: center; padding: 60px 20px; }
    .login-hero h1 { font-size: 52px; margin-bottom: 8px; }
    .login-hero p { font-size: 18px; color: #a5b4fc; margin-bottom: 30px; }
    
    /* Metric cards */
    .metric-card {
        background: #1e1b4b; border: 1px solid #3730a3; border-radius: 12px;
        padding: 20px; text-align: center;
    }
    .metric-card h3 { color: #a5b4fc; font-size: 14px; margin: 0 0 8px 0; }
    .metric-card .num { font-size: 36px; font-weight: 800; color: #e0e7ff; }
    
    /* Chat bubbles */
    .stChatMessage { border-radius: 12px !important; }
    
    /* Sidebar profile section */
    .profile-section {
        display: flex; align-items: center; gap: 12px;
        padding: 12px; background: #1e1b4b; border-radius: 10px;
        margin-bottom: 16px; border: 1px solid #3730a3;
    }
    .profile-avatar {
        width: 42px; height: 42px; border-radius: 50%;
        background: #7c3aed; display: flex; align-items: center;
        justify-content: center; font-size: 20px; color: white;
    }
    .profile-info { color: #c7d2fe; font-size: 13px; }
    .profile-info strong { color: #e0e7ff; font-size: 14px; display: block; }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ───
defaults = {
    "authenticated": False,
    "thread_id": str(uuid.uuid4()),
    "messages": [],
    "current_page": "Dashboard",
    "tasks": [
        {"id": 1, "title": "Configure Service Accounts", "status": "New", "due": "Today", "report": "Pending execution"},
        {"id": 2, "title": "Pitch Deck Formatting", "status": "Ongoing", "due": "Today", "report": "Slides 1-5 completed"},
        {"id": 3, "title": "Security Review GCP", "status": "New", "due": "Tomorrow", "report": "Awaiting assignment"},
        {"id": 4, "title": "Setup Vertex Embeddings", "status": "Completed", "due": "Yesterday", "report": "768-D vectors stored"},
        {"id": 5, "title": "MCP Gateway Deployment", "status": "Completed", "due": "Yesterday", "report": "Cloud Run active"},
    ]
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

API_KEY = os.getenv("API_KEY", "hackathon_default_key")
BACKEND_URL = os.getenv("BACKEND_URL", "https://taskninja-mcp-gateway-836906162288.us-central1.run.app")

# ═══════════════════════════════════════════════════════════════
# LOGIN / LANDING PAGE
# ═══════════════════════════════════════════════════════════════
if not st.session_state.authenticated:
    col_left, col_right = st.columns([3, 2], gap="large")
    
    with col_left:
        st.markdown("""
        <div class="login-hero">
            <h1>🥷 TaskNinja</h1>
            <p>Context-Aware Multi-Agent Productivity Assistant</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("##### Key Features")
        feat1, feat2, feat3 = st.columns(3)
        with feat1:
            with st.container(border=True):
                st.markdown("🧠 **Multi-Agent AI**\n\nLangGraph swarm with specialized sub-agents")
        with feat2:
            with st.container(border=True):
                st.markdown("🔌 **MCP Protocol**\n\nUniversal tool discovery via Model Context Protocol")
        with feat3:
            with st.container(border=True):
                st.markdown("🛡️ **Full Observability**\n\nDecision tracing, audit logs, PII detection")
    
    with col_right:
        st.markdown("###")
        st.markdown("###")
        with st.container(border=True):
            st.markdown("### 🔐 Authenticate")
            st.text_input("Email", value="judge@hackathon.dev", disabled=True)
            st.text_input("Password", type="password", value="••••••••", disabled=True)
            if st.button("🚀 Demo Login", use_container_width=True, type="primary"):
                st.session_state.authenticated = True
                st.rerun()
            st.caption("Demo mode — bypasses OAuth for hackathon judges")
    st.stop()

# ═══════════════════════════════════════════════════════════════
# AUTHENTICATED APP LAYOUT
# ═══════════════════════════════════════════════════════════════

# ─── Top Bar ───
st.markdown("""
<div class="tn-topbar">
    <div class="tn-topbar-title">🥷 TaskNinja <span>Command Center v1.0</span></div>
    <div style="display:flex; gap:12px; align-items:center;">
        <span class="tn-badge">🤖 gemini-2.5-flash</span>
        <span class="tn-badge" style="background:#059669;">● MCP Online</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ───
with st.sidebar:
    st.markdown("""
    <div class="profile-section">
        <div class="profile-avatar">👤</div>
        <div class="profile-info">
            <strong>Hackathon Judge</strong>
            judge@hackathon.dev
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    page = st.radio(
        "Navigation", 
        ["Dashboard", "💬 Chat", "📋 Tasks", "📅 Calendar", "🛡️ Audit"],
        label_visibility="collapsed"
    )
    st.session_state.current_page = page
    
    st.markdown("---")
    st.caption(f"Session: `{st.session_state.thread_id[:12]}`")
    if st.button("🔄 New Session"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
    if st.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.rerun()

# ═══════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════
if page == "Dashboard":
    st.markdown("### 🏠 System Dashboard")
    
    # Metrics row
    m1, m2, m3, m4 = st.columns(4)
    tasks = st.session_state.tasks
    with m1:
        st.markdown(f'<div class="metric-card"><h3>Today\'s Tasks</h3><div class="num">{sum(1 for t in tasks if t["due"]=="Today")}</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card"><h3>Upcoming</h3><div class="num">{sum(1 for t in tasks if t["due"]=="Tomorrow")}</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-card"><h3>Completed</h3><div class="num">{sum(1 for t in tasks if t["status"]=="Completed")}</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown('<div class="metric-card"><h3>Agents Active</h3><div class="num">4</div></div>', unsafe_allow_html=True)
    
    st.markdown("###")
    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown("#### 📅 Today's Focus")
            for t in tasks:
                if t["due"] == "Today":
                    icon = "🟡" if t["status"] == "Ongoing" else "🔵"
                    st.markdown(f"{icon} **{t['title']}** — _{t['status']}_")
    with col_b:
        with st.container(border=True):
            st.markdown("#### ✅ Recently Completed")
            for t in tasks:
                if t["status"] == "Completed":
                    st.markdown(f"✔️ ~~{t['title']}~~")

# ═══════════════════════════════════════════════════════════════
# PAGE: CHAT (The core demo page)
# ═══════════════════════════════════════════════════════════════
elif page == "💬 Chat":
    st.markdown("### 💬 AI Swarm Terminal")
    
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("metadata"):
                with st.expander("🔍 View Agent Trace — Judge's Toolkit"):
                    st.json(msg["metadata"], expanded=True)

    # Chat input at page root level — this is the correct placement
    if user_query := st.chat_input("Ask TaskNinja to schedule, search, create tasks..."):
        # Append user message and display immediately
        st.session_state.messages.append({"role": "user", "content": user_query})
        
        with st.chat_message("user"):
            st.markdown(user_query)
        
        # Process with the swarm
        with st.chat_message("assistant"):
            with st.status("🥷 TaskNinja Swarm Activating...", expanded=True) as status:
                st.write("🔗 Connecting to MCP Gateway...")
                
                try:
                    start_time = time.time()
                    
                    st.write("🧠 Master Orchestrator analyzing intent...")
                    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
                    payload = {"query": user_query, "thread_id": st.session_state.thread_id}
                    
                    st.write("⚡ Dispatching to Sub-Agents via MCP SSE...")
                    response = requests.post(
                        f"{BACKEND_URL}/v1/orchestrate",
                        json=payload,
                        headers=headers,
                        timeout=120
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    latency = time.time() - start_time
                    st.write(f"📊 Telemetry published to Pub/Sub")
                    status.update(label=f"✅ Swarm Complete ({latency:.1f}s)", state="complete", expanded=False)
                    
                    final_text = data.get("response", "The swarm completed but returned no text.")
                    meta = data.get("metadata", {})
                    meta["latency_seconds"] = round(latency, 2)
                    
                    st.markdown(final_text)
                    
                    with st.expander("🔍 View Agent Trace — Judge's Toolkit"):
                        st.json(meta, expanded=True)
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": final_text,
                        "metadata": meta
                    })
                    
                except requests.exceptions.Timeout:
                    status.update(label="⏳ Request Timed Out", state="error")
                    st.error("The swarm took too long to respond. The MCP gateway may be cold-starting.")
                except requests.exceptions.RequestException as e:
                    status.update(label="❌ Connection Failed", state="error")
                    st.error(f"Could not reach the MCP Gateway: {e}")

# ═══════════════════════════════════════════════════════════════
# PAGE: TASKS
# ═══════════════════════════════════════════════════════════════
elif page == "📋 Tasks":
    st.markdown("### 📋 Task Management")
    
    filter_col, add_col = st.columns([3, 1])
    with filter_col:
        status_filter = st.selectbox("Filter by Status", ["All", "New", "Ongoing", "Completed"])
    with add_col:
        st.markdown("###")
        if st.button("➕ Add Task", use_container_width=True):
            new_id = max(t["id"] for t in st.session_state.tasks) + 1
            st.session_state.tasks.append({
                "id": new_id,
                "title": f"New Task #{new_id}",
                "status": "New",
                "due": "Today",
                "report": "Created via UI"
            })
            st.rerun()
    
    tasks = st.session_state.tasks
    if status_filter != "All":
        tasks = [t for t in tasks if t["status"] == status_filter]
    
    for task in tasks:
        status_icon = {"New": "🔵", "Ongoing": "🟡", "Completed": "✅"}.get(task["status"], "⚪")
        with st.expander(f"{status_icon} {task['title']}  —  {task['status']}  |  Due: {task['due']}"):
            st.markdown(f"**Execution Report:** {task['report']}")
            st.markdown(f"**Idempotency Key:** `task-{task['id']}-{uuid.uuid4().hex[:8]}`")
            col1, col2 = st.columns(2)
            with col1:
                if task["status"] != "Completed":
                    if st.button(f"Mark Complete", key=f"done_{task['id']}"):
                        task["status"] = "Completed"
                        st.rerun()
            with col2:
                if st.button(f"🔄 Replay Task", key=f"replay_{task['id']}"):
                    st.info(f"Re-queuing '{task['title']}' through the MCP Gateway...")

# ═══════════════════════════════════════════════════════════════
# PAGE: CALENDAR
# ═══════════════════════════════════════════════════════════════
elif page == "📅 Calendar":
    st.markdown("### 📅 Calendar View")
    
    today = datetime.now()
    week_cols = st.columns(7)
    for i, col in enumerate(week_cols):
        day = today + timedelta(days=i - today.weekday())
        with col:
            is_today = day.date() == today.date()
            border_style = "border: 2px solid #7c3aed;" if is_today else "border: 1px solid #374151;"
            st.markdown(f"""
            <div style="background:#1e1b4b; {border_style} border-radius:10px; padding:12px; text-align:center; min-height:120px;">
                <div style="color:#a5b4fc; font-size:12px;">{day.strftime('%a')}</div>
                <div style="color:#e0e7ff; font-size:22px; font-weight:700;">{day.strftime('%d')}</div>
                <div style="color:#6b7280; font-size:11px; margin-top:8px;">{'📌 Tasks due' if is_today else ''}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("###")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("➕ Add Calendar Block", use_container_width=True):
            st.info("This will trigger the `schedule_meeting` MCP tool via the Chat interface.")
    with col2:
        if st.button("🔄 Sync Google Calendar", use_container_width=True):
            st.info("Calendar API integration available via the `fetch_calendar` MCP tool.")

# ═══════════════════════════════════════════════════════════════
# PAGE: AUDIT
# ═══════════════════════════════════════════════════════════════
elif page == "🛡️ Audit":
    st.markdown("### 🛡️ Audit & Observability Hub")
    
    st.info("Audit records are published to Google Cloud Pub/Sub topic `taskninja-events` in real-time by the Telemetry Node.")
    
    # Show chat-based audit trail from session
    if st.session_state.messages:
        st.markdown("#### Session Execution Log")
        for i, msg in enumerate(st.session_state.messages):
            if msg["role"] == "assistant" and msg.get("metadata"):
                meta = msg["metadata"]
                with st.expander(f"🔎 Decision #{i//2 + 1} — ID: `{meta.get('decision_id', 'N/A')}`"):
                    st.markdown(f"**Agents Invoked:** {', '.join(meta.get('invoked_agents', []))}")
                    st.markdown(f"**Latency:** {meta.get('latency_seconds', 'N/A')}s")
                    st.markdown("**Full Trace Payload:**")
                    st.json(meta, expanded=False)
    else:
        st.warning("No execution traces yet. Start a conversation in the Chat view to generate audit data.")
