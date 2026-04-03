import asyncio
import sys
import os
from backend.database import engine, init_extensions
from backend.models import Base

async def run_init():
    """
    Standalone initialization script to physically create AlloyDB tables and extensions.
    Run this from the project root in Google Cloud Shell.
    """
    print("========================================")
    print("   TASKNINJA ALLOYDB INITIALIZER       ")
    print("========================================\n")
    
    # Validation check for DB_PASSWORD
    if not os.getenv("DB_PASSWORD"):
        print("[ERROR] DB_PASSWORD environment variable is not set.")
        print("Please run: export DB_PASSWORD='your_alloydb_password'")
        sys.exit(1)

    try:
        print(f"Connecting to AlloyDB at {engine.url.host}...")
        
        # 1. Initialize extensions (pgvector and uuid-ossp)
        await init_extensions()
        print("✅ [1/2] Extensions 'vector' and 'uuid-ossp' initialized.")

        # 2. Create all tables defined in models.py
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ [2/2] All schema tables created successfully.")
        
        print("\n[SUCCESS] Database initialization complete!")
        print("Tables created: users, sessions, decisions, actions, audit_logs, documents, embeddings.")
        
    except Exception as e:
        print(f"\n❌ [ERROR] Database initialization failed: {e}")
        print("\nTip: Ensure you are running this from Google Cloud Shell and that your Cloud Shell ")
        print("is authorized to reach the AlloyDB Private IP (10.34.0.8).")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_init())
