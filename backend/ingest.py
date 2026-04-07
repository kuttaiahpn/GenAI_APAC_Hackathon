import asyncio
import uuid
import yaml
from pathlib import Path
from typing import List

import vertexai
from vertexai.language_models import TextEmbeddingModel
from sqlalchemy.ext.asyncio import AsyncSession

from .database import AsyncSessionFactory, CONFIG_PATH, load_config
from .models import Document, Embedding
from google.cloud import storage
import os

class RecursiveCharacterTextSplitter:
    """A simplistic recursive character text splitter for chunking documents."""
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", " ", ""]

    def split_text(self, text: str) -> List[str]:
        final_chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            if end >= len(text):
                final_chunks.append(text[start:].strip())
                break
                
            split_at = end
            for sep in self.separators:
                if sep == "":
                    continue
                pos = text.rfind(sep, start, end)
                if pos != -1 and pos > start:
                    split_at = pos + len(sep)
                    break
            
            chunk = text[start:split_at].strip()
            if chunk:
                final_chunks.append(chunk)

            # Advance start pointer, ensuring progress even with large overlap
            next_start = split_at - self.chunk_overlap
            start = max(start + 1, next_start) 

        return [c for c in final_chunks if c]


async def ingest_document(
    db: AsyncSession, 
    raw_text: str, 
    user_id: uuid.UUID, 
    title: str = "Untitled Document"
) -> uuid.UUID:
    """Ingests raw text, saves to GCS, and vectorizes into AlloyDB."""
    config = load_config()
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", config.get("gcp_project_id", "track3codelabs"))
    location = config.get("gcp_location", "us-central1")
    bucket_name = os.getenv("GCS_BUCKET_NAME", f"taskninja-vault-{project_id}")
    
    # 1. GCS Persistence (The "Cold Storage" Layer)
    storage_client = storage.Client(project=project_id)
    try:
        bucket = storage_client.bucket(bucket_name)
        file_name = f"vault/{uuid.uuid4()}_{title}.txt"
        blob = bucket.blob(file_name)
        blob.upload_from_string(raw_text)
        gcs_uri = f"gs://{bucket_name}/{file_name}"
        print(f"SRE_LOG: Persisted file to GCS: {gcs_uri}")
    except Exception as e:
        print(f"SRE_ERROR: GCS Upload FAILED: {e}")
        gcs_uri = None # We proceed to DB but log the storage failure

    # 2. Vertex AI Initialization
    vertexai.init(project=project_id, location=location)
    model_name = config.get("models", {}).get("vector_search", "text-embedding-004")
    embedding_model = TextEmbeddingModel.from_pretrained(model_name)

    # 3. AlloyDB Persistence (The "Hot Search" Layer)
    pii_flag = "PII" in raw_text or "Confidential" in raw_text
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_text(raw_text)

    new_doc = Document(
        title=title,
        content=raw_text,
        gcs_uri=gcs_uri,
        pii_flag=pii_flag
    )
    db.add(new_doc)
    await db.flush() 

    BATCH_SIZE = 100
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        embedding_res = embedding_model.get_embeddings(batch, output_dimensionality=768)
        
        for j, (chunk, embedding) in enumerate(zip(batch, embedding_res)):
            new_embedding = Embedding(
                doc_id=new_doc.doc_id,
                chunk_id=f"chunk_{i + j}",
                text_chunk=chunk,
                embedding=embedding.values
            )
            db.add(new_embedding)

    await db.commit()
    print(f"SRE_LOG: Synchronized sync completed for {title} (DocID: {new_doc.doc_id})")
    return new_doc.doc_id

async def main():
    print("Starting ingestion test...")
    # This requires AlloyDB to be reachable and google-cloud-aiplatform configured
    try:
        async with AsyncSessionFactory() as db:
            test_text = "This is a PII containing test document.\n" + ("It has multiple lines and words to test chunking logic. " * 30)
            test_user_id = uuid.uuid4()
            print(f"Generating chunks and vectors...")
            doc_id = await ingest_document(db, test_text, test_user_id, "Vertex AI Test Doc")
            print(f"[SUCCESS] Successfully ingested doc and vectors! Doc ID: {doc_id}")
    except Exception as e:
        print(f"[ERROR] Ingestion failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
