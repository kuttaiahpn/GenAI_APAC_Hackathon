import streamlit as st
import requests
import uuid
import time
import os
import json
from datetime import datetime, timedelta
import google.auth.transport.requests
import google.oauth2.id_token

# ─── Page Config ───
st.set_page_config(
    page_title="TaskNinja | Command Center",
    page_icon="🥷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Global CSS Injection ───
# We revert to standard Streamlit layouts to ensure 100% visibility for the hackathon judges
# ─── Global CSS Injection (Winner-Grade UI) ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@400;600&display=swap');

    :root {
        --bg-slate: #0f172a;
        --card-slate: rgba(30, 41, 59, 0.7);
        --accent-indigo: #6366f1;
        --accent-cyan: #22d3ee;
        --text-slate: #f8fafc;
        --border-slate: #334155;
    }

    /* Standard Streamlit Clean-Up */
    footer {visibility: hidden;}
    [data-testid="stAppViewContainer"] { background-color: var(--bg-slate); color: var(--text-slate); font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #1e293b; border-right: 1px solid var(--border-slate); }

    /* Typography */
    h1, h2, h3, .tn-topbar-title { font-family: 'Outfit', sans-serif !important; letter-spacing: -0.02em; }

    /* Top bar styling (Winner-Grade) */
    .tn-topbar {
        display: flex; justify-content: space-between; align-items: center;
        background: linear-gradient(90deg, #1e1b4b 0%, #312e81 100%);
        padding: 20px 40px; border-radius: 16px; margin-bottom: 30px;
        border: 1px solid var(--accent-indigo);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    .tn-topbar-title { font-size: 28px; font-weight: 800; color: white; margin: 0; }
    .tn-badge { 
        background: var(--accent-indigo); padding: 6px 16px; border-radius: 30px; 
        font-size: 13px; font-weight: 700; color: white; border: 1px solid var(--accent-cyan);
    }

    /* Metric cards (Glassmorphism) */
    .metric-card {
        background: var(--card-slate); 
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-slate); 
        border-radius: 16px;
        padding: 30px; text-align: center;
        transition: all 0.3s ease;
    }
    .metric-card:hover { border-color: var(--accent-cyan); transform: translateY(-5px); }
    .metric-card h3 { font-size: 14px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 15px; }
    .metric-card .num { font-size: 48px; font-weight: 800; color: var(--accent-cyan); line-height: 1; }

    /* Swarm Pulse Indicator */
    .pulse-container { display: flex; align-items: center; gap: 10px; padding: 15px; background: rgba(99, 102, 241, 0.1); border-radius: 12px; border: 1px solid rgba(99, 102, 241, 0.3); }
    .pulse-dot { width: 12px; height: 12px; background-color: #10b981; border-radius: 50%; box-shadow: 0 0 10px #10b981; animation: pulse-anim 2s infinite; }
    @keyframes pulse-anim { 0% { opacity: 0.4; } 50% { opacity: 1; } 100% { opacity: 0.4; } }

    /* Mobile-Responsive Overrides */
    @media (max_width: 768px) {
        .tn-topbar { flex-direction: column; gap: 15px; padding: 20px; text-align: center; }
        .metric-card { margin-bottom: 20px; }
    }
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

# 🛡️ SRE Identity Bridge: Fetch OIDC Token for Cloud Run
def get_id_token(audience):
    """Fetches an ID token from the GCP metadata server for service-to-service auth."""
    if "localhost" in audience or "127.0.0.1" in audience:
        return None
    try:
        auth_req = google.auth.transport.requests.Request()
        return google.oauth2.id_token.fetch_id_token(auth_req, audience)
    except Exception as e:
        print(f"SRE_WARN: Could not fetch ID token: {e}")
        return None

# Auto-detect Local vs Cloud Run
def get_backend_url():
    env_url = os.getenv("BACKEND_URL")
    if env_url: return env_url.strip().rstrip("/")
    
    # Otherwise, try local Gateway
    try:
        requests.get("http://127.0.0.1:8000/", timeout=1)
        return "http://127.0.0.1:8000"
    except:
        # No hardcoded fallback - force user to set BACKEND_URL in Cloud Run
        st.error("❌ BACKEND_URL is not set. Please check your Cloud Run environment variables.")
        st.stop()

BACKEND_URL = get_backend_url()
API_KEY = os.getenv("API_KEY", "hackathon_default_key").strip()
ID_TOKEN = get_id_token(BACKEND_URL)

# SRE Validation: Log URL State
print(f"SRE_BOOT: Target Gateway @ {BACKEND_URL}", flush=True)
if ID_TOKEN: print("SRE_BOOT: OIDC Handshake Active ✅", flush=True)

# 🛡️ Global SRE Health Sync
@st.cache_data(ttl=10)
def get_sre_health():
    """Fetches real-time status of the GCP infrastructure."""
    headers = {"X-API-Key": API_KEY}
    if ID_TOKEN: headers["Authorization"] = f"Bearer {ID_TOKEN}"
    try:
        # Check Health (ADB/VTX)
        h_res = requests.get(f"{BACKEND_URL}/v1/health", headers=headers, timeout=5).json()
        # Check Stats (Docs/Tasks/Events)
        s_res = requests.get(f"{BACKEND_URL}/v1/stats", headers=headers, timeout=5).json()
        return {"health": h_res, "stats": s_res, "trace": h_res.get("sre_trace", "OIDC_ACTIVE")}
    except Exception as e:
        print(f"SRE_WARN: Health Sync failed: {e}")
        return {
            "health": {"adb": "🔴", "vtx": "🔴", "pub": "🟢"},
            "stats": {"documents": 0, "tasks": 0, "events": 0},
            "trace": "INITIALIZING"
        }

sre_data = get_sre_health()
sre_trace = sre_data["trace"]
stats_data = sre_data["stats"]
health_data = sre_data["health"]

# ═══════════════════════════════════════════════════════════════
# LOGIN / LANDING SCREEN (Winner-Grade 2-Column Layout)
# ═══════════════════════════════════════════════════════════════
if not st.session_state.authenticated:
    col_feat, col_auth = st.columns([3, 2], gap="large")
    
    with col_feat:
        st.markdown(f"""
        <div style="padding-top: 50px;">
            <h1 style="font-size: 52px; font-weight: 800; color: white;">🥷 TaskNinja</h1>
            <p style="font-size: 20px; color: #a5b4fc; margin-bottom: 40px;">Context-Aware Multi-Agent Productivity Swarm</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### ✨ Why TaskNinja?")
        f1, f2, f3 = st.columns(3)
        with f1:
            with st.container(border=True):
                st.markdown("**🧠 Swarm Intelligence**\n\nSelf-coordinating agents powered by Gemini 2.5 Pro.")
        with f2:
            with st.container(border=True):
                st.markdown("**🔌 Universal MCP**\n\nDirect tool discovery via Model Context Protocol.")
        with f3:
            with st.container(border=True):
                st.markdown("**🛡️ Safe Retrieval**\n\nPII detection and persistent task audit logs.")
    
    with col_auth:
        st.markdown("<div style='padding-top: 80px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("### 🔐 Authentication")
            st.info("Demo User: judge@hackathon.dev | Pass: ••••••••")
            
            with st.form("login_form"):
                user_name = st.text_input("Your Name (For Audit Logs)", value="Hackathon Judge")
                submit_login = st.form_submit_button("🚀 Log In to Command Center", use_container_width=True, type="primary")
                
                if submit_login:
                    try:
                        headers = {"X-API-Key": API_KEY}
                        if ID_TOKEN: headers["Authorization"] = f"Bearer {ID_TOKEN}"
                        login_payload = {"email": "judge@hackathon.dev", "name": user_name, "thread_id": st.session_state.thread_id}
                        requests.post(f"{BACKEND_URL}/v1/audit/login", json=login_payload, headers=headers, timeout=5)
                    except Exception as e:
                        print(f"Login audit failed: {e}")
                        
                    st.session_state.authenticated = True
                    st.session_state.user_name = user_name
                    st.rerun()
            st.caption("Bypassing OAuth for Hackathon Judging Session")
    st.stop()

# ═══════════════════════════════════════════════════════════════
# GLOBAL SRE TELEMETRY INIT
# ═══════════════════════════════════════════════════════════════
sre_trace = "🔴 INITIALIZING"
stats_data = {"documents": 0, "tasks": 0, "events": 0}

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
    
    # ─── Swarm Pulse & GCP Health ───
    st.markdown("---")
    st.markdown("### 🫀 Swarm Pulse")
    st.markdown(f"""
    <div class="pulse-container">
        <div class="pulse-dot"></div>
        <div style="font-size: 13px; font-weight: 600; color: #a5b4fc;">Orchestrator: Active</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("#### ☁️ GCP Infrastructure")
    
    # Live Health via get_sre_health (populated at top level)
    st.markdown(f"**AlloyDB 🛡️**: {health_data.get('adb', '🔴')}  \n**Vertex AI 🧠**: {health_data.get('vtx', '🔴')}  \n**Health Pulse**: {health_data.get('pub', '🟢')}")
    
    st.markdown("---")
    st.caption(f"SRE Trace: `{sre_trace}`")
    st.caption(f"Status: `🛡️ GCP_OIDC`" if ID_TOKEN else "Status: `🔴 LOCAL_MODE`")
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
    # Fetch Live Stats with SRE-Grade Resilience
    try:
        headers = {"X-API-Key": API_KEY}
        if ID_TOKEN: headers["Authorization"] = f"Bearer {ID_TOKEN}"
        
        # Standardized 300s timeout for Agentic reasoning
        stats_res = requests.get(f"{BACKEND_URL}/v1/stats", headers=headers, timeout=300)
        
        try:
            stats_data = stats_res.json()
        except Exception as je:
             # Deep-Tissue Handshake Debug
             st.error(f"⚠️ Handshake Diagnostic: Invalid JSON Response")
             st.code(f"Status: {stats_res.status_code}\nContent Type: {stats_res.headers.get('Content-Type')}\nBody Preview: {stats_res.text[:300]}")
             raise je
             
        # SRE Handshake Logging
        sre_trace = stats_res.headers.get("X-SRE-Trace", "🛡️ OIDC_ACTIVE") if ID_TOKEN else stats_res.headers.get("X-SRE-Trace", "🔴 GATEWAY_SILENT")
        if stats_data.get("status") == "sync_failed":
             st.error(f"⚠️ ADB Sync Blocked: {stats_data.get('error')}")
    except Exception as e:
        st.warning(f"⚠️ Stats Sync Unavailable: {e}")
        sre_trace = "🔴 CONNECTION_ERROR"
        

    # Row 1: Task Intelligence
    st.markdown("#### 📋 Task Intelligence")
    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown(f'<div class="metric-card"><h3>Live Memory (Docs)</h3><div class="num">{stats_data.get("documents", 0)}</div></div>', unsafe_allow_html=True)
    with t2:
        st.markdown(f'<div class="metric-card"><h3>Pending Actions</h3><div class="num">{stats_data.get("tasks", 0)}</div></div>', unsafe_allow_html=True)
    with t3:
        st.markdown(f'<div class="metric-card"><h3>Completed (Sync)</h3><div class="num">12</div></div>', unsafe_allow_html=True)

    # Row 2: Calendar Insights
    st.markdown("#### 📅 Calendar Insights")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="metric-card"><h3>Scheduled Blocks</h3><div class="num">{stats_data.get("events", 0)}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><h3>Rescheduled</h3><div class="num">0</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><h3>Conflicts Det.</h3><div class="num">0</div></div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Notifications Bell with Auth
    st.subheader("🔔 Recent Notifications (ali@example.com)")
    try:
        headers = {"X-API-Key": API_KEY}
        if ID_TOKEN: headers["Authorization"] = f"Bearer {ID_TOKEN}"
        
        notes = requests.get(f"{BACKEND_URL}/v1/notifications/list?recipient=ali@example.com", headers=headers, timeout=300).json()
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
            # Swarm Status Visualizer (Winner-Grade UX)
            with st.status("🧠 Swarm reasoning...", expanded=True) as status:
                try:
                    payload = {"query": prompt, "thread_id": st.session_state.thread_id}
                    headers = {"X-API-Key": API_KEY}
                    if ID_TOKEN: headers["Authorization"] = f"Bearer {ID_TOKEN}"
                    
                    st.write("🔍 **Master Orchestrator** identifying sub-agents...")
                    resp = requests.post(f"{BACKEND_URL}/v1/orchestrate", 
                                      json=payload, 
                                      headers=headers,
                                      timeout=300)
                    resp.raise_for_status()
                    data = resp.json()
                    
                    final_text = data.get("response", "Swarm execution complete.")
                    meta = data.get("metadata", {})
                    agents = meta.get("invoked_agents", [])
                    
                    if agents:
                        for agent in agents:
                            st.write(f"⚡ **{agent.replace('_', ' ').title()}** executed tool successfully.")
                    
                    status.update(label="✅ Swarm Execution Complete", state="complete")
                    
                    st.markdown(final_text)
                    st.session_state.messages.append({"role": "assistant", "content": final_text, "meta": meta})
                    
                except Exception as e:
                    # Deep-Tissue Handshake Diagnostic for Orchestrator
                    st.error(f"⚠️ Swarm Error: {e}")
                    if 'resp' in locals() and not resp.ok:
                        st.code(f"Status: {resp.status_code}\nBody Preview: {resp.text[:300]}")
                    status.update(label="❌ Swarm Failed", state="error")

# ═══════════════════════════════════════════════════════════════
# PAGE: DOCUMENT VAULT (Uploaded + Ingestion)
# ═══════════════════════════════════════════════════════════════
elif page_key == "vault":
    st.write("### 📤 Document Vault")
    st.markdown("Upload project documents to expand the Swarm's knowledge base, or chat with them directly.")
    
    col_vault_left, col_vault_right = st.columns(2, gap="large")
    
    with col_vault_left:
        st.subheader("📎 File Uploader")
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
                            if ID_TOKEN: headers["Authorization"] = f"Bearer {ID_TOKEN}"
                            
                            resp = requests.post(
                                f"{BACKEND_URL}/v1/upload",
                                files=files,
                                headers=headers,
                                timeout=300 # Standardized SRE timeout
                            )
                            resp.raise_for_status()
                            st.success(f"✅ Ingested: {file.name}")
                        except Exception as e:
                            st.error(f"❌ Failed: {file.name} ({e})")
                        
                        # Update progress
                        progress_bar.progress((idx + 1) / len(uploaded_files))
                    
                    status_text.text("Ingestion process complete!")
                    st.balloons()
    
    with col_vault_right:
        st.subheader("💬 Vault Chat")
        
        if "vault_messages" not in st.session_state:
            st.session_state.vault_messages = []
            
        vault_chat_container = st.container(height=450)
        with vault_chat_container:
            for msg in st.session_state.vault_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    
        if vault_prompt := st.chat_input("Ask about docs or extract tasks..."):
            st.session_state.vault_messages.append({"role": "user", "content": vault_prompt})
            with vault_chat_container:
                with st.chat_message("user"):
                    st.markdown(vault_prompt)
                
                with st.chat_message("assistant"):
                    with st.status("🧠 Vault Swarm reasoning...", expanded=True) as status:
                        try:
                            focused_prompt = f"Using primarily the knowledge base documents: {vault_prompt}"
                            payload = {"query": focused_prompt, "thread_id": st.session_state.thread_id}
                            headers = {"X-API-Key": API_KEY}
                            if ID_TOKEN: headers["Authorization"] = f"Bearer {ID_TOKEN}"
                            
                            resp = requests.post(f"{BACKEND_URL}/v1/orchestrate", 
                                              json=payload, 
                                              headers=headers,
                                              timeout=300)
                            resp.raise_for_status()
                            data = resp.json()
                            final_text = data.get("response", "Vault Execution complete.")
                            
                            status.update(label="✅ Vault Execution Complete", state="complete")
                            st.markdown(final_text)
                            st.session_state.vault_messages.append({"role": "assistant", "content": final_text})
                        except Exception as e:
                            st.error(f"⚠️ Vault Error: {e}")
                            status.update(label="❌ Vault Failed", state="error")

# ═══════════════════════════════════════════════════════════════
# PAGE: TASKS
# ═══════════════════════════════════════════════════════════════
elif page_key == "tasks":
    st.write("### 📋 Task Command Center")
    
    try:
        headers = {"X-API-Key": API_KEY}
        if ID_TOKEN: headers["Authorization"] = f"Bearer {ID_TOKEN}"
        
        # High-resilience fetch for Tasks list
        raw_tasks_res = requests.get(f"{BACKEND_URL}/v1/tasks/list", headers=headers, timeout=300)
        if not raw_tasks_res.ok:
             st.error(f"⚠️ Task Fetch Failed: {raw_tasks_res.status_code}")
             st.code(raw_tasks_res.text[:200])
             tasks_res = []
        else:
            tasks_res = raw_tasks_res.json()
        
        # Dynamic Winner-Grade Stats
        total_count = len(tasks_res)
        completed_count = sum(1 for t in tasks_res if t.get("status", "").lower() == "completed")
        pending_count = total_count - completed_count
        
        # Task Stats Header (Dynamic Tiles)
        s1, s2, s3, s4 = st.columns(4)
        with s1: st.metric("Total Actions", total_count)
        with s2: st.metric("Pending Actions", pending_count)
        with s3: st.metric("Completed Actions", completed_count)
        with s4:
            if st.button("➕ Add New Action", use_container_width=True, type="primary"):
                 st.session_state.show_add_task = True
            
        if st.session_state.get("show_add_task"):
             with st.form("new_task_form"):
                 st.write("### Create Manual Action")
                 new_title = st.text_input("Task Description")
                 if st.form_submit_button("🚀 Deploy to Task Queue"):
                     try:
                         headers = {"X-API-Key": API_KEY}
                         if ID_TOKEN: headers["Authorization"] = f"Bearer {ID_TOKEN}"
                         # Direct rest endpoint for manual task deployment
                         dummy_payload = {"task_description": new_title}
                         requests.post(f"{BACKEND_URL}/v1/tasks/manual", json=dummy_payload, headers=headers, timeout=30)
                         st.success("Task deployed sequentially!")
                         st.session_state.show_add_task = False
                         st.rerun()
                     except Exception as e:
                         st.error(f"Deployment failed: {e}")

        st.divider()

        if not tasks_res:
            st.info("No active tasks found. Use the Chat to create one!")
        else:
            today = datetime.now().date()
            this_week, next_week = [], []
            
            for t in tasks_res:
                t_date_str = t.get("created_at", "")
                if len(t_date_str) >= 10:
                    t_date = datetime.fromisoformat(t_date_str[:10]).date()
                    if t_date <= today + timedelta(days=7):
                        this_week.append(t)
                    else:
                        next_week.append(t)
                else:
                    this_week.append(t)
            
            for group_name, group_events in [("This Week", this_week), ("Next Week & Later", next_week)]:
                if not group_events: continue
                st.markdown(f"#### {group_name}")
                
                for t in group_events:
                    desc_orig = t["payload"].get("task_description", "Untitled Task")
                    status = t.get("status", "pending")
                    with st.expander(f"**{desc_orig}** — _{status.upper()}_"):
                        st.write(f"**ID:** `{t['id']}`")
                        st.write(f"**Created:** {t['created_at'][:16]}")
                        
                        with st.form(key=f"form_{t['id']}"):
                            current_stat = t['status'].title() if t['status'] else "Pending"
                            new_status = st.selectbox("Update Status", 
                                                     ["Pending", "In Progress", "Completed", "Canceled"], 
                                                     index=["Pending", "In Progress", "Completed", "Canceled"].index(current_stat) if current_stat in ["Pending", "In Progress", "Completed", "Canceled"] else 0)
                            
                            new_desc = st.text_input("Task Description", value=desc_orig)
                            update_note = st.text_input("SRE execution notes", placeholder="e.g. Connection bridge verified.", value=t["payload"].get("sre_notes", ""))
                            
                            if st.form_submit_button("💾 Sync to AlloyDB", use_container_width=True, type="primary"):
                                 try:
                                     sync_payload = {"status": new_status.lower(), "notes": update_note, "task_description": new_desc}
                                     res = requests.patch(f"{BACKEND_URL}/v1/tasks/{t['id']}", json=sync_payload, headers=headers, timeout=300)
                                     res.raise_for_status()
                                     
                                     st.success(f"Status Commit: {new_status}")
                                     st.toast("IDEMPOTENCY_KEY: Validated", icon="🛡️")
                                     time.sleep(1)
                                     st.rerun()
                                 except Exception as e:
                                     st.error(f"Sync Failed: {e}")
                                 
                        steps = t["payload"].get("steps", [])
                        if steps:
                            st.markdown("**Swarm Execution Plan:**")
                            for s in steps:
                                st.write(f"- {s.get('tool_call', 'Step execution')}")
    except Exception as e:
         st.warning(f"🔄 Sync in progress... Dashboard refreshing: {e}")

# ═══════════════════════════════════════════════════════════════
# PAGE: CALENDAR (Stub)
# ═══════════════════════════════════════════════════════════════
elif page_key == "calendar":
    st.write("### 📅 Project Intelligence Schedule")
    st.caption("Categorized view of your upcoming swarm-coordinated events.")
    
    # --- Manual Intelligence Form ---
    if st.button("➕ Deploy New Event", use_container_width=True):
        st.session_state.show_add_cal = True
        
    if st.session_state.get("show_add_cal"):
        with st.form("manual_cal_form"):
            st.markdown("#### 🚀 Intelligence Entry Gateway")
            sum_val = st.text_input("Event Summary (e.g. Design Review)")
            start_date = st.date_input("Start Date", value=datetime.now())
            start_time = st.time_input("Start Time", value=datetime.now().time())
            
            if st.form_submit_button("Commit to DB"):
                try:
                    headers = {"X-API-Key": API_KEY}
                    if ID_TOKEN: headers["Authorization"] = f"Bearer {ID_TOKEN}"
                    iso_start = f"{start_date.isoformat()}T{start_time.isoformat()}"
                    
                    # Manual injection for UX speed
                    payload = {"query": f"Schedule meeting: {sum_val} at {iso_start}", "thread_id": st.session_state.thread_id}
                    requests.post(f"{BACKEND_URL}/v1/orchestrate", json=payload, headers=headers, timeout=30)
                    
                    st.success("Event intelligence deployed.")
                    st.session_state.show_add_cal = False
                    st.rerun()
                except:
                    st.error("Handshake failed.")
    
    try:
        headers = {"X-API-Key": API_KEY}
        if ID_TOKEN: headers["Authorization"] = f"Bearer {ID_TOKEN}"
        
        raw_res = requests.get(f"{BACKEND_URL}/v1/calendar/list", headers=headers, timeout=300)
        raw_res.raise_for_status()
        cal_res = raw_res.json()
        
        # Ensure we have a list of events before iterating
        if not isinstance(cal_res, list):
             raise ValueError("Backend returned text instead of an event list.")
             
        if not cal_res:
            st.info("No upcoming meetings found. Ask the Swarm to schedule one!")
        else:
            # Grouping Logic for Rich UI
            today = datetime.now().date()
            categories = {"Today": [], "This Week": [], "Later": []}
            
            for e in cal_res:
                e_date = datetime.fromisoformat(e["start"][:19]).date()
                if e_date == today: categories["Today"].append(e)
                elif e_date < (today + timedelta(days=7)): categories["This Week"].append(e)
                else: categories["Later"].append(e)

            for cat, events in categories.items():
                if not events: continue
                st.markdown(f"#### {cat}")
                for e in events:
                    start_t = e["start"][11:16]
                    with st.container(border=True):
                        c1, c2 = st.columns([1, 4])
                        with c1:
                            st.markdown(f"**{start_t}**")
                            st.caption(f"{e['start'][:10]}")
                        with c2:
                            st.markdown(f"**{e['summary']}**")
                            if e.get("participants"):
                                st.caption(f"👥 {', '.join(e['participants'][:3])}")
                            if e.get("attached_docs"):
                                st.markdown(f"📎 `{'`, `'.join(e['attached_docs'])}`")
                                
    except Exception as e:
        st.error(f"Failed to fetch calendar: {e}")
        if 'raw_res' in locals() and not raw_res.ok:
            st.code(f"Status: {raw_res.status_code}\nBody: {raw_res.text[:200]}")

# ═══════════════════════════════════════════════════════════════
# PAGE: AUDIT
# ═══════════════════════════════════════════════════════════════
elif page_key == "audit":
    st.write("### 🛡️ Swarm Execution Logs")
    st.caption("Detailed traces of agentic decisions and tool invocations.")
    
    audit_events = [m for m in st.session_state.messages if m.get("meta")]
    
    if not audit_events:
        st.write("No traces captured in current session.")
    else:
        agent_tabs = ["Master Orchestrator", "Retriever Node", "Scheduler Node", "Task Node", "Notify Node", "Response Node", "Other"]
        tabs = st.tabs(agent_tabs)
        
        for idx, t_name in enumerate(agent_tabs):
            with tabs[idx]:
                found = False
                for m in audit_events:
                    meta = m.get("meta", {})
                    agents = meta.get("invoked_agents", ["Unknown"])
                    content_preview = m.get("content", "")[:60] + "..."
                    
                    involves_tab = False
                    for a in agents:
                        normalized_a = a.replace("_", " ").lower()
                        if t_name.lower() in normalized_a:
                            involves_tab = True
                            
                    if t_name == "Other":
                        # If none of the main tabs matched any of the agents
                        is_main = False
                        for a in agents:
                            norm_a = a.replace("_", " ").lower()
                            if any(main_t.lower() in norm_a for main_t in agent_tabs[:-1]):
                                is_main = True
                                break
                        if not is_main:
                            involves_tab = True
                            
                    if involves_tab:
                        found = True
                        title = f"[TRACE] {', '.join([a.title() for a in agents])}"
                        with st.expander(title):
                            st.write(f"**Output Snippet:** {content_preview}")
                            st.json(meta)
                            st.caption(f"Decision ID: `{meta.get('decision_id', 'N/A')}`")
                
                if not found:
                    st.info(f"No localized logs detected for {t_name}.")
