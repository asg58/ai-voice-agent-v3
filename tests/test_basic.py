"""
Basic test to verify the test environment is set up correctly
"""
import pytest
import sys
from pathlib import Path

def test_python_path():
    """Test that the Python path is set up correctly"""
    # Check that the project root is in the Python path
    project_root = Path(__file__).parent.parent
    assert str(project_root) in sys.path
    
    # Check that we can import from the project
    import tests
    assert tests.__name__ == "tests"
    
    # Print the Python path for debugging
    print("\nPython path:")
    for path in sys.path:
        print(f"  {path}")