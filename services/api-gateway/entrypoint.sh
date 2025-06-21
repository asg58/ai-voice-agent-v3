#!/bin/sh

# Wait for service discovery to be available
echo "Waiting for service discovery..."
until $(curl --output /dev/null --silent --head --fail ${SERVICE_DISCOVERY_URL}/health); do
    printf '.'
    sleep 2
done
echo "Service discovery is available!"

# Start the API Gateway
echo "Starting API Gateway..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000