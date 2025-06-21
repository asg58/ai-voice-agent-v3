#!/usr/bin/env python3
"""
Script to wait for a service to be ready.
"""
import argparse
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

def wait_for_service(url, timeout=300, interval=5, verbose=True):
    """
    Wait for a service to be ready by checking its health endpoint.
    
    Args:
        url: URL to check
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds
        verbose: Whether to log progress messages
    
    Returns:
        bool: True if service is ready, False if timeout reached
    """
    if verbose:
        logger.info(f"Waiting for service at {url} to be ready...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code < 400:
                if verbose:
                    logger.info(f"Service at {url} is ready!")
                return True
            else:
                if verbose:
                    logger.warning(f"Service at {url} returned status code {response.status_code}, waiting...")
        except requests.RequestException as e:
            if verbose:
                logger.warning(f"Error connecting to {url}: {e}")
        
        time.sleep(interval)
    
    if verbose:
        logger.error(f"Timeout reached waiting for service at {url}")
    return False

def main():
    """Main function to parse arguments and wait for service."""
    parser = argparse.ArgumentParser(description="Wait for a service to be ready")
    parser.add_argument("--url", required=True, help="URL to check")
    parser.add_argument("--timeout", type=int, default=300, help="Maximum time to wait in seconds")
    parser.add_argument("--interval", type=int, default=5, help="Time between checks in seconds")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress messages")
    
    args = parser.parse_args()
    
    if wait_for_service(args.url, args.timeout, args.interval, not args.quiet):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())