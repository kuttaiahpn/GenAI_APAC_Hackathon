import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check_connectivity():
    print("🚀 TaskNinja Intelligence Diagnostic Tooling")
    print("-" * 40)
    
    # 1. AlloyDB Check
    db_host = os.getenv("DB_HOST", "10.34.0.8")
    db_pass = os.getenv("DB_PASSWORD", "password")
    db_user = os.getenv("DB_USER", "postgres")
    db_name = os.getenv("DB_NAME", "taskninja")
    
    db_url = f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:5432/{db_name}?ssl=disable"
    
    print(f"📡 Testing Database Bridge: {db_host}...")
    try:
        # Standardize URL construction to prevent hidden parsing errors
        db_url = f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:5432/{db_name}?ssl=disable"
        engine = create_async_engine(db_url, connect_args={"command_timeout": 5})
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ [ALLOYDB] Connection Successful! The bridge is open.")
    except Exception as e:
        print(f"🔴 [ALLOYDB] FAILED: {type(e).__name__} - {str(e)}")
        if "Timeout" in str(e) or "ETIMEDOUT" in str(e):
            print("💡 TIP: Cloushell cannot see the private IP (10.34.0.8). Ensure you are using VPC Peering or rely on Cloud Run's Direct VPC Egress for testing.")
        elif "password" in str(e).lower():
            print("💡 TIP: authentication failed. Check your DB_PASSWORD env var.")
        else:
            print(f"💡 TIP: Unexpected error. Path to 10.34.0.8 might be blocked by firewall rules.")

    # 2. Vertex AI Check
    print("\n🧠 Testing Intelligence Access: Vertex AI...")
    try:
        import vertexai
        from vertexai.language_models import TextEmbeddingModel
        project = os.getenv("GOOGLE_CLOUD_PROJECT", "track3codelabs")
        vertexai.init(project=project, location="us-central1")
        TextEmbeddingModel.from_pretrained("text-embedding-004")
        print("✅ [VERTEX AI] Authentication Successful! Intelligence is online.")
    except Exception as e:
        print(f"🔴 [VERTEX AI] FAILED: {e}")
        print("💡 TIP: Ensure your project-id is correct or check IAM permissions.")

    print("-" * 40)
    print("🏆 If both checkmarks are Green, your system is ready for the FINAL COMMIT!")

if __name__ == "__main__":
    asyncio.run(check_connectivity())
