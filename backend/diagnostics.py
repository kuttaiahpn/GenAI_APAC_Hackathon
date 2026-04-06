import asyncio
import os
import uuid
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from google.cloud import storage
import vertexai
from vertexai.language_models import TextEmbeddingModel

print("--- Starting module-level imports in diagnostics.py ---")
# Local Imports
from .database import engine, AsyncSessionFactory, load_config
from .models import Base
print("--- Imports successful ---")

async def run_diagnostics():
    print("=== TaskNinja System Health Audit (Root Cause Analysis Mode) ===")
    print(f"Target Project: {os.getenv('GOOGLE_CLOUD_PROJECT', 'track3codelabs')}")
    print("-" * 60)

    # 1. Connectivity Check
    print("[1/5] Connectivity & Version Check...")
    try:
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT version();"))
            version = res.scalar()
            print(f"  ✅ Connected to AlloyDB: {version[:50]}...")
    except Exception as e:
        print(f"  ❌ Connectivity Failed: {e}")
        return

    # 2. Extension Check
    print("[2/5] PostgreSQLExtensions Check...")
    try:
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT extname FROM pg_extension;"))
            extensions = [r[0] for r in res.fetchall()]
            for ext in ["vector", "uuid-ossp"]:
                status = "✅" if ext in extensions else "❌ MISSING"
                print(f"  {status} Extension: {ext}")
    except Exception as e:
        print(f"  ❌ Extension Check Failed: {e}")

    # 3. Schema Audit (Reporting Only)
    print("[3/5] Schema Integrity Audit...")
    try:
        async with engine.connect() as conn:
            def get_tables(sync_conn):
                return inspect(sync_conn).get_table_names()
            
            existing_tables = await conn.run_sync(get_tables)
            expected_tables = Base.metadata.tables.keys()
            
            for table in expected_tables:
                status = "✅" if table in existing_tables else "🔴 MISSING"
                print(f"  {status} Table: {table}")
    except Exception as e:
        print(f"  ❌ Schema Audit Failed: {e}")

    # 4. Vector Dimension & Precision Check
    print("[4/5] pgvector 768-D Check...")
    try:
        async with engine.connect() as conn:
            # Check the actual dimension of the embedding column
            res = await conn.execute(text("""
                SELECT atttypmod 
                FROM pg_attribute 
                WHERE attrelid = 'embeddings'::regclass 
                AND attname = 'embedding';
            """))
            dim = res.scalar()
            if dim == 768:
                print(f"  ✅ pgvector Dimension: {dim} (Matches text-embedding-004)")
            else:
                print(f"  ⚠️ pgvector Dimension mismatch: {dim} (Expected 768)")
    except Exception as e:
        print(f"  ❌ Vector Check Failed (Expected if 'embeddings' table is missing): {e}")

    # 5. Vertex AI & GCS Handshake
    print("[5/5] Vertex AI & GCS Handshake...")
    config = load_config()
    bucket_id = "taskninja-demo-docs-track3codelabs"
    
    try:
        # Vertex AI Handshake
        vertexai.init(project=config.get("gcp_project_id", "track3codelabs"), location="us-central1")
        model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        print(f"  ✅ Vertex AI Connection: Model 'text-embedding-004' ready.")
        
        # GCS Handshake
        client = storage.Client()
        bucket = client.bucket(bucket_id)
        if bucket.exists():
            print(f"  ✅ GCS Bucket Connectivity: {bucket_id} is accessible.")
        else:
            print(f"  ❌ GCS Bucket Connectivity: {bucket_id} NOT FOUND.")
    except Exception as e:
        print(f"  ❌ Vertex/GCS Handshake Failed: {e}")

    print("-" * 60)
    print("Audit Complete. Review the 🔴 MISSING or ❌ indicators for Root Cause Analysis.")

if __name__ == "__main__":
    print("Executing main block...")
    try:
        asyncio.run(run_diagnostics())
    except Exception as e:
        print(f"CRITICAL FAILURE in diagnostics main execution: {e}")
        import traceback
        traceback.print_exc()
