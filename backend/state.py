import operator
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    The canonical state object passed between nodes in the TaskNinja LangGraph swarm.
    Mappings align with the inputs injected via Streamlit / UI and context provided to Gemini.
    """
    # Conversation History tracking through LangChain BaseMessage objects
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Core User Intent
    user_query: str
    
    # State vectors mapped from Phase 1 dependencies
    session_summary: str
    rag_context: List[Dict[str, Any]]
    schedule_context: List[Dict[str, Any]]
    active_tasks: List[Dict[str, Any]]
    
    # Payload output populated by the Orchestrator
    actions_payload: Optional[Dict[str, Any]]
    
    # Hackathon requirement: Metadata dictionary tracking which sub-agents were invoked during a run
    metadata: Dict[str, Any]
