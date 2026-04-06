import streamlit as st
import requests
import uuid
import time
import os
import json
from datetime import datetime, timedelta

# ─── Page Config ───
st.set_page_config(
    page_title="TaskNinja | Command Center",
    page_icon="🥷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Global CSS Injection ───
# We revert to standard Streamlit layouts to ensure 100% visibility for the hackathon judges
st.markdown("""
<style>
    /* Vanish the 'Made with Streamlit' footer */
    footer {visibility: hidden;}

    /* Top bar styling */
    .tn-topbar {
        display: flex; justify-content: space-between; align-items: center;
        background: #1e1b4b; padding: 15px 30px; border-radius: 12px; margin-bottom: 25px;
        border: 1px solid #3730a3;
    }
    .tn-topbar-title { font-size: 24px; font-weight: 800; color: #e0e7ff; }
    .tn-badge { 
        background: #7c3aed; padding: 4px 12px; border-radius: 20px; 
        font-size: 12px; font-weight: 700; color: white;
    }

    /* Metric cards */
    .metric-card {
        background: #1e1b4b; border: 1px solid #3730a3; border-radius: 12px;
        padding: 20px; text-align: center;
    }
    .metric-card .num { font-size: 36px; font-weight: 800; color: #7c3aed; }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ───
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tasks" not in st.session_state:
    st.session_state.tasks = [
        {"id": 1, "title": "Configure Service Accounts", "status": "New", "due": "Today"},
        {"id": 2, "title": "Pitch Deck Formatting", "status": "Ongoing", "due": "Today"},
        {"id": 3, "title": "Security Review GCP", "status": "New", "due": "Tomorrow"},
        {"id": 4, "title": "Setup Vertex Embeddings", "status": "Completed", "due": "Yesterday"},
    ]

API_KEY = os.getenv("API_KEY", "hackathon_default_key")

# Auto-detect Local vs Cloud Run
def get_backend_url():
    # If explicitly set in ENV, use that (for Cloud Run)
    env_url = os.getenv("BACKEND_URL")
    if env_url: return env_url
    
    # Otherwise, try local Gateway
    try:
        requests.get("http://127.0.0.1:8000/", timeout=1)
        return "http://127.0.0.1:8000"
    except:
        return "https://taskninja-mcp-gateway-836906162288.us-central1.run.app"

BACKEND_URL = get_backend_url()

# ═══════════════════════════════════════════════════════════════
# LOGIN SCREEN
# ═══════════════════════════════════════════════════════════════
if not st.session_state.authenticated:
    st.title("🥷 TaskNinja")
    st.subheader("Context-Aware Multi-Agent Productivity Assistant")
    
    with st.container(border=True):
        st.markdown("### 🔐 Authentication Required")
        st.info("Demo User: judge@hackathon.dev | Pass: ••••••••")
        if st.button("🚀 Log In to Command Center", use_container_width=True, type="primary"):
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# ═══════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION (Standard Elements)
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("🥷 TaskNinja")
    st.markdown("👤 **Judge Account**")
    
    # Selection mapping to avoid emoji comparison issues
    NAV_PAGES = {
        "dashboard": "🏠 Dashboard",
        "chat": "💬 Swarm Chat",
        "vault": "📤 Document Vault",
        "tasks": "📋 Task Manager",
        "calendar": "📅 Calendar",
        "audit": "🛡️ Audit Hub"
    }
    
    page_key = st.radio(
        "Menu",
        options=list(NAV_PAGES.keys()),
        format_func=lambda x: NAV_PAGES[x]
    )
    
    st.markdown("---")
    st.markdown("🟢 **System Pulse: Active**")
    st.caption(f"Backend: `{BACKEND_URL}`")
    
    if st.button("🔄 Refresh Data"):
        st.rerun()
        
    st.markdown("---")
    st.caption(f"Thread: `{st.session_state.thread_id[:8]}`")

# ═══════════════════════════════════════════════════════════════
# TOP BAR (Main Area)
# ═══════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="tn-topbar">
    <div class="tn-topbar-title">TaskNinja // {NAV_PAGES[page_key]}</div>
    <div style="display:flex; gap:10px;">
        <span class="tn-badge">API: Online</span>
        <span class="tn-badge">MCP: SSE</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════
if page_key == "dashboard":
    # Fetch Live Stats with Auth
    try:
        headers = {"X-API-Key": API_KEY}
        stats_res = requests.get(f"{BACKEND_URL}/v1/stats", headers=headers, timeout=5).json()
    except:
        stats_res = {"documents": 0, "tasks": 0, "events": 0}

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f'<div class="metric-card"><h3>Live Docs</h3><div class="num">{stats_res["documents"]}</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card"><h3>Active Tasks</h3><div class="num">{stats_res["tasks"]}</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-card"><h3>Calendar</h3><div class="num">{stats_res["events"]}</div></div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Notifications Bell with Auth
    st.subheader("🔔 Recent Notifications (ali@example.com)")
    try:
        headers = {"X-API-Key": API_KEY}
        notes = requests.get(f"{BACKEND_URL}/v1/notifications/list?recipient=ali@example.com", headers=headers, timeout=5).json()
        if notes.get("notifications"):
            for n in notes["notifications"][:3]:
                st.toast(f"New Alert: {n['message']}")
                st.warning(f"**{n['message']}**  \n*Channel: {n['channel']} | {n['created_at'][:16]}*")
        else:
            st.write("No new alerts.")
    except:
        st.write("Notification service unreachable.")

# ═══════════════════════════════════════════════════════════════
# PAGE: CHAT (The Core Feature)
# ═══════════════════════════════════════════════════════════════
elif page_key == "chat":
    st.write("### AI Swarm Terminal")
    st.caption("Ask your assistant to retrieve docs, schedule meetings, or organize tasks.")

    # Show History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("meta"):
                agents = msg["meta"].get("invoked_agents", [])
                if agents:
                    st.caption(f"🧠 **Swarm Trace:** {' ➔ '.join(agents)}")

    # Chat Input
    if prompt := st.chat_input("Tell TaskNinja what to do..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.status("🥷 Swarm reasoning...", expanded=True) as status:
                try:
                    payload = {"query": prompt, "thread_id": st.session_state.thread_id}
                    resp = requests.post(f"{BACKEND_URL}/v1/orchestrate", 
                                      json=payload, 
                                      headers={"X-API-Key": API_KEY},
                                      timeout=90)
                    resp.raise_for_status()
                    data = resp.json()
                    
                    final_text = data.get("response", "Execution complete.")
                    meta = data.get("metadata", {})
                    
                    st.markdown(final_text)
                    with st.expander("🔍 Swarm Trace Details"):
                        st.json(meta)
                    
                    st.session_state.messages.append({"role": "assistant", "content": final_text, "meta": meta})
                    status.update(label="✅ Success", state="complete")
                    
                except Exception as e:
                    st.error(f"Backend communication error: {e}")
                    status.update(label="❌ Failed", state="error")

# ═══════════════════════════════════════════════════════════════
# PAGE: DOCUMENT VAULT (Uploaded + Ingestion)
# ═══════════════════════════════════════════════════════════════
elif page_key == "vault":
    st.write("### 📤 Document Vault")
    st.markdown("Upload project documents to expand the Swarm's knowledge base. Supporters `.txt` and `.md` files.")
    
    uploaded_files = st.file_uploader(
        "Select files to ingest (Max 5)", 
        accept_multiple_files=True,
        type=["txt", "md"]
    )
    
    if uploaded_files:
        if st.button("🚀 Start Ingestion", use_container_width=True, type="primary"):
            if len(uploaded_files) > 5:
                st.error("Please select a maximum of 5 files.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, file in enumerate(uploaded_files):
                    status_text.text(f"Processing: {file.name}...")
                    try:
                        # Prepare multipart upload
                        files = [('files', (file.name, file.getvalue(), file.type))]
                        headers = {"X-API-Key": API_KEY}
                        
                        resp = requests.post(
                            f"{BACKEND_URL}/v1/upload",
                            files=files,
                            headers=headers,
                            timeout=60
                        )
                        resp.raise_for_status()
                        st.success(f"✅ Ingested: {file.name}")
                    except Exception as e:
                        st.error(f"❌ Failed: {file.name} ({e})")
                    
                    # Update progress
                    progress_bar.progress((idx + 1) / len(uploaded_files))
                
                status_text.text("Ingestion process complete!")
                st.balloons()

# ═══════════════════════════════════════════════════════════════
# PAGE: TASKS
# ═══════════════════════════════════════════════════════════════
elif page_key == "tasks":
    st.write("### 📋 Active Swarm Tasks")
    try:
        headers = {"X-API-Key": API_KEY}
        tasks_res = requests.get(f"{BACKEND_URL}/v1/tasks/list", headers=headers, timeout=5).json()
        if not tasks_res:
            st.info("No active tasks found. Use the Chat to create one!")
        else:
            for t in tasks_res:
                desc = t["payload"].get("task_description", "Untitled Task")
                status = t.get("status", "pending")
                with st.expander(f"{desc} [_{status}_]"):
                    st.write(f"**ID:** `{t['id']}`")
                    st.write(f"**Created:** {t['created_at'][:16]}")
                    steps = t["payload"].get("steps", [])
                    if steps:
                        st.markdown("**Execution Plan:**")
                        for s in steps:
                            st.write(f"- {s['tool_call']}")
    except:
        st.error("Failed to fetch tasks from backend.")

# ═══════════════════════════════════════════════════════════════
# PAGE: CALENDAR (Stub)
# ═══════════════════════════════════════════════════════════════
elif page_key == "calendar":
    st.write("### 📅 Swarm Calendar")
    try:
        headers = {"X-API-Key": API_KEY}
        cal_res = requests.get(f"{BACKEND_URL}/v1/calendar/list", headers=headers, timeout=5).json()
        if not cal_res:
            st.info("No upcoming meetings found.")
        else:
            for e in cal_res:
                start = e["start"][:16].replace("T", " ")
                with st.container(border=True):
                    st.markdown(f"#### {e['summary']}")
                    st.markdown(f"🕘 **Time:** {start}")
                    if e.get("attached_docs"):
                        st.caption(f"📎 **Attached:** {', '.join(e['attached_docs'])}")
    except:
        st.error("Failed to fetch calendar from backend.")

# ═══════════════════════════════════════════════════════════════
# PAGE: AUDIT
# ═══════════════════════════════════════════════════════════════
elif page_key == "audit":
    st.write("### System Logs")
    if not st.session_state.messages:
        st.write("No traces captured in current session.")
    else:
        for m in st.session_state.messages:
            if m.get("meta"):
                st.json(m["meta"])
