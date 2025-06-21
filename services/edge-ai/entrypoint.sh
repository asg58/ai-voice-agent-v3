#!/bin/bash
set -e

# Convert LOG_LEVEL to lowercase for uvicorn
LOG_LEVEL_LOWER=$(echo "$LOG_LEVEL" | tr '[:upper:]' '[:lower:]')

# Start the FastAPI application with Uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --log-level $LOG_LEVEL_LOWER