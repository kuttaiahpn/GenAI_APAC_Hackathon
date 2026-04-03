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
BACKEND_URL = os.getenv("BACKEND_URL", "https://taskninja-mcp-gateway-836906162288.us-central1.run.app")

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
    st.caption(f"Thread: `{st.session_state.thread_id[:8]}`")
    if st.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.rerun()

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
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown('<div class="metric-card"><h3>Active Agents</h3><div class="num">4</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown('<div class="metric-card"><h3>Pending Tasks</h3><div class="num">3</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown('<div class="metric-card"><h3>Search Context</h3><div class="num">Vector</div></div>', unsafe_allow_html=True)
    
    st.divider()
    st.subheader("🚀 Getting Started")
    st.info("Navigate to the **💬 Swarm Chat** page to interact with the Agents using natural language.")

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
                with st.expander("🔍 Swarm Trace Details"):
                    st.json(msg["meta"])

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
# PAGE: TASKS
# ═══════════════════════════════════════════════════════════════
elif page_key == "tasks":
    st.write("### task-ninja-queue")
    for task in st.session_state.tasks:
        with st.expander(f"{task['title']} [{task['status']}]"):
            st.write(f"Due: {task['due']}")
            if st.button("Mark Completed", key=f"btn_{task['id']}"):
                task["status"] = "Completed"
                st.info("Update synchronized.")

# ═══════════════════════════════════════════════════════════════
# PAGE: CALENDAR (Stub)
# ═══════════════════════════════════════════════════════════════
elif page_key == "calendar":
    st.write("### Swarm Calendar View")
    st.info("The Calendar Agent can be triggered via the Chat page by asking to schedule meetings.")

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
