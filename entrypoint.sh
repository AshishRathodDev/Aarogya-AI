#!/bin/sh
# This is the definitive, unified entrypoint script for all services.

# Set a default value for the PORT environment variable.
# The ":-" syntax means: use $PORT if it's set, otherwise use the default.
APP_PORT=${PORT:-8000}

# The first argument to this script ($1) tells us which service to start.
SERVICE_TYPE="$1"

echo "--- [Entrypoint] Starting Service: ${SERVICE_TYPE} on Port: ${APP_PORT} ---"

if [ "$SERVICE_TYPE" = "api" ]; then
  # Start the FastAPI server
  exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker aarogya_ai.api.main:app --bind 0.0.0.0:${APP_PORT}

elif [ "$SERVICE_TYPE" = "dashboard" ]; then
  # Start the Streamlit dashboard
  exec streamlit run src/aarogya_ai/dashboard.py --server.port=${APP_PORT} --server.address=0.0.0.0

else
  echo "Error: Unknown service type '$SERVICE_TYPE'. Please specify 'api' or 'dashboard'."
  exit 1
fi

