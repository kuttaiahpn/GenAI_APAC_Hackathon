import json
import uuid
import datetime
from typing import List
from langgraph.graph import StateGraph, END, START
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from google.cloud import pubsub_v1

from .state import AgentState
from .nodes import retriever_node, scheduler_node, task_node, notify_node

PROJECT_ID = "track3codelabs"
TOPIC_ID = "taskninja-events"

ORCHESTRATOR_SYSTEM_PROMPT = """You are the TaskNinja Orchestrator, a planning engine for a multi-agent productivity system.

Your job: Accept a user query and output a VALID JSON action payload. Nothing else.

STRICT RULES:
1. OUTPUT RAW JSON ONLY. No markdown, no commentary, no ```json blocks.
2. Every action needs a unique "idempotency_key" (use a short UUID-like string).
3. Pick the right action types from: "query_rag", "schedule_meeting", "create_task", "send_notification"

AVAILABLE TOOLS:
- query_rag: Search project documents. Payload: {"query_text": "...", "k": 5}
- schedule_meeting: Book a meeting. Payload: {"summary": "...", "start_time": "ISO8601", "end_time": "ISO8601", "participants": ["email"], "attached_docs": ["GCS_URI"]}
- fetch_calendar: Check schedule. Payload: {"time_min": "ISO8601", "time_max": "ISO8601"}
- create_task: Create a task. Payload: {"task_description": "...", "steps": [{"step_order": 1, "tool_call": "update_local_db", "parameters": {}}], "attached_docs": ["GCS_URI"]}
- send_notification: Send alert. Payload: {"recipient": "email or user_id", "message": "...", "channel": "ui_toast"}
- fetch_notifications: Check for alerts. Payload: {"recipient": "email or user_id", "status": "unread"}

REQUIRED OUTPUT FORMAT:
{"decision_id": "unique-id", "session_id": "session-id", "audit_id": "unique-id", "actions": [{"type": "action_type", "idempotency_key": "unique-key", "payload": {...}}]}

If the user query is conversational (greeting, general question), return:
{"decision_id": "unique-id", "session_id": "conversational", "audit_id": "unique-id", "actions": [{"type": "query_rag", "idempotency_key": "unique-key", "payload": {"query_text": "user's question rephrased for search", "k": 3}}]}

IMPORTANT: Use the CURRENT_TIME provided in the context for all relative date calculations (e.g., 'tomorrow', 'next Friday').
"""

async def master_orchestrator(state: AgentState) -> dict:
    """The Master Orchestrator — uses Gemini to decompose user intent into action payloads."""
    llm = ChatVertexAI(model_name="gemini-2.5-pro", temperature=0.1)
    
    user_q = state.get("user_query", "")
    session_summary = state.get("session_summary", "")
    rag = str(state.get("rag_context", []))
    tasks = str(state.get("active_tasks", []))
    
    context_str = f"""CURRENT_TIME: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
USER QUERY: {user_q}
SESSION_SUMMARY: {session_summary}
RAG_CONTEXT: {rag}
ACTIVE_TASKS: {tasks}"""
    
    combined_prompt = f"{ORCHESTRATOR_SYSTEM_PROMPT}\n\nCONTEXT:\n{context_str}"
    
    res = await llm.ainvoke(combined_prompt)
    
    # Parse JSON robustly
    try:
        raw = res.content.strip()
        # Strip markdown fences if LLM wraps them
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
        actions_payload = json.loads(raw)
    except Exception as e:
        print(f"[Orchestrator] JSON parse failed: {e}. Raw: {res.content[:200]}", flush=True)
        actions_payload = {
            "decision_id": str(uuid.uuid4()),
            "session_id": "fallback",
            "audit_id": str(uuid.uuid4()),
            "actions": [{
                "type": "query_rag",
                "idempotency_key": str(uuid.uuid4())[:8],
                "payload": {"query_text": state.get("user_query", "help"), "k": 3}
            }]
        }
        
    current_metadata = dict(state.get("metadata", {"invoked_agents": []}))
    invoked = list(current_metadata.get("invoked_agents", []))
    invoked.append("master_orchestrator")
    current_metadata["invoked_agents"] = invoked
    
    return {"actions_payload": actions_payload, "metadata": current_metadata}

def route_actions(state: AgentState) -> List[str]:
    """Routes to appropriate sub-agents based on the Orchestrator's action payload."""
    actions_payload = state.get("actions_payload")
    if actions_payload is None:
        return ["ResponseNode"]
    
    actions = actions_payload.get("actions", [])
    routes = set()
    
    for a in actions:
        action_type = a.get("type")
        if action_type == "query_rag":
            routes.add("RetrieverNode")
        elif action_type == "schedule_meeting" or action_type == "fetch_calendar":
            routes.add("SchedulerNode")
        elif action_type == "create_task":
            routes.add("TaskNode")
        elif action_type == "send_notification" or action_type == "fetch_notifications":
            routes.add("NotifyNode")
            
    if not routes:
        return ["ResponseNode"]
        
    return list(routes)

async def response_node(state: AgentState) -> dict:
    """Synthesizes all sub-agent outputs into a single conversational reply."""
    llm = ChatVertexAI(model_name="gemini-2.5-pro", temperature=0.7)
    
    tool_results = "\n".join([
        msg.content for msg in state.get("messages", []) 
        if hasattr(msg, "content") and msg.content
    ])
    
    if not tool_results.strip():
        tool_results = "No sub-agents were invoked. The user asked a general question."
    
    combined_prompt = f"You are TaskNinja, a friendly AI productivity assistant. Based on the sub-agent execution traces below, give the user a clear, concise summary of what was accomplished. If no tools ran, answer the user's question directly and helpfully.\n\nSub-Agent Traces:\n{tool_results}\n\nUSER QUESTION: {state.get('user_query', '')}"
    
    final_res = await llm.ainvoke(combined_prompt)
    
    current_metadata = dict(state.get("metadata", {"invoked_agents": []}))
    invoked = list(current_metadata.get("invoked_agents", []))
    invoked.append("response_node")
    current_metadata["invoked_agents"] = invoked
    
    return {"messages": [AIMessage(content=final_res.content)], "metadata": current_metadata}

async def telemetry_node(state: AgentState) -> dict:
    """Publishes execution audit to Google Cloud Pub/Sub for observability."""
    try:
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
        
        telemetry_payload = {
            "decision_id": (state.get("actions_payload") or {}).get("decision_id", "unknown"),
            "invoked_agents": (state.get("metadata") or {}).get("invoked_agents", []),
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        data = json.dumps(telemetry_payload).encode("utf-8")
        future = publisher.publish(topic_path, data)
        future.result(timeout=3.0)
        print(f"[Telemetry] Published to {TOPIC_ID}", flush=True)
    except Exception as e:
        print(f"[Telemetry] PubSub skipped: {e}", flush=True)
        
    current_metadata = dict(state.get("metadata", {"invoked_agents": []}))
    invoked = list(current_metadata.get("invoked_agents", []))
    invoked.append("telemetry_node")
    current_metadata["invoked_agents"] = invoked
    return {"metadata": current_metadata}

def compile_swarm_graph():
    """Compiles the TaskNinja LangGraph state machine."""
    graph = StateGraph(AgentState)
    
    graph.add_node("MasterOrchestrator", master_orchestrator)
    graph.add_node("RetrieverNode", retriever_node)
    graph.add_node("SchedulerNode", scheduler_node)
    graph.add_node("TaskNode", task_node)
    graph.add_node("NotifyNode", notify_node)
    graph.add_node("ResponseNode", response_node)
    graph.add_node("TelemetryNode", telemetry_node)
    
    graph.add_edge(START, "MasterOrchestrator")
    
    # Route to sub-agents OR directly to ResponseNode if no actions
    graph.add_conditional_edges(
        "MasterOrchestrator", 
        route_actions, 
        ["RetrieverNode", "SchedulerNode", "TaskNode", "NotifyNode", "ResponseNode"]
    )
    
    # All sub-agents funnel into ResponseNode
    graph.add_edge("RetrieverNode", "ResponseNode")
    graph.add_edge("SchedulerNode", "ResponseNode")
    graph.add_edge("TaskNode", "ResponseNode")
    graph.add_edge("NotifyNode", "ResponseNode")
    
    # ResponseNode → Telemetry → END
    graph.add_edge("ResponseNode", "TelemetryNode")
    graph.add_edge("TelemetryNode", END)
    
    return graph.compile()
