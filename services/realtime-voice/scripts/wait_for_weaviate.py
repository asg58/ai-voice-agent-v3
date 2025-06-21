#!/usr/bin/env python3
"""
Script to wait for Weaviate to be ready.
"""
import os
import time
import sys
import logging
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def wait_for_weaviate(weaviate_url=None, timeout=300, interval=5, verbose=True):
    """
    Wait for Weaviate to be ready.
    
    Args:
        weaviate_url: Weaviate URL
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds
        verbose: Whether to log progress messages
    
    Returns:
        bool: True if Weaviate is ready, False if timeout reached
    """
    # Get Weaviate URL from environment if not provided
    if weaviate_url is None:
        weaviate_url = os.environ.get("WEAVIATE_URL")
        if not weaviate_url:
            if verbose:
                logger.error("WEAVIATE_URL environment variable not set")
            return False
    
    # Ensure URL ends with the ready endpoint
    if not weaviate_url.endswith("/v1/.well-known/ready"):
        if weaviate_url.endswith("/"):
            weaviate_url = weaviate_url + "v1/.well-known/ready"
        else:
            weaviate_url = weaviate_url + "/v1/.well-known/ready"
    
    if verbose:
        logger.info(f"Waiting for Weaviate at {weaviate_url} to be ready...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(weaviate_url, timeout=10)
            if response.status_code < 400:
                if verbose:
                    logger.info("Weaviate is ready!")
                return True
            else:
                if verbose:
                    logger.warning(f"Weaviate returned status code {response.status_code}, waiting...")
        except requests.RequestException as e:
            if verbose:
                logger.warning(f"Error connecting to Weaviate: {e}")
        
        time.sleep(interval)
    
    if verbose:
        logger.error("Timeout reached waiting for Weaviate")
    return False

def main() -> int:
    """
    Main function.
    
    Returns:
        0 if Weaviate is ready, 1 otherwise
    """
    weaviate_url = os.environ.get("WEAVIATE_URL")
    if wait_for_weaviate(weaviate_url):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())