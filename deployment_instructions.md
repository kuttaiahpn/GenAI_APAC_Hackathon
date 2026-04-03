# Deployment Instructions for TaskNinja MCP Gateway

This document provides the exact Google Cloud SDK hooks (`gcloud`) required to containerize and push our finished Phase 2 MCP server to Google Cloud Run natively.

## 1. Setup Your Google Cloud Shell
Ensure you have set your core Google Cloud Project ID matching your `config.yaml` (`track3codelabs`):
```bash
gcloud config set project track3codelabs
```

## 2. Push Image via Cloud Build
Upload the source snapshot and build the Dockerfile. We will tag the final image as `taskninja-mcp-gateway`.
```bash
gcloud builds submit --tag gcr.io/track3codelabs/taskninja-mcp-gateway .
```
*(Run this command directly in the same root folder containing `Dockerfile`)*

## 3. Deploy to Cloud Run & Bind to AlloyDB VPC
This deployment command allocates backend endpoints and exposes Port 8080 exactly to the MCP Gateway. 

Because AlloyDB uses a Private IP (10.34.0.8), your Cloud Run service must be deployed onto the same VPC network. We will use **Direct VPC Egress** (the modern replacement for VPC Connectors) to attach the service directly to your `default` network.

```bash
gcloud run deploy taskninja-mcp-gateway \
  --image gcr.io/track3codelabs/taskninja-mcp-gateway \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --network default \
  --subnet default \
  --vpc-egress private-ranges-only \
  --port 8080 \
  --set-env-vars="DB_PASSWORD=changemelater"
```

> **Note on `allow-unauthenticated`:** During hackathon demos, it's typically easiest to leave the endpoint public, allowing Streamlit and your orchestrator agent rapid ingress routing. Re-evaluate this binding with standard OIDC if placing in serious production!
