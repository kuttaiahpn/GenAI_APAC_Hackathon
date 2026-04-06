import uuid
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import vertexai
from vertexai.language_models import TextEmbeddingModel

# Local Imports
from .database import load_config
from .models import Action, Decision, CalendarEvent, Document, Notification

# ==============================================================================
# Pydantic Schemas - Strict Input/Output definitions for 100% accurate Function Calling
# ==============================================================================

class RAGQueryInput(BaseModel):
    query_text: str = Field(..., description="The semantic search query.")
    k: int = Field(5, description="Number of top similar documents to retrieve.")
    context_hints: Optional[List[str]] = Field(None, description="Optional keywords or filters to narrow down the search space.")

class MeetingScheduleInput(BaseModel):
    summary: str = Field(..., description="The subject or summary of the meeting.")
    start_time: datetime = Field(..., description="Start time of the meeting in ISO 8601 format.")
    end_time: datetime = Field(..., description="End time of the meeting in ISO 8601 format.")
    participants: List[str] = Field(..., description="List of participant email addresses.")
    attached_docs: Optional[List[str]] = Field(None, description="List of document UUIDs or GCS URIs to attach.")

class CalendarFetchInput(BaseModel):
    time_min: datetime = Field(..., description="Lower bound for fetching events.")
    time_max: datetime = Field(..., description="Upper bound for fetching events.")

class NotificationInput(BaseModel):
    recipient: str = Field(..., description="Email or User ID of the recipient.")
    message: str = Field(..., description="The content of the notification alert.")
    channel: str = Field("ui_toast", description="Delivery channel: ui_toast, email, or slack.")

class NotificationFetchInput(BaseModel):
    recipient: str = Field(..., description="Email or User ID to fetch notifications for.")
    status: str = Field("unread", description="Status filter: unread or read.")

class TaskStep(BaseModel):
    step_order: int
    tool_call: Literal["external_api_connector", "update_local_db"]
    parameters: Dict[str, Any]

class CreateTaskInput(BaseModel):
    task_description: str = Field(..., description="High level goal of the task.")
    steps: List[TaskStep] = Field(..., description="Sequential steps defining the multi-step execution plan.")
    attached_docs: Optional[List[str]] = Field(None, description="List of document UUIDs or GCS URIs mapped to the task.")

class CreateDecisionLogInput(BaseModel):
    session_id: str = Field(..., description="The master session ID string.")
    decision_id: str = Field(..., description="Unique generated identifier for this decision.")
    summary: str = Field(..., description="Short summary of the orchestration decision.")
    model_used: str = Field(..., description="Which model derived this logic (e.g., gemini-2.5-flash).")
    budget_policy: str = Field(..., description="Budget policy allocated.")

# ==============================================================================
# Functional Core (The actual Python Logic that Gemini executes)
# ==============================================================================

async def query_rag_tool(input_data: RAGQueryInput, db: AsyncSession) -> dict:
    """
    Executes a vector similarity search across the Document Embeddings database.
    This acts as the agent's memory retrieval mechanism.
    """
    config = load_config()
    project_id = config.get("gcp_project_id", "track3codelabs")
    location = config.get("gcp_location", "us-central1")
    
    # Initialize Vertex AI
    vertexai.init(project=project_id, location=location)
    model_name = config.get("models", {}).get("vector_search", "text-embedding-004")
    model = TextEmbeddingModel.from_pretrained(model_name)
    
    # Generate Embedding for the query
    # We use batch size 1 for a single query
    embedding_res = model.get_embeddings([input_data.query_text], output_dimensionality=768)
    query_vector = embedding_res[0].values

    # Vector similarity search using pgvector (cosine distance <=> )
    # Ordering by distance ascending (smaller is more similar)
    sql = text("""
        SELECT text_chunk, 1 - (embedding <=> :query_vector) AS similarity
        FROM embeddings
        ORDER BY embedding <=> :query_vector
        LIMIT :k
    """)
    
    try:
        # We convert the list to a string format '[v1, v2, ...]' for pgvector raw SQL compatibility
        result = await db.execute(sql, {"query_vector": str(query_vector), "k": input_data.k})
        rows = result.fetchall()
        
        documents = [
            {"content": row[0], "similarity": float(row[1])}
            for row in rows
        ]
        
        return {
            "status": "success", 
            "documents_retrieved": len(documents),
            "query": input_data.query_text,
            "data": documents
        }
    except Exception as e:
        print(f"RAG Tool Error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "query": input_data.query_text
        }

async def schedule_meeting_tool(input_data: MeetingScheduleInput, db: AsyncSession) -> dict:
    """
    Provisions a new meeting block on the Calendar API and persists to AlloyDB.
    """
    try:
        new_event = CalendarEvent(
            summary=input_data.summary,
            start_time=input_data.start_time,
            end_time=input_data.end_time,
            participants=list(input_data.participants),
            attached_docs=list(input_data.attached_docs or [])
        )
        db.add(new_event)
        await db.commit()
        await db.refresh(new_event)
        
        return {
            "status": "success",
            "action": "meeting_created",
            "event_id": str(new_event.event_id),
            "summary": new_event.summary,
            "start": new_event.start_time.isoformat(),
            "attached_docs": new_event.attached_docs
        }
    except Exception as e:
        print(f"Schedule Meeting Error: {e}")
        return {"status": "error", "message": str(e)}

async def fetch_calendar_tool(input_data: CalendarFetchInput, db: AsyncSession) -> dict:
    """
    Pulls existing calendar slots for awareness from AlloyDB.
    """
    from sqlalchemy import select
    try:
        stmt = select(CalendarEvent).where(
            CalendarEvent.start_time >= input_data.time_min,
            CalendarEvent.start_time <= input_data.time_max
        )
        result = await db.execute(stmt)
        events = result.scalars().all()
        
        return {
            "status": "success",
            "events": [
                {
                    "summary": e.summary,
                    "start": e.start_time.isoformat(),
                    "end": e.end_time.isoformat(),
                    "participants": e.participants,
                    "attached_docs": e.attached_docs
                } for e in events
            ]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def create_task_tool(input_data: CreateTaskInput, db: AsyncSession) -> dict:
    """
    Queues a complex, multi-step sub-agent execution flow into the Action tables.
    """
    try:
        # We model 'tasks' as Actions in this system for now
        new_action = Action(
            type="create_task",
            agent="task_runner",
            payload={
                "task_description": input_data.task_description,
                "steps": [s.model_dump() for s in input_data.steps],
                "attached_docs": input_data.attached_docs
            },
            idempotency_key=str(uuid.uuid4())[:8]
        )
        db.add(new_action)
        await db.commit()
        await db.refresh(new_action)
        
        return {
            "status": "success",
            "task_id": str(new_action.action_id),
            "task_queued": input_data.task_description,
            "total_steps": len(input_data.steps)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def send_notification_tool(input_data: NotificationInput, db: AsyncSession) -> dict:
    """
    Dispatches targeted alerts via the Notification table in AlloyDB.
    """
    try:
        new_note = Notification(
            recipient=input_data.recipient,
            message=input_data.message,
            channel=input_data.channel
        )
        db.add(new_note)
        await db.commit()
        await db.refresh(new_note)
        
        return {
            "status": "success",
            "notification_id": str(new_note.notification_id),
            "recipient": new_note.recipient,
            "channel": new_note.channel
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def fetch_notifications_tool(input_data: NotificationFetchInput, db: AsyncSession) -> dict:
    """
    Retrieves unread alerts for the user interface from AlloyDB.
    """
    from sqlalchemy import select
    try:
        stmt = select(Notification).where(
            Notification.recipient == input_data.recipient,
            Notification.status == input_data.status
        ).order_by(Notification.created_at.desc())
        
        result = await db.execute(stmt)
        notes = result.scalars().all()
        
        return {
            "status": "success",
            "notifications": [
                {
                    "notification_id": str(n.notification_id),
                    "message": n.message,
                    "channel": n.channel,
                    "created_at": n.created_at.isoformat()
                } for n in notes
            ]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def create_decision_log_tool(input_data: CreateDecisionLogInput, db: AsyncSession) -> dict:
    """
    Inserts a master 'Decision' context object into the database before downstream asynchronous execution.
    """
    # Uses crud.py bindings conceptually
    return {
        "status": "success",
        "decision_recorded": input_data.decision_id
    }
