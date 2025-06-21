#!/usr/bin/env python
"""
Health check script for the realtime-voice service
Used by Docker to verify service health
"""
import sys
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Health check endpoint
HEALTH_CHECK_URL = "http://localhost:8080/health/health"

def check_service_health():
    """
    Check if the service is healthy by making a request to the health endpoint
    Returns exit code 0 if healthy, 1 otherwise
    """
    try:
        logger.info(f"Checking service health at {HEALTH_CHECK_URL}")
        response = requests.get(HEALTH_CHECK_URL, timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            status = health_data.get("status", "")
            
            if status.lower() == "healthy":
                logger.info("Service is healthy")
                return 0
            else:
                logger.warning(f"Service reported unhealthy status: {status}")
                return 1
        else:
            logger.error(f"Health check failed with status code: {response.status_code}")
            return 1
            
    except requests.RequestException as e:
        logger.error(f"Health check request failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during health check: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(check_service_health())