import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()

def get_utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = 'users'

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    budget_policy = Column(String(50), default='medium')
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

class Session(Base):
    __tablename__ = 'sessions'

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id'))
    short_context = Column(Text)
    session_summary = Column(Text)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    user = relationship("User")

class Decision(Base):
    __tablename__ = 'decisions'

    decision_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.session_id'))
    summary = Column(Text)
    model_used = Column(String(100))
    budget_policy = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    session = relationship("Session")

class Action(Base):
    __tablename__ = 'actions'

    action_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_id = Column(UUID(as_uuid=True), ForeignKey('decisions.decision_id'))
    type = Column(String(100), nullable=False)
    agent = Column(String(100), nullable=False)
    payload = Column(JSONB)
    idempotency_key = Column(String(255), unique=True, nullable=False)
    status = Column(String(50), default='pending')
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    decision = relationship("Decision")

class AuditLog(Base):
    __tablename__ = 'audit_logs'

    audit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_id = Column(UUID(as_uuid=True), ForeignKey('actions.action_id'))
    connector_name = Column(String(100))
    request_payload = Column(JSONB)
    response_payload = Column(JSONB)
    status = Column(String(50))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    action = relationship("Action")

class Document(Base):
    __tablename__ = 'documents'

    doc_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    gcs_uri = Column(String(512))
    file_type = Column(String(50))
    metadata_ = Column("metadata", JSONB)  # Workaround for 'metadata' reserved keyword
    pii_flag = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

class Embedding(Base):
    __tablename__ = 'embeddings'

    embedding_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id = Column(UUID(as_uuid=True), ForeignKey('documents.doc_id'))
    chunk_id = Column(String(255))
    text_chunk = Column(Text)
    embedding = Column(Vector(768))
    metadata_ = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

    document = relationship("Document")

class CalendarEvent(Base):
    __tablename__ = 'calendar_events'

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    summary = Column(Text, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    participants = Column(JSONB) # List of emails
    attached_docs = Column(JSONB) # List of GCS URIs or Doc IDs
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

class Notification(Base):
    __tablename__ = 'notifications'

    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(String(50), default='ui_toast')
    status = Column(String(20), default='unread')
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

class RetrievalCache(Base):
    __tablename__ = 'retrieval_cache'

    cache_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.session_id'))
    query = Column(String(255), nullable=False)
    retrievals = Column(JSONB)
    expires_at = Column(DateTime(timezone=True))

    session = relationship("Session")
