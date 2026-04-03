import json
import os
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi import FastAPI, Depends, Request, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import mcp.server.sse
from mcp.server import Server
from mcp.types import Tool, TextContent

# Local Application Imports
from .database import AsyncSessionFactory, engine, init_extensions
from .models import Base
from .tools import (
    RAGQueryInput, MeetingScheduleInput, CalendarFetchInput, 
    CreateTaskInput, NotificationInput, CreateDecisionLogInput,
    query_rag_tool, schedule_meeting_tool, fetch_calendar_tool,
    create_task_tool, send_notification_tool, create_decision_log_tool
)
from .orchestrator import compile_swarm_graph

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes the database schema and pgvector extensions automatically on Cloud Run boot."""
    try:
        await init_extensions()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Successfully initialized AlloyDB Schema and pgvector extensions.", flush=True)
    except Exception as e:
        print(f"Schema initialization warning: {e}", flush=True)
    yield
    # Cleanup logic (if any) could go here

# Initialize FastAPI App
app = FastAPI(
    title="TaskNinja MCP Gateway", 
    version="1.0.0", 
    description="Gateway servicing RESTful endpoints and MCP SSE integrations.",
    lifespan=lifespan
)

API_KEY = os.getenv("API_KEY", "hackathon_default_key")

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

async def get_db():
    """Dependency injection to provide SQLAlchemy async sessions to our endpoints."""
    async with AsyncSessionFactory() as session:
        yield session

# ==============================================================================
# RESTful Tool Endpoints (Direct Integration)
# ==============================================================================

@app.post("/v1/tools/query_rag")
async def post_query_rag(input_data: RAGQueryInput, db: AsyncSession = Depends(get_db)):
    return await query_rag_tool(input_data, db)

@app.post("/v1/tools/schedule_meeting")
async def post_schedule_meeting(input_data: MeetingScheduleInput):
    return await schedule_meeting_tool(input_data)

@app.post("/v1/tools/fetch_calendar")
async def post_fetch_calendar(input_data: CalendarFetchInput):
    return await fetch_calendar_tool(input_data)

@app.post("/v1/tools/create_task")
async def post_create_task(input_data: CreateTaskInput, db: AsyncSession = Depends(get_db)):
    return await create_task_tool(input_data, db)

@app.post("/v1/tools/send_notification")
async def post_send_notification(input_data: NotificationInput):
    return await send_notification_tool(input_data)

@app.post("/v1/tools/create_decision_log")
async def post_create_decision_log(input_data: CreateDecisionLogInput, db: AsyncSession = Depends(get_db)):
    return await create_decision_log_tool(input_data, db)

# ==============================================================================
# The Overarching Intelligence Bridge (Orchestrator Routing)
# ==============================================================================

class OrchestrateInput(BaseModel):
    query: str
    thread_id: str

@app.post("/v1/orchestrate")
async def post_orchestrate(payload: OrchestrateInput, authorized: bool = Depends(verify_api_key)):
    """Triggers the Master LangGraph Swarm securely."""
    graph = compile_swarm_graph()
    
    # LangGraph state configurations mapping conversational memory constraints
    config = {"configurable": {"thread_id": payload.thread_id}}
    
    # Seed the initial architecture state cleanly
    initial_state = {
        "user_query": payload.query,
        "messages": [],
        "session_summary": "Active Sprint Session",
        "rag_context": [],
        "schedule_context": [],
        "active_tasks": [],
        "metadata": {"invoked_agents": []}
    }
    
    # Fire the intelligence compilation natively yielding all intermediate routes sequentially
    result = await graph.ainvoke(initial_state, config)
    
    msgs = result.get("messages", [])
    final_message = msgs[-1].content if msgs else "Swarm completed execution loop without yielding final response traces."
    
    return {
        "response": final_message,
        "metadata": {
            "decision_id": result.get("actions_payload", {}).get("decision_id", "unknown"),
            "invoked_agents": result.get("metadata", {}).get("invoked_agents", [])
        }
    }

# ==============================================================================
# Model Context Protocol (MCP) Server Configuration (SSE Transport)
# ==============================================================================

mcp_server = Server("TaskNinja MCP Hub")

@mcp_server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Exposes precise Pydantic schemas over MCP protocol."""
    return [
        Tool(
            name="query_rag",
            description="Executes a vector similarity search across the Document Embeddings database.",
            inputSchema=RAGQueryInput.model_json_schema()
        ),
        Tool(
            name="schedule_meeting",
            description="Provisions a new meeting block on the Calendar API.",
            inputSchema=MeetingScheduleInput.model_json_schema()
        ),
        Tool(
            name="create_task",
            description="Queues a multi-step execution block.",
            inputSchema=CreateTaskInput.model_json_schema()
        ),
        Tool(
            name="send_notification",
            description="Dispatches targeted alerts via configured channels.",
            inputSchema=NotificationInput.model_json_schema()
        )
    ]

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Routes execution payloads triggered dynamically by the LLM."""
    try:
        # Isolated DB context for MCP Tool invocation
        async with AsyncSessionFactory() as db:
            result = None
            if name == "query_rag":
                # Validate argument payload automatically
                payload = RAGQueryInput(**arguments)
                res = await query_rag_tool(payload, db)
                result = json.dumps(res)
                
            elif name == "schedule_meeting":
                payload = MeetingScheduleInput(**arguments)
                res = await schedule_meeting_tool(payload)
                result = json.dumps(res)
                
            elif name == "create_task":
                payload = CreateTaskInput(**arguments)
                res = await create_task_tool(payload, db)
                result = json.dumps(res)
                
            elif name == "send_notification":
                payload = NotificationInput(**arguments)
                res = await send_notification_tool(payload)
                result = json.dumps(res)
            else:
                raise ValueError(f"Unknown MCP tool registration invoked: {name}")

            return [TextContent(type="text", text=result)]
    except Exception as e:
        # Prevent crash returning robust text error
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


# Hook up the specific transport router objects for SSE streaming
sse = mcp.server.sse.SseServerTransport("/mcp/messages")

@app.get("/mcp/sse")
async def mcp_sse_endpoint(request: Request):
    """Initializing handshake endpoint utilized by an MCP-compatible LLM"""
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await mcp_server.run(streams[0], streams[1], mcp_server.create_initialization_options())

@app.post("/mcp/messages")
async def mcp_messages_endpoint(request: Request):
    """Post routing endpoint where JSON-RPC calls are fed"""
    await sse.handle_post_message(request.scope, request.receive, request._send)

# Default entry
@app.get("/")
async def root():
    return {"message": "TaskNinja MCP Gateway Online. Attach to /mcp/sse for protocol binding, or POST to /v1/tools."}
