import json
from mcp import ClientSession
from mcp.client.sse import sse_client
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import SystemMessage, AIMessage

from .state import AgentState

# Const URL mapped dynamically to the deployed Cloud Run Gateway resolving MCP standard protocols
MCP_GATEWAY_URL = "https://taskninja-mcp-gateway-836906162288.us-central1.run.app/mcp/sse"

# Core dependency injection constraint handling network-first executions
async def execute_mcp_tool(tool_name: str, arguments: dict):
    """
    Connects to the TaskNinja MCP Gateway natively using Server-Sent Events (SSE).
    This executes Universal Tool Discovery without binding to local Python functions.
    """
    async with sse_client(MCP_GATEWAY_URL) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=arguments)
            # Result is usually an array of TextContents, we collapse it securely
            output_string = ""
            for out in result.content:
                if out.type == "text":
                    output_string += out.text
            return output_string

# -----------------------------------------------------------------------------------------
# Sub-Agent Nodes (Implementing the required 'gemini-2.5-flash' engine constraints)
# -----------------------------------------------------------------------------------------

def init_llm():
    return ChatVertexAI(model_name="gemini-2.5-flash")

async def retriever_node(state: AgentState) -> dict:
    """The RAG Agent processing state payload queries."""
    llm = init_llm()
    # Mocking standard LangChain execution passing contextual hints securely
    responses = []
    
    # We parse the actions_payload formulated by Orchestrator
    actions = state.get("actions_payload", {}).get("actions", [])
    rag_actions = [a for a in actions if a["type"] == "query_rag"]
    
    for action in rag_actions:
        payload = action.get("payload", {})
        # Fire it entirely disconnected, over the network
        mcp_res = await execute_mcp_tool("query_rag", arguments={"query_text": payload.get("query_text", ""), "k": payload.get("k", 5)})
        
        # Swarm LLM synthesis pass
        chat_res = await llm.ainvoke([
            SystemMessage(content="You are the TaskNinja RAG Agent. Summarize the tool response neutrally."),
            SystemMessage(content=f"Tool Output: {mcp_res}")
        ])
        responses.append(chat_res.content)
        
    # Append execution metadata securely
    current_metadata = state.get("metadata", {})
    invoked = current_metadata.get("invoked_agents", [])
    invoked.append("retriever_node")
    current_metadata["invoked_agents"] = invoked

    return {"metadata": current_metadata, "messages": [AIMessage(content=f"Retriever Agent complete: {responses}")]}

async def scheduler_node(state: AgentState) -> dict:
    """Agent bridging Calendar Tooling payloads natively."""
    llm = init_llm()
    actions = state.get("actions_payload", {}).get("actions", [])
    schedule_actions = [a for a in actions if a["type"] == "schedule_meeting"]
    
    responses = []
    for action in schedule_actions:
        payload = action.get("payload", {})
        # Route strictly to MCP Cloud Run URI Wrapper
        mcp_res = await execute_mcp_tool("schedule_meeting", arguments=payload)
        
        chat_res = await llm.ainvoke([
            SystemMessage(content="You are the TaskNinja Scheduler Agent. Confirm meeting creation concisely based on context."),
            SystemMessage(content=f"Tool Context: {mcp_res}")
        ])
        responses.append(chat_res.content)
        
    current_metadata = state.get("metadata", {})
    invoked = current_metadata.get("invoked_agents", [])
    invoked.append("scheduler_node")
    current_metadata["invoked_agents"] = invoked

    return {"metadata": current_metadata, "messages": [AIMessage(content=f"Scheduler Agent complete: {responses}")]}

async def task_node(state: AgentState) -> dict:
    """Agent manipulating the Multi-Step queueing logic."""
    llm = init_llm()
    actions = state.get("actions_payload", {}).get("actions", [])
    task_actions = [a for a in actions if a["type"] == "create_task"]
    
    responses = []
    for action in task_actions:
        payload = action.get("payload", {})
        mcp_res = await execute_mcp_tool("create_task", arguments=payload)
        
        chat_res = await llm.ainvoke([
            SystemMessage(content="You are the TaskNinja Task Agent. Interpret queue confirmation."),
            SystemMessage(content=f"Tool Context: {mcp_res}")
        ])
        responses.append(chat_res.content)
        
    current_metadata = state.get("metadata", {})
    invoked = current_metadata.get("invoked_agents", [])
    invoked.append("task_node")
    current_metadata["invoked_agents"] = invoked

    return {"metadata": current_metadata, "messages": [AIMessage(content=f"Task Agent complete: {responses}")]}

async def notify_node(state: AgentState) -> dict:
    """Agent processing outgoing broadcasts."""
    llm = init_llm()
    actions = state.get("actions_payload", {}).get("actions", [])
    notify_actions = [a for a in actions if a["type"] == "send_notification"]
    
    responses = []
    for action in notify_actions:
        payload = action.get("payload", {})
        mcp_res = await execute_mcp_tool("send_notification", arguments=payload)
        
        chat_res = await llm.ainvoke([
            SystemMessage(content="You are the TaskNinja Notify Agent. Validate broadcast success."),
            SystemMessage(content=f"Tool Context: {mcp_res}")
        ])
        responses.append(chat_res.content)
        
    current_metadata = state.get("metadata", {})
    invoked = current_metadata.get("invoked_agents", [])
    invoked.append("notify_node")
    current_metadata["invoked_agents"] = invoked

    return {"metadata": current_metadata, "messages": [AIMessage(content=f"Notify Agent complete: {responses}")]}
