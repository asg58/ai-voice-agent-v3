#!/usr/bin/env python3
"""
Script to test if the weaviate client is working.
"""
import os
import sys
import logging
import weaviate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_weaviate_client(weaviate_url=None):
    """
    Test if the weaviate client is working.
    
    Args:
        weaviate_url: Weaviate URL
    
    Returns:
        bool: True if the weaviate client is working, False otherwise
    """
    # Get Weaviate URL from environment if not provided
    if weaviate_url is None:
        weaviate_url = os.environ.get("WEAVIATE_URL")
        if not weaviate_url:
            logger.error("WEAVIATE_URL environment variable not set")
            return False
    
    try:
        # Create a weaviate client
        client = weaviate.Client(weaviate_url)
        
        # Check if the client is connected
        if client.is_ready():
            logger.info("Weaviate client is connected!")
            return True
        else:
            logger.error("Weaviate client is not connected!")
            return False
    except Exception as e:
        logger.error(f"Error connecting to Weaviate: {e}")
        return False


def main() -> int:
    """
    Main function.
    
    Returns:
        0 if Weaviate client is working, 1 otherwise
    """
    weaviate_url = os.environ.get("WEAVIATE_URL")
    if test_weaviate_client(weaviate_url):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())