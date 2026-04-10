Final Demo: The Document Vault
Restart the Backend (Terminal 1): Required to pick up the new /v1/upload endpoint:

bash
pkill -f uvicorn
python3 -m uvicorn backend.mcp_server:app --host 0.0.0.0 --port 8000
Open the UI (Terminal 4 / Browser): If you have Streamlit running, you'll see a new "📤 Document Vault" tab in the sidebar.

The Test Flight:

Navigate to the Document Vault.
Upload 2-3 .txt or .md files (like project notes or logs).
Click "🚀 Start Ingestion".
Watch the progress bars fill up and the success balloons appear!
Finally, check the Dashboard—the "Live Docs" count will have increased automatically.