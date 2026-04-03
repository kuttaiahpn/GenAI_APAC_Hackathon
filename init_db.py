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
        import traceback
        print(f"\n❌ [ERROR] Database initialization failed.")
        print("-" * 40)
        traceback.print_exc()
        print("-" * 40)
        print("\nPossible causes:")
        print("1. Cloud Shell is NOT in your VPC (Default Cloud Shell is external).")
        print("2. The AlloyDB Auth Proxy is not running.")
        print("3. Firewall rules in your VPC are blocking port 5432.")
        print("\nTip: Try running 'nc -zv 10.34.0.8 5432' to check connectivity first.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_init())
