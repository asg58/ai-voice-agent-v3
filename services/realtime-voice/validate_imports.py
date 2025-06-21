#!/usr/bin/env python
"""
Validate imports for the realtime-voice service
Checks that all required dependencies are available and compatible
"""
import sys
import importlib
import logging
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Required packages and their minimum versions
REQUIRED_PACKAGES: Dict[str, str] = {
    "fastapi": "0.95.0",
    "uvicorn": "0.21.0",
    "pydantic": "1.10.0",
    "websockets": "10.4",
    "aiortc": "1.3.0",
    "numpy": "1.22.0",
    "redis": "4.5.0",
    "sqlalchemy": "2.0.0",
    "asyncpg": "0.27.0",
    "jinja2": "3.1.0",
    "python-multipart": "0.0.5",
    "aiohttp": "3.8.0",
    "python-dotenv": "1.0.0",
}

def check_package(package_name: str, min_version: str) -> Tuple[bool, str]:
    """
    Check if a package is installed and meets the minimum version requirement
    
    Args:
        package_name: Name of the package to check
        min_version: Minimum required version
        
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        module = importlib.import_module(package_name)
        version = getattr(module, "__version__", "unknown")
        
        if version == "unknown":
            return True, f"{package_name}: version unknown (assuming compatible)"
        
        # Simple version comparison (for production, use packaging.version)
        if version < min_version:
            return False, f"{package_name}: installed {version}, required {min_version}"
        
        return True, f"{package_name}: installed {version} ✓"
        
    except ImportError:
        return False, f"{package_name}: not installed"
    except Exception as e:
        return False, f"{package_name}: error checking - {str(e)}"

def validate_imports() -> bool:
    """
    Validate all required imports
    
    Returns:
        True if all imports are valid, False otherwise
    """
    logger.info("Validating required packages...")
    
    all_valid = True
    failed_packages: List[str] = []
    
    for package_name, min_version in REQUIRED_PACKAGES.items():
        is_valid, message = check_package(package_name, min_version)
        
        if is_valid:
            logger.info(message)
        else:
            logger.error(message)
            all_valid = False
            failed_packages.append(package_name)
    
    if all_valid:
        logger.info("All required packages are available and compatible ✓")
    else:
        logger.error(f"Missing or incompatible packages: {', '.join(failed_packages)}")
    
    return all_valid

if __name__ == "__main__":
    if validate_imports():
        sys.exit(0)
    else:
        sys.exit(1)