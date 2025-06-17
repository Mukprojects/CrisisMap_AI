"""
Entry point for running the CrisisMap AI API server.

This script ensures proper import paths are set up before running the FastAPI application.
"""
import sys
import os
from pathlib import Path

# Add the parent directory to the path
current_dir = Path(__file__).parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Now run the API
from crisismap_ai.api.app import app
import uvicorn
from crisismap_ai.config import API_HOST, API_PORT

if __name__ == "__main__":
    print("Starting CrisisMap AI API server...")
    try:
        uvicorn.run(app, host=API_HOST, port=API_PORT)
    except Exception as e:
        print(f"Error starting API server: {e}")
        import traceback
        traceback.print_exc() 