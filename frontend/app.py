import streamlit as st
import requests
import uuid
import time
import os

# Essential config rendering the UI across the full viewport identically mimicking a SaaS tool
st.set_page_config(page_title="TaskNinja | Command Center", layout="wide", initial_sidebar_state="expanded")

# =================================================================================
# Custom CSS Injections - Masking Chrome & Structuring the Floating Action Chat
# =================================================================================
st.markdown("""
<style>
    /* Vanish standard Streamlit Chrome */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Top Bar SaaS Aesthetics */
    .top-bar-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #1F2937;
        padding: 15px 30px;
        border-radius: 12px;
        margin-bottom: 25px;
        border: 1px solid #374151;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .top-title { font-size: 26px; font-weight: 800; color: #F3F4F6; margin: 0; display: flex; align-items: center; gap: 10px; }
    .badge-container { display: flex; align-items: center; gap: 15px; }
    .model-badge { background-color: #8B5CF6; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 700; }
    
    /* The Magical Floating Chat Popover Hack */
    div[data-testid="stPopover"] {
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 99999;
    }
    div[data-testid="stPopover"] > button {
        background-color: #8B5CF6 !important;
        color: white !important;
        border-radius: 50px !important;
        padding: 12px 24px !important;
        font-weight: bold !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3) !important;
        border: 2px solid #A78BFA !important;
        transition: transform 0.2s;
    }
    div[data-testid="stPopover"] > button:hover {
        transform: scale(1.05);
    }
</style>
""", unsafe_allow_html=True)

# =================================================================================
# Core Session State Maintenance (Bulletproof API memory limits)
# =================================================================================
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("API_KEY", "hackathon_default_key")

BACKEND_URL = os.getenv("BACKEND_URL", "https://taskninja-mcp-gateway-836906162288.us-central1.run.app")

# =================================================================================
# Persistent Global Layout Views
# =================================================================================
st.markdown("""
<div class="top-bar-container">
    <div class="top-title">🥷 TaskNinja <span style="font-size: 14px; font-weight: 400; color: #9CA3AF;">Hackathon Build v1.0</span></div>
    <div class="badge-container">
        <span class="model-badge">Routing Layer: gemini-2.5-flash</span>
        <button style="background:transparent; border:1px solid #6B7280; color:#D1D5DB; padding:6px 14px; border-radius:20px; cursor:pointer;">Switch Model</button>
    </div>
</div>
""", unsafe_allow_html=True)

# Application Sidebar (Left Nav pane)
with st.sidebar:
    st.markdown("### Context Navigation")
    current_view = st.radio("Dashboards", ["Command Center", "Calendar", "Audit Hub"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("👤 **Admin Mode Active**")

# Contextual Screen Mapping (As configured in UI Spec)
if current_view == "Command Center":
    st.markdown("### 🏠 System Dashboard")
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.markdown("#### 📅 Today's Requirements\n- Configure Service Accounts\n- Pitch Deck Formatting\n- Ping Project Stakeholders")
    with col2:
        with st.container(border=True):
            st.markdown("#### 🚀 Upcoming Sprints\n- Security review of GCP components\n- Finalize judging presentation")
    with col3:
        with st.container(border=True):
            st.markdown("#### ✅ Completed Traces\n- Setup Vertex Embeddings\n- Configured Model Context Protocol Gateway")

elif current_view == "Calendar":
    st.markdown("### 📅 Calendar Perspective")
    st.info("Connect to Google Calendar via settings to overlay upcoming events dynamically. The API Bridge is ready to receive calendar scheduling arrays!")
    st.button("Add Manual Block")
    
elif current_view == "Audit Hub":
    st.markdown("### 🛡️ Swarm Execution Metrics")
    st.warning("Audit records are actively captured inside Google Cloud Pub/Sub (`taskninja-events` topic). Pull the subscription to stream visual logs here!")

# =================================================================================
# The Hovering Chat "Illusion" Structure
# =================================================================================
with st.popover("💬 Engage TaskNinja Swarm", use_container_width=False):
    st.markdown("### System Terminal")
    st.caption(f"Session Matrix ID: `{st.session_state.thread_id[:12]}`")
    
    # 1. Output historical trace interactions dynamically
    st.markdown("<div style='height: 350px; overflow-y: auto; padding-right: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            # Display perfectly nested metadata drop-downs
            if "metadata" in msg and msg["metadata"]:
                with st.expander("🔍 View Swarm Traces (Judge's Toolkit)"):
                    st.json(msg["metadata"], expanded=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 2. Accept explicit logic instructions natively
    if user_query := st.chat_input("Instruct your AI Swarm..."):
        st.session_state.messages.append({"role": "user", "content": user_query})
        st.rerun() # Hard loop back to UI render prioritizing rapid engagement framing
        
    # 3. Synchronous Graph Processing Loop
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        query_str = st.session_state.messages[-1]["content"]
        with st.chat_message("assistant"):
            
            # Formulating the explicit "Illusion of Speed" widget
            status_container = st.status("Initializing Swarm Topology...", expanded=True)
            with status_container:
                st.write("Resolving Thread Context.")
                try:
                    start_time = time.time()
                    
                    st.write("Transmitting standard payload across the API Bridge...")
                    headers = {"X-API-Key": st.session_state.api_key}
                    payload = {"query": query_str, "thread_id": st.session_state.thread_id}
                    
                    # Force execution against the Phase 3 backend framework!
                    st.write("Executing LangGraph nodes dynamically 📈...")
                    res = requests.post(f"{BACKEND_URL}/v1/orchestrate", json=payload, headers=headers)
                    res.raise_for_status()
                    
                    st.write("Processing Telemetry Payload...")
                    data = res.json()
                    
                    latency = time.time() - start_time
                    status_container.update(label=f"Nodes Compiled ({latency:.2f}s)", state="complete", expanded=False)
                    
                    final_text = data.get("response", "Swarm execution encountered an unknown trace completion.")
                    meta = data.get("metadata", {})
                    
                    # Print results visually
                    st.write(final_text)
                    with st.expander("🔍 View Swarm Traces (Judge's Toolkit)"):
                        st.json(meta, expanded=True)
                        
                    # Save results strictly to memory
                    st.session_state.messages.append({"role": "assistant", "content": final_text, "metadata": meta})
                    st.rerun() # Redraw finalizing the execution cycle!
                    
                except requests.exceptions.RequestException as e:
                    st.error(f"Networking Gateway Offline: {e}")
                    status_container.update(label="Critical API Breach", state="error", expanded=True)
