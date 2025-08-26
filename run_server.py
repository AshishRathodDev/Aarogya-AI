# run_server.py

import uvicorn
import sys
import os

# [CRITICAL] This line explicitly adds the 'src' directory to Python's path.
# This allows the Python interpreter to find the 'aarogya_ai' package inside it.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

if __name__ == "__main__":
    print("--- Starting Aarogya-AI Server ---")
    
    # This is the correct, unambiguous path to your app object
    app_location = "aarogya_ai.api.main:app"
    
    uvicorn.run(
        app_location,
        host="127.0.0.1",
        port=8000,
        reload=True,
        # We explicitly tell the reloader to watch the correct directory
        reload_dirs=["src/aarogya_ai"]
    )
    
    