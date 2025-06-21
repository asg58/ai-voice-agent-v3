#!/bin/bash
# Docker entrypoint script for realtime-voice service

set -e

# Print environment for debugging (excluding sensitive values)
echo "Starting realtime-voice service with environment:"
env | grep -v "PASSWORD\|SECRET\|KEY" | sort

# Check and install dependencies if needed
echo "Checking Python dependencies..."
# Directly install critical dependencies to ensure they're available
if [ -f /tmp/requirements-weaviate.txt ]; then
    echo "Installing dependencies from /tmp/requirements-weaviate.txt..."
    pip install -r /tmp/requirements-weaviate.txt
elif [ -f /app/requirements-weaviate.txt ]; then
    echo "Installing dependencies from /app/requirements-weaviate.txt..."
    pip install -r /app/requirements-weaviate.txt
else
    echo "requirements-weaviate.txt not found, installing critical dependencies directly..."
    pip install --no-cache-dir weaviate-client==3.25.3 openai==1.3.0 sqlalchemy==2.0.23 alembic==1.12.1 asyncpg==0.28.0 redis==5.0.1
fi

# Verify weaviate is installed
if python -c "import weaviate" 2>/dev/null; then
    echo "Weaviate client is installed!"
    python -c "import weaviate; print(f'Weaviate client version: {weaviate.__version__}')"
    
    # Test weaviate client if script is available
    if [ -f /app/scripts/test_weaviate.py ]; then
        echo "Testing weaviate client..."
        python -m scripts.test_weaviate
    fi
else
    echo "WARNING: Weaviate client is NOT installed! Installing now..."
    pip install --no-cache-dir weaviate-client==3.25.3
fi

# Verify PyAudio is installed
if python -c "import pyaudio" 2>/dev/null; then
    echo "PyAudio is installed!"
    python -c "import pyaudio; print(f'PyAudio version: {pyaudio.__version__}')"
else
    echo "WARNING: PyAudio is NOT installed! Installing now..."
    # Try to install PyAudio without building from source
    pip install --no-cache-dir pyaudio || {
        echo "Failed to install PyAudio via pip. Installing system package..."
        apt-get update && apt-get install -y python3-pyaudio
    }
fi

# Run dependency check script if available
if [ -f /app/check_dependencies.py ]; then
    echo "Running dependency check script..."
    python /app/check_dependencies.py
fi

# Wait for external services to be ready
echo "Waiting for external services..."

# Wait for PostgreSQL
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for PostgreSQL..."
    # Simple retry loop for PostgreSQL using pg_isready equivalent
    MAX_RETRIES=60
    RETRY_COUNT=0
    # Extract host and port from DATABASE_URL
    DB_HOST=${DB_HOST:-postgres}
    DB_PORT=${DB_PORT:-5432}
    
    until python -c "
import socket
import sys
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex(('$DB_HOST', $DB_PORT))
    sock.close()
    if result == 0:
        print('PostgreSQL is accepting connections')
        sys.exit(0)
    else:
        sys.exit(1)
except Exception as e:
    print(f'Connection failed: {e}')
    sys.exit(1)
" 2>/dev/null || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
        echo "PostgreSQL connection attempt $((++RETRY_COUNT)) of $MAX_RETRIES..."
        sleep 3
    done
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "Could not connect to PostgreSQL, but continuing anyway..."
    else
        echo "Successfully connected to PostgreSQL!"
    fi
fi

# Wait for Redis
if [ -n "$REDIS_URL" ]; then
    echo "Waiting for Redis..."
    # Simple retry loop for Redis
    MAX_RETRIES=30
    RETRY_COUNT=0
    until python -c "import redis; r = redis.from_url('$REDIS_URL'); r.ping()" 2>/dev/null || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
        echo "Redis connection attempt $((++RETRY_COUNT)) of $MAX_RETRIES..."
        sleep 2
    done
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "Could not connect to Redis, but continuing anyway..."
    else
        echo "Successfully connected to Redis!"
    fi
fi

# Wait for Weaviate if configured
if [ -n "$WEAVIATE_URL" ]; then
    echo "Waiting for Weaviate..."
    if [ -f /app/scripts/wait_for_weaviate.py ]; then
        python -m scripts.wait_for_weaviate
    else
        # Simple retry loop for Weaviate
        MAX_RETRIES=30
        RETRY_COUNT=0
        until curl -s -f "$WEAVIATE_URL/v1/.well-known/ready" > /dev/null 2>&1 || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
            echo "Weaviate connection attempt $((++RETRY_COUNT)) of $MAX_RETRIES..."
            sleep 2
        done
        if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
            echo "Could not connect to Weaviate, but continuing anyway..."
        else
            echo "Successfully connected to Weaviate!"
        fi
    fi
fi

# Run database migrations if needed
if [ -n "$RUN_MIGRATIONS" ]; then
    echo "Running database migrations..."
    if [ -f /app/scripts/run_migrations.py ]; then
        python -m scripts.run_migrations
    else
        echo "Migration script not found, skipping migrations."
    fi
fi

# Determine which main file to run - Use consolidated main.py
MAIN_FILE="main.py"

# Convert LOG_LEVEL to lowercase to ensure compatibility with uvicorn
LOG_LEVEL=$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')

# Start the application with consolidated main
echo "Starting application with consolidated $MAIN_FILE..."
# Use the consolidated main.py directly (not in src folder)
exec uvicorn $MAIN_FILE:app --host ${SERVICE_HOST:-0.0.0.0} --port ${SERVICE_PORT:-8080} --log-level $LOG_LEVEL