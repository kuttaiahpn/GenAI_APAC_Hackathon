import os
import uuid
import asyncio
from google.cloud import storage
from sqlalchemy.ext.asyncio import AsyncSession

# Local Imports
from .ingest import ingest_document
from .database import AsyncSessionFactory

DEFAULT_BUCKET = "taskninja-demo-docs-track3codelabs"

def upload_blob(source_file_name, destination_blob_name, bucket_name=DEFAULT_BUCKET):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)
    print(f"File {source_file_name} uploaded to {destination_blob_name} in {bucket_name}.")
    return f"gs://{bucket_name}/{destination_blob_name}"

def read_blob_as_text(gs_uri):
    """Reads content from a GCS URI (gs://bucket/blob)."""
    storage_client = storage.Client()
    if not gs_uri.startswith("gs://"):
        raise ValueError("Invalid GCS URI. Must start with 'gs://'")
    
    parts = gs_uri[5:].split("/", 1)
    bucket_name = parts[0]
    blob_name = parts[1]
    
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    content = blob.download_as_text()
    return content

async def ingest_from_gcs(gs_uri, user_id=None, title=None):
    """
    Diagnostic Bridge: Fetches content from GCS and triggers the Phase 1 Ingestion Logic.
    """
    if user_id is None:
        user_id = uuid.uuid4()
    
    if title is None:
        title = os.path.basename(gs_uri)

    print(f"Starting ingestion from GCS: {gs_uri}")
    content = read_blob_as_text(gs_uri)
    
    async with AsyncSessionFactory() as db:
        doc_id = await ingest_document(db, content, user_id, title)
        print(f"Successfully ingested GCS document: {doc_id}")
        return doc_id

if __name__ == "__main__":
    # Example usage for manual testing
    # asyncio.run(ingest_from_gcs("gs://taskninja-demo-docs-track3codelabs/sample.txt"))
    pass
