import asyncio
import os
import uuid
from google.cloud import storage
from backend.database import AsyncSessionFactory
from backend.ingest import ingest_document

async def backfill_vault():
    """SRE Utility: Synchronizes the existing GCS bucket state with AlloyDB."""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "track3codelabs")
    bucket_name = os.getenv("GCS_BUCKET_NAME", f"taskninja-vault-{project_id}")
    
    print(f"🚀 SRE Recovery: Scanning Bucket '{bucket_name}'...", flush=True)
    
    storage_client = storage.Client(project=project_id)
    try:
        bucket = storage_client.bucket(bucket_name)
        blobs = list(bucket.list_blobs())
        
        print(f"📦 Found {len(blobs)} files in vault. Commencing synchronization...", flush=True)
        
        # 771ce1ff represents the Judge/Demo User ID
        JUDGE_UID = uuid.UUID("771ce1ff-b0ed-4246-ba3b-dca00665c138")
        
        async with AsyncSessionFactory() as db:
            for blob in blobs:
                # We skip metadata/folders
                if blob.name.endswith("/") or ".txt" not in blob.name:
                    continue
                
                print(f"🔍 Syncing: {blob.name}...", flush=True)
                content = blob.download_as_text()
                
                # Check for existing
                from sqlalchemy import select
                from backend.models import Document
                stmt = select(Document).where(Document.title == blob.name)
                res = await db.execute(stmt)
                if res.scalar():
                    print(f"  ⏩ Skipping: Already synchronized.")
                    continue
                
                # Trigger Ingestion (Vector + DB)
                doc_id = await ingest_document(
                    db=db,
                    raw_text=content,
                    user_id=JUDGE_UID,
                    title=blob.name
                )
                print(f"  ✅ Success: Sync ID {doc_id}")
                
            print("\n🏁 DASHBOARD_RECOVERY: Complete. Your metrics are now synchronized.", flush=True)
            
    except Exception as e:
        print(f"❌ SRE_ERROR: Backfill failed: {e}")

if __name__ == "__main__":
    asyncio.run(backfill_vault())
