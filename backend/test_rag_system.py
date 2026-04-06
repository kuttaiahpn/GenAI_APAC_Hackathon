import asyncio
import uuid
import sys
from backend.orchestrator import compile_swarm_graph

async def test_rag_flow(query: str):
    print(f"--- TaskNinja RAG Test ---")
    print(f"Query: {query}")
    print("-" * 30)

    # Compile the Master Swarm Graph
    graph = compile_swarm_graph()
    
    # Configuration for LangGraph (thread_id for memory)
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    
    # Initial state
    initial_state = {
        "user_query": query,
        "messages": [],
        "session_summary": "Testing RAG Integration with Hackathon.txt",
        "rag_context": [],
        "schedule_context": [],
        "active_tasks": [],
        "metadata": {"invoked_agents": []}
    }

    try:
        print("Invoking Orchestrator Swarm...")
        # Note: This requires the MCP Gateway to be running at http://localhost:8000/mcp/sse
        result = await graph.ainvoke(initial_state, config)
        
        print("\n--- Execution Trace ---")
        invoked = result.get("metadata", {}).get("invoked_agents", [])
        print(f"Agents Invoked: { ' -> '.join(invoked) }")
        
        msgs = result.get("messages", [])
        if msgs:
            print(f"\nFinal Response:\n{msgs[-1].content}")
        else:
            print("\nNo response generated.")
            
    except Exception as e:
        print(f"\n[ERROR] Flow failed: {e}")
        print("\nTip: Make sure the MCP Gateway is running in another terminal:")
        print("export DB_HOST=127.0.0.1 && export DB_PASSWORD=your_password")
        print("python3 -m uvicorn backend.mcp_server:app --reload")

if __name__ == "__main__":
    query = "What are the rules and objectives of the hackathon described in the documents?"
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    
    asyncio.run(test_rag_flow(query))
