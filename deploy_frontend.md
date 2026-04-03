# TaskNinja Streamlit Deployment & Secret Manager Setup

To ensure total end-to-end security while validating your "Command Center," we inject Google Cloud Secret Manager explicitly configuring the API Gateway hook.

## 1. Register API KEY organically in Google Cloud Secret Manager
Execute these commands dynamically from Cloud Shell to generate and register your access key block payload.

```bash
# Enable the Secret Manager API natively if you haven't yet!
gcloud services enable secretmanager.googleapis.com

# Create the Secret Record Configuration
gcloud secrets create API_KEY --replication-policy="automatic"

# Inject the Hackathon pass-phrase into the container record natively
echo -n "hackathon2026_super_secret" | gcloud secrets versions add API_KEY --data-file=-
```

*(Note: Grant the default Compute Engine service account access to the Secret payload via IAM if you natively configured custom boundaries)*

## 2. Compile the Container Image (Frontend)
Run this inside the `frontend` payload directory natively!
```bash
cd frontend
gcloud builds submit --tag gcr.io/track3codelabs/taskninja-ui .
```

## 3. Deploy UI securely with dynamically mapped Secrets
Run the layout hook. This command binds the native generic `API_KEY` exactly mapped to `latest` iteration and hard-codes the Backend Orchestration hook.

```bash
gcloud run deploy taskninja-ui \
  --image gcr.io/track3codelabs/taskninja-ui \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets="API_KEY=API_KEY:latest" \
  --set-env-vars="BACKEND_URL=https://taskninja-mcp-gateway-836906162288.us-central1.run.app" \
  --port 8501
```
