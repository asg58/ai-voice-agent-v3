#!/usr/bin/env python3
"""
Script to check if all required dependencies are installed.
"""
import sys
import importlib.util
import subprocess

def check_module(module_name):
    """Check if a module is installed and can be imported."""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            print(f"Module {module_name} is NOT installed!")
            return False
        else:
            module = importlib.import_module(module_name)
            print(f"Module {module_name} is installed!")
            if hasattr(module, '__version__'):
                print(f"Version: {module.__version__}")
            return True
    except ImportError:
        print(f"Module {module_name} is NOT installed!")
        return False

def install_module(module_name, version=None):
    """Install a Python module using pip."""
    package = module_name
    if version:
        package = f"{module_name}=={version}"
    
    print(f"Installing {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package}: {e}")
        return False

def main():
    """Main function to check and install modules."""
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
        print("\nInstalling missing modules...")
        for module, version in missing_modules:
            install_module(module, version)
        
        # Verify installation
        all_installed = True
        for module, _ in missing_modules:
            if not check_module(module):
                all_installed = False
        
        if all_installed:
            print("\nAll required modules are now installed!")
            return 0
        else:
            print("\nSome required modules could not be installed!")
            return 1
    else:
        print("\nAll required modules are already installed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())