import uuid
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Session, Decision, Action, AuditLog

async def initialize_session(db: AsyncSession, user_id: uuid.UUID, short_context: Optional[str] = None) -> Session:
    """Initializes a new session for a user."""
    new_session = Session(
        user_id=user_id,
        short_context=short_context
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session

async def initialize_decision(
    db: AsyncSession, 
    session_id: uuid.UUID, 
    summary: str, 
    model_used: str, 
    budget_policy: str
) -> Decision:
    """Initializes a new decision linked to a session."""
    new_decision = Decision(
        session_id=session_id,
        summary=summary,
        model_used=model_used,
        budget_policy=budget_policy
    )
    db.add(new_decision)
    await db.commit()
    await db.refresh(new_decision)
    return new_decision

async def log_action(
    db: AsyncSession, 
    decision_id: uuid.UUID, 
    action_type: str, 
    agent: str, 
    payload: Dict[str, Any], 
    idempotency_key: str
) -> Action:
    """
    Logs an action to be executed by a sub-agent.
    Ensures idempotency_key is uniquely recorded to prevent duplicate execution.
    """
    new_action = Action(
        decision_id=decision_id,
        type=action_type,
        agent=agent,
        payload=payload,
        idempotency_key=idempotency_key,
        status='pending'
    )
    db.add(new_action)
    await db.commit()
    await db.refresh(new_action)
    return new_action

async def write_audit_log(
    db: AsyncSession,
    action_id: uuid.UUID,
    connector_name: str,
    request_payload: Optional[Dict[str, Any]] = None,
    response_payload: Optional[Dict[str, Any]] = None,
    status: str = 'success',
    error_message: Optional[str] = None
) -> AuditLog:
    """Writes to the audit_logs table for traceability after action completion."""
    new_audit_log = AuditLog(
        action_id=action_id,
        connector_name=connector_name,
        request_payload=request_payload,
        response_payload=response_payload,
        status=status,
        error_message=error_message
    )
    db.add(new_audit_log)
    await db.commit()
    await db.refresh(new_audit_log)
    return new_audit_log
