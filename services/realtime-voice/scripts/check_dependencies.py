#!/usr/bin/env python3
"""
Script to check and install missing dependencies.
"""
import sys
import importlib.util
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_module(module_name: str) -> bool:
    """
    Check if a module is installed and can be imported.
    
    Args:
        module_name: Name of the module to check
        
    Returns:
        True if module is available, False otherwise
    """
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            logger.warning(f"Module {module_name} is NOT installed")
            return False
        
        module = importlib.import_module(module_name)
        logger.info(f"Module {module_name} is installed")
        
        if hasattr(module, '__version__'):
            logger.info(f"Version: {module.__version__}")
        
        return True
        
    except ImportError as e:
        logger.error(f"Import error for {module_name}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking {module_name}: {e}")
        return False

def install_module(module_name: str, version: str = None) -> bool:
    """
    Install a Python module using pip.
    
    Args:
        module_name: Name of the module to install
        version: Optional version to install
        
    Returns:
        True if installation succeeded, False otherwise
    """
    package = module_name
    if version:
        package = f"{module_name}=={version}"
    
    logger.info(f"Installing {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        logger.info(f"Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {package}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error installing {package}: {e}")
        return False

def main() -> int:
    """
    Main function to check and install modules.
    
    Returns:
        0 if all modules are installed successfully, 1 otherwise
    """
    # Define required modules with their versions
    required_modules = {
        'weaviate': '3.25.3',
        'openai': '1.3.0',
        'sqlalchemy': '2.0.23',
        'alembic': '1.12.1',
        'asyncpg': '0.28.0',
        'fastapi': '0.103.1',
        'uvicorn': '0.23.2',
        'numpy': '1.26.0',
        'redis': '5.0.1'
    }
    
    missing_modules = []
    
    # Check which modules are missing
    for module, version in required_modules.items():
        if not check_module(module):
            missing_modules.append((module, version))
      # Install missing modules
    if missing_modules:
        logger.info(f"Installing {len(missing_modules)} missing modules...")
        for module, version in missing_modules:
            install_module(module, version)
        
        # Verify installation
        all_installed = True
        for module, _ in missing_modules:
            if not check_module(module):
                all_installed = False
        
        if all_installed:
            logger.info("All required modules are now installed!")
            return 0
        else:
            logger.error("Some required modules could not be installed!")
            return 1
    else:
        logger.info("All required modules are already installed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())