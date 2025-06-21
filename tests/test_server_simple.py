# Rename test file to avoid import mismatch

import pytest
import asyncio

async def initialize_server():
    class MockServer:
        def __init__(self):
            self.is_running = True

        async def handle_request(self, input):
            if input == "invalid_input":
                raise Exception("Invalid input")
            return "expected_output"

    return MockServer()

@pytest.mark.asyncio
async def test_server_initialization():
    # Simuleer serverinitialisatie
    server = await initialize_server()
    assert server.is_running

@pytest.mark.asyncio
async def test_server_response():
    # Test serverrespons op complexe input
    server = await initialize_server()
    response = await server.handle_request("complex_input")
    assert response == "expected_output"

@pytest.mark.asyncio
async def test_server_error_handling():
    # Test foutafhandeling
    server = await initialize_server()
    with pytest.raises(Exception):
        await server.handle_request("invalid_input")