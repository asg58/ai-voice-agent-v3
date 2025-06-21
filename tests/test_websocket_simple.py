import pytest
import asyncio

async def connect_websocket():
    class MockWebSocket:
        def __init__(self):
            self.is_connected = True

        async def send_message(self, message):
            return "expected_response"

        async def disconnect(self):
            self.is_connected = False

    return MockWebSocket()

@pytest.mark.asyncio
async def test_websocket_connection():
    # Test WebSocket-verbinding
    websocket = await connect_websocket()
    assert websocket.is_connected

@pytest.mark.asyncio
async def test_websocket_message_handling():
    # Test berichtverwerking
    websocket = await connect_websocket()
    message = "complex_message"
    response = await websocket.send_message(message)
    assert response == "expected_response"

@pytest.mark.asyncio
async def test_websocket_disconnection():
    # Test WebSocket-verbreking
    websocket = await connect_websocket()
    await websocket.disconnect()
    assert not websocket.is_connected