import json
import uuid
import datetime
from typing import List
from langgraph.graph import StateGraph, END, START
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from google.cloud import pubsub_v1

# Local dependencies ensuring proper typing execution
from .state import AgentState
from .nodes import retriever_node, scheduler_node, task_node, notify_node

PROJECT_ID = "track3codelabs"
TOPIC_ID = "taskninja-events"

def get_master_prompt() -> str:
    """Reads our core Intelligence logic constraints natively."""
    try:
        with open("documents/Context Docs/prompt_library.md", "r") as f:
            return f.read()
    except Exception:
        return "You are a helpful multi-agent orchestrator. Output JSON matching the schema."

async def master_orchestrator(state: AgentState) -> dict:
    """
    The Core brain. Reaches into Google Vertex AI Gemini 2.5 Flash.
    Formats contextual state and instructs payload generation.
    """
    llm = ChatVertexAI(model_name="gemini-2.5-flash", temperature=0.1)
    sys_prompt = get_master_prompt()
    
    # Map TypedDict directly to structured text context mapping
    user_q = state.get("user_query", "")
    session_summary = state.get("session_summary", "")
    rag = str(state.get("rag_context", []))
    sched = str(state.get("schedule_context", []))
    tasks = str(state.get("active_tasks", []))
    
    context_str = f"""
    - USER QUERY: {user_q}
    - CURRENT_SESSION_SUMMARY: {session_summary}
    - RELEVANT_RAG_CONTEXT: {rag}
    - CURRENT_SCHEDULE: {sched}
    - RELEVANT_ACTIVE_TASKS: {tasks}
    """
    
    # Force invocation
    res = await llm.ainvoke([
        SystemMessage(content=sys_prompt),
        HumanMessage(content=context_str)
    ])
    
    # Safely extract strictly generated JSON skipping markdown injection blocks
    try:
        raw_output = res.content.replace("```json", "").replace("```", "").strip()
        actions_payload = json.loads(raw_output)
    except Exception as e:
        print(f"[Orchestrator] Warning: Fallback payload generation activated. Exception: {e}")
        actions_payload = {
            "decision_id": str(uuid.uuid4()),
            "session_id": "fallback",
            "audit_id": str(uuid.uuid4()),
            "actions": []
        }
        
    # Append Metadata requirement
    current_metadata = state.get("metadata", {"invoked_agents": []})
    invoked = current_metadata.get("invoked_agents", [])
    invoked.append("master_orchestrator")
    current_metadata["invoked_agents"] = invoked
    
    return {"actions_payload": actions_payload, "metadata": current_metadata}

def route_actions(state: AgentState) -> List[str]:
    """
    Reads the Master mapping instructions and fans-out dynamically to sub-agents.
    LangGraph supports returning lists for native parallel conditional execution.
    """
    actions = state.get("actions_payload", {}).get("actions", [])
    routes = []
    
    for a in actions:
        action_type = a.get("type")
        if action_type == "query_rag":
            routes.append("RetrieverNode")
        elif action_type == "schedule_meeting":
            routes.append("SchedulerNode")
        elif action_type == "create_task":
            routes.append("TaskNode")
        elif action_type == "send_notification":
            routes.append("NotifyNode")
            
    # Remove duplicate invokes natively ensuring smooth traversal
    unique_routes = list(set(routes))
    
    # If the LLM generated no explicit tool paths, we shortcut instantly to Telemetry
    if not unique_routes:
        return ["TelemetryNode"]
        
    return unique_routes

async def telemetry_node(state: AgentState) -> dict:
    """
    The final "Cloud Native" footprint mapping audit payloads across Google Pub/Sub seamlessly.
    Doesn't interrupt core execution logic loop but secures final tracing natively!
    """
    try:
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
        
        telemetry_payload = {
            "decision_id": state.get("actions_payload", {}).get("decision_id", "unknown"),
            "metadata_invocations": state.get("metadata", {}).get("invoked_agents", []),
            "timestamp": str(datetime.datetime.now())
        }
        
        data_str = json.dumps(telemetry_payload)
        data = data_str.encode("utf-8")
        
        # Publish asynchronously natively
        future = publisher.publish(topic_path, data)
        # Attempt to wait for confirmation, skipping rapidly if environment lacks ADC context
        future.result(timeout=2.0) 
        
    except Exception as e:
        print(f"[Telemetry Node] PubSub Execution Skipped gracefully. (Local Demo Expected). Reason: {e}")
        
    # Mark execution chain safely
    current_metadata = state.get("metadata", {"invoked_agents": []})
    current_metadata["invoked_agents"].append("telemetry_node")
    return {"metadata": current_metadata}

async def response_node(state: AgentState) -> dict:
    """Consolidates tool output traces into a conversational AI reply for the user."""
    llm = ChatVertexAI(model_name="gemini-2.5-flash", temperature=0.7)
    
    # Bundle the tool payload outputs from the messages array securely
    tool_results = "\n".join([msg.content for msg in state.get("messages", []) if getattr(msg, "content", "")])
    
    final_res = await llm.ainvoke([
        SystemMessage(content="You are TaskNinja. Summarize what you successfully completed to the user based on the tool trace logs below. Keep it friendly and concise."),
        SystemMessage(content=f"Sub-Agent Traces: {tool_results}"),
        HumanMessage(content=state.get("user_query", ""))
    ])
    
    current_metadata = state.get("metadata", {"invoked_agents": []})
    current_metadata["invoked_agents"].append("response_node")
    
    return {"messages": [AIMessage(content=final_res.content)], "metadata": current_metadata}

def compile_swarm_graph():
    """Compiles the primary TaskNinja Intelligence Graph binding orchestration tightly."""
    graph = StateGraph(AgentState)
    
    # Declare primary architecture components natively
    graph.add_node("MasterOrchestrator", master_orchestrator)
    graph.add_node("RetrieverNode", retriever_node)
    graph.add_node("SchedulerNode", scheduler_node)
    graph.add_node("TaskNode", task_node)
    graph.add_node("NotifyNode", notify_node)
    graph.add_node("ResponseNode", response_node)
    graph.add_node("TelemetryNode", telemetry_node)
    
    # Anchor the start
    graph.add_edge(START, "MasterOrchestrator")
    
    # Branching decision dynamically invoking Node routing fans
    graph.add_conditional_edges(
        "MasterOrchestrator", 
        route_actions, 
        ["RetrieverNode", "SchedulerNode", "TaskNode", "NotifyNode", "TelemetryNode"]
    )
    
    # Enforce funnel bridging natively to the conversational text generator
    graph.add_edge("RetrieverNode", "ResponseNode")
    graph.add_edge("SchedulerNode", "ResponseNode")
    graph.add_edge("TaskNode", "ResponseNode")
    graph.add_edge("NotifyNode", "ResponseNode")
    
    # Then route the finalized response payload trace over the PubSub loop ensuring traceability
    graph.add_edge("ResponseNode", "TelemetryNode")
    
    # Exhaust execution loop securely
    graph.add_edge("TelemetryNode", END)
    
    return graph.compile()
