import asyncio
import os
import vertexai
from vertexai.language_models import TextEmbeddingModel
from sqlalchemy import text

# Import our local components
from .database import AsyncSessionFactory, engine
from .ingest import load_config

async def check_db():
    print("[DB] Attempting to connect to the database...")
    try:
        async with AsyncSessionFactory() as session:
            # Simple health check query
            result = await session.execute(text("SELECT 1"))
            row = result.scalar()
            if row == 1:
                print(f"[DB] SUCCESS: Connected to database at {engine.url.host}:{engine.url.port}")
            else:
                print(f"[DB] UNEXPECTED: Connected, but got result: {row}")
    except Exception as e:
        print(f"[DB] FAILED: Could not connect to database at {engine.url.host}.")
        print(f"     Reason: {e}")
        print("     (Note: If you are using a Private IP like 10.x.x.x for your AlloyDB cluster, you cannot connect from your local IDE without a VPN or Auth Proxy.)\n")

async def check_vertex():
    print("[Vertex AI] Attempting to initialize Vertex API...")
    try:
        config = load_config()
        project_id = config.get("gcp_project_id")
        location = config.get("gcp_location", "us-central1")
        
        if not project_id:
            print("[Vertex AI] FAILED: Could not find gcp_project_id in config.yaml")
            return
            
        print(f"[Vertex AI] Initializing client for project: {project_id}")
        vertexai.init(project=project_id, location=location)
        
        model_name = config.get("models", {}).get("vector_search", "text-embedding-004")
        embedding_model = TextEmbeddingModel.from_pretrained(model_name)
        
        print(f"[Vertex AI] Requesting test embeddings from {model_name}...")
        embedding_res = embedding_model.get_embeddings(["health check"])
        vec = embedding_res[0].values
        print(f"[Vertex AI] SUCCESS: Generated embedding array of {len(vec)} dimensions.")
    except Exception as e:
        print(f"[Vertex AI] FAILED: Could not complete API request.")
        print(f"     Reason: {e}")
        print("     (Note: Double check that 'gcloud auth application-default login' was executed in your environment.)\n")

async def main():
    print("================================")
    print("   PHASE 1 HEALTH CHECK TOOL    ")
    print("================================\n")
    
    await check_db()
    print("-" * 32)
    await check_vertex()
    
    print("================================")

if __name__ == "__main__":
    asyncio.run(main())
