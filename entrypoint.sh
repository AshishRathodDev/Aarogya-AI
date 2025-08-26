#!/bin/sh

# This script is the definitive entrypoint for the API container.
# It activates the virtual environment implicitly by using the full path
# to the executables, which is the most robust method.

echo "--- Starting Gunicorn Server via entrypoint.sh ---"

# We use the full path to the gunicorn executable inside the venv.
# This bypasses any and all $PATH issues.
/app/.venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker aarogya_ai.api.main:app --bind 0.0.0.0:8000
