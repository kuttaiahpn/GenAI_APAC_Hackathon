import vertexai
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import HumanMessage
import asyncio
import os

# Local config
from backend.database import load_config

async def scout_models():
    config = load_config()
    project = config.get("gcp_project_id", "track3codelabs")
    location = config.get("gcp_location", "us-central1")
    
    print(f"--- Vertex AI Model Scout ---")
    print(f"Project: {project}")
    print(f"Location: {location}")
    print("-" * 30)

    # Models to test in order of preference
    candidate_models = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-001",
        "gemini-1.5-flash-002",
        "gemini-1.0-pro",
        "gemini-pro",
        "gemini-1.5-pro",
        "gemini-1.5-pro-001"
        "gemini-2.5-pro"
    ]

    working_model = None

    for model_name in candidate_models:
        print(f"Testing '{model_name}'...", end=" ", flush=True)
        try:
            llm = ChatVertexAI(
                model_name=model_name,
                project=project,
                location=location,
                max_output_tokens=10,
                temperature=0
            )
            # Simple test call
            res = await llm.ainvoke("Hi")
            print("✅ Success!")
            working_model = model_name
            break # Stop at the first working model
        except Exception as e:
            if "404" in str(e):
                print("❌ 404 Not Found")
            elif "400" in str(e):
                print(f"⚠️ 400 Invalid/Quota (Likely found but fails request)")
            else:
                print(f"❌ Error: {str(e)[:50]}...")

    if working_model:
        print("-" * 30)
        print(f"FINAL RESULT: Please use '{working_model}'")
        print("-" * 30)
    else:
        print("\nFATAL: No working Gemini models found in this region.")
        print("Tip: Try changing 'gcp_location' in config.yaml to 'us-east1' and run again.")

if __name__ == "__main__":
    asyncio.run(scout_models())
