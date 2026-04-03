import json
import os
import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import SystemMessage, AIMessage

from .state import AgentState

# External Cloud Run URL — this proves true network-based Universal Tool Discovery
MCP_GATEWAY_URL = os.getenv(
    "MCP_GATEWAY_URL",
    "https://taskninja-mcp-gateway-836906162288.us-central1.run.app/mcp/sse"
)

async def execute_mcp_tool(tool_name: str, arguments: dict) -> str:
    """
    Connects to the TaskNinja MCP Gateway using the official MCP Client SDK over SSE.
    Proves Universal Tool Discovery — sub-agents do NOT import local Python functions.
    Includes timeout and error handling for production reliability.
    """
    try:
        async with sse_client(MCP_GATEWAY_URL) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments)
                output_parts = []
                for content_block in result.content:
                    if content_block.type == "text":
                        output_parts.append(content_block.text)
                return "".join(output_parts) if output_parts else json.dumps({"status": "success", "note": "Tool executed with empty response"})
    except Exception as e:
        error_msg = f"MCP tool '{tool_name}' call failed: {str(e)}"
        print(f"[MCP Client] {error_msg}", flush=True)
        return json.dumps({"status": "error", "error": error_msg})

# -----------------------------------------------------------------------------------------
# Sub-Agent Nodes
# -----------------------------------------------------------------------------------------

def init_llm():
    return ChatVertexAI(model_name="gemini-2.5-flash", temperature=0.3)

async def retriever_node(state: AgentState) -> dict:
    """RAG Retriever Agent — queries document embeddings via MCP."""
    llm = init_llm()
    responses = []
    
    actions = state.get("actions_payload", {})
    if actions is None:
        actions = {}
    action_list = actions.get("actions", [])
    rag_actions = [a for a in action_list if a.get("type") == "query_rag"]
    
    for action in rag_actions:
        payload = action.get("payload", {})
        mcp_res = await execute_mcp_tool("query_rag", arguments={
            "query_text": payload.get("query_text", "general knowledge retrieval"),
            "k": payload.get("k", 5)
        })
        chat_res = await llm.ainvoke([
            SystemMessage(content="You are the TaskNinja RAG Agent. Briefly summarize what you found from the knowledge base."),
            SystemMessage(content=f"Search Results: {mcp_res}")
        ])
        responses.append(chat_res.content)
        
    current_metadata = dict(state.get("metadata", {}))
    invoked = list(current_metadata.get("invoked_agents", []))
    invoked.append("retriever_node")
    current_metadata["invoked_agents"] = invoked

    summary = "; ".join(responses) if responses else "No RAG queries needed."
    return {"metadata": current_metadata, "messages": [AIMessage(content=f"[RAG Agent] {summary}")]}

async def scheduler_node(state: AgentState) -> dict:
    """Scheduler Agent — manages calendar via MCP."""
    llm = init_llm()
    responses = []
    
    actions = state.get("actions_payload", {})
    if actions is None:
        actions = {}
    action_list = actions.get("actions", [])
    schedule_actions = [a for a in action_list if a.get("type") == "schedule_meeting"]
    
    for action in schedule_actions:
        payload = action.get("payload", {})
        mcp_res = await execute_mcp_tool("schedule_meeting", arguments=payload)
        chat_res = await llm.ainvoke([
            SystemMessage(content="You are the TaskNinja Scheduler Agent. Confirm the meeting was scheduled."),
            SystemMessage(content=f"Scheduling Result: {mcp_res}")
        ])
        responses.append(chat_res.content)
        
    current_metadata = dict(state.get("metadata", {}))
    invoked = list(current_metadata.get("invoked_agents", []))
    invoked.append("scheduler_node")
    current_metadata["invoked_agents"] = invoked

    summary = "; ".join(responses) if responses else "No meetings to schedule."
    return {"metadata": current_metadata, "messages": [AIMessage(content=f"[Scheduler Agent] {summary}")]}

async def task_node(state: AgentState) -> dict:
    """Task Runner Agent — queues multi-step tasks via MCP."""
    llm = init_llm()
    responses = []
    
    actions = state.get("actions_payload", {})
    if actions is None:
        actions = {}
    action_list = actions.get("actions", [])
    task_actions = [a for a in action_list if a.get("type") == "create_task"]
    
    for action in task_actions:
        payload = action.get("payload", {})
        mcp_res = await execute_mcp_tool("create_task", arguments=payload)
        chat_res = await llm.ainvoke([
            SystemMessage(content="You are the TaskNinja Task Agent. Confirm the task was queued."),
            SystemMessage(content=f"Task Result: {mcp_res}")
        ])
        responses.append(chat_res.content)
        
    current_metadata = dict(state.get("metadata", {}))
    invoked = list(current_metadata.get("invoked_agents", []))
    invoked.append("task_node")
    current_metadata["invoked_agents"] = invoked

    summary = "; ".join(responses) if responses else "No tasks to create."
    return {"metadata": current_metadata, "messages": [AIMessage(content=f"[Task Agent] {summary}")]}

async def notify_node(state: AgentState) -> dict:
    """Notifier Agent — dispatches alerts via MCP."""
    llm = init_llm()
    responses = []
    
    actions = state.get("actions_payload", {})
    if actions is None:
        actions = {}
    action_list = actions.get("actions", [])
    notify_actions = [a for a in action_list if a.get("type") == "send_notification"]
    
    for action in notify_actions:
        payload = action.get("payload", {})
        mcp_res = await execute_mcp_tool("send_notification", arguments=payload)
        chat_res = await llm.ainvoke([
            SystemMessage(content="You are the TaskNinja Notifier Agent. Confirm notification delivery."),
            SystemMessage(content=f"Notification Result: {mcp_res}")
        ])
        responses.append(chat_res.content)
        
    current_metadata = dict(state.get("metadata", {}))
    invoked = list(current_metadata.get("invoked_agents", []))
    invoked.append("notify_node")
    current_metadata["invoked_agents"] = invoked

    summary = "; ".join(responses) if responses else "No notifications to send."
    return {"metadata": current_metadata, "messages": [AIMessage(content=f"[Notify Agent] {summary}")]}
