import sys
import os
import pytest
from unittest.mock import patch
# Voeg projectroot toe aan sys.path als dat nog niet is gebeurd
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from memory.memory_awareness import MemoryAwareness

def test_detect_memory_modules():
    awareness = MemoryAwareness()
    modules = awareness.detect_memory_modules()
    assert isinstance(modules, dict)
    assert len(modules) > 0

def test_get_memory_capabilities():
    awareness = MemoryAwareness()
    with patch.object(awareness, 'memory_modules', {'mock_module': [('mock_func', lambda: None)]}):
        capabilities = awareness.get_memory_capabilities()
        assert isinstance(capabilities, dict)
        assert len(capabilities) > 0

def test_log_memory_status():
    awareness = MemoryAwareness()
    status = awareness.log_memory_status()
    assert status == "Memory status logged successfully"
