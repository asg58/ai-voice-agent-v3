#!/bin/bash

# Stop all running containers
docker-compose down

# Build all containers
docker-compose build

# Start all containers
docker-compose up -d

# Print status
echo "All services have been restarted."
