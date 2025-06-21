#!/usr/bin/env python
"""
PyAudio Dependency Check Script

This script verifies that PyAudio is properly installed and working.
It also checks for the required system dependencies.
"""
import sys
import subprocess
import importlib.util
import logging
from typing import List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_system_dependencies() -> List[Tuple[str, bool]]:
    """
    Check if required system dependencies are installed.
    
    Returns:
        List of tuples containing (dependency_name, is_installed)
    """
    dependencies = [
        "portaudio19-dev",
        "libasound2", 
        "python3-pyaudio"
    ]
    
    results = []
    for dep in dependencies:
        try:
            # Check if the package is installed
            result = subprocess.run(
                ["dpkg", "-s", dep], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            installed = result.returncode == 0
            results.append((dep, installed))
        except FileNotFoundError:
            logger.warning(f"dpkg not found, cannot check {dep}")
            results.append((dep, False))
        except Exception as e:
            logger.error(f"Error checking {dep}: {e}")
            results.append((dep, False))
    
    return results

def check_pyaudio() -> bool:
    """
    Check if PyAudio is properly installed.
    
    Returns:
        True if PyAudio is working correctly, False otherwise
    """
    try:
        # Check if PyAudio is installed
        spec = importlib.util.find_spec("pyaudio")
        if spec is None:
            logger.warning("PyAudio is not installed")
            return False
        
        # Import PyAudio - ignore linting error as this is optional dependency
        import pyaudio  # pylint: disable=import-outside-toplevel
        logger.info(f"PyAudio version: {pyaudio.__version__}")
        
        # Try to create a PyAudio instance
        p = pyaudio.PyAudio()
        
        # Get device count
        device_count = p.get_device_count()
        logger.info(f"Number of audio devices: {device_count}")
        
        # List devices
        for i in range(device_count):
            device_info = p.get_device_info_by_index(i)
            logger.info(f"Device {i}: {device_info['name']}")
        
        # Terminate PyAudio
        p.terminate()
        
        return True
    except ImportError as e:
        logger.error(f"PyAudio import error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error checking PyAudio: {e}")
        return False

def main() -> int:
    """
    Main function to check PyAudio and its dependencies.
    
    Returns:
        0 if all dependencies are properly installed, 1 otherwise
    """
    logger.info("Checking system dependencies...")
    dependencies = check_system_dependencies()
    
    all_deps_installed = True
    for dep, installed in dependencies:
        status = "✓ Installed" if installed else "✗ Not installed"
        logger.info(f"  {dep}: {status}")
        if not installed:
            all_deps_installed = False
    
    logger.info("Checking PyAudio installation...")
    pyaudio_installed = check_pyaudio()
    
    if all_deps_installed and pyaudio_installed:
        logger.info("✓ All dependencies and PyAudio are properly installed")
        return 0
    else:
        logger.error("✗ Some dependencies or PyAudio are not properly installed")
        return 1

if __name__ == "__main__":
    sys.exit(main())