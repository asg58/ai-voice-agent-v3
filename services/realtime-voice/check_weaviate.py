#!/usr/bin/env python3
"""
Script to check if weaviate is properly installed and accessible.
"""
import sys
import importlib.util

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

def main():
    """Main function to check modules."""
    modules_to_check = [
        'weaviate',
        'openai',
        'sqlalchemy',
        'alembic',
        'asyncpg',
        'fastapi',
        'uvicorn',
        'numpy',
        'redis'
    ]
    
    all_installed = True
    for module in modules_to_check:
        if not check_module(module):
            all_installed = False
    
    if all_installed:
        print("\nAll required modules are installed!")
        return 0
    else:
        print("\nSome required modules are missing!")
        return 1

if __name__ == "__main__":
    sys.exit(main())