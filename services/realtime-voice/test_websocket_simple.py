#!/usr/bin/env python3
"""
WebSocket Test Client voor Simple Test Server (poort 8081)
Aangepaste versie van de originele test
"""
import asyncio
import json
import websockets
import uuid
from datetime import datetime


class VoiceAITestClient:
    """Test client voor de Simple Test Server"""
    
    def __init__(self, base_url="ws://localhost:8081"):
        self.base_url = base_url
        self.session_id = None
        self.websocket = None
    
    async def create_session(self):
        """Maak een nieuwe sessie aan"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8081/sessions",
                json={"user_id": "test_client"}
            )
            data = response.json()
            self.session_id = data["session_id"]
            print(f"✅ Session created: {self.session_id}")
            return self.session_id
    
    async def connect_websocket(self):
        """Verbind met WebSocket"""
        if not self.session_id:
            await self.create_session()
        
        ws_url = f"{self.base_url}/ws/{self.session_id}"
        print(f"🔌 Connecting to: {ws_url}")
        
        self.websocket = await websockets.connect(ws_url)
        print("✅ WebSocket connected!")
        
        # Start message listener
        asyncio.create_task(self.listen_messages())
    
    async def listen_messages(self):
        """Luister naar inkomende berichten"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            print("🔌 WebSocket connection closed")
        except Exception as e:
            print(f"❌ Error listening to messages: {e}")
    
    async def handle_message(self, data):
        """Handle inkomende berichten"""
        msg_type = data.get("type", "unknown")
        
        if msg_type == "status":
            print(f"📊 Status: {data.get('status')} - {data.get('message', '')}")
        elif msg_type == "text_response":
            print(f"🤖 AI Response: {data.get('text')}")
        elif msg_type == "audio_processed":
            print(f"🎤 Audio: {data.get('message')}")
        elif msg_type == "pong":
            print(f"🏓 Pong received at {data.get('timestamp')}")
        elif msg_type == "error":
            print(f"❌ Error: {data.get('error_message')}")
        else:
            print(f"📨 Message [{msg_type}]: {data}")
    
    async def send_message(self, message_type, **kwargs):
        """Verstuur bericht naar server"""
        if not self.websocket:
            print("❌ WebSocket not connected")
            return
        
        message = {
            "type": message_type,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        
        await self.websocket.send(json.dumps(message))
        print(f"📤 Sent [{message_type}]: {kwargs}")
    
    async def test_ping(self):
        """Test ping/pong"""
        await self.send_message("ping")
    
    async def test_text_message(self, text):
        """Test tekst bericht"""
        await self.send_message("text_message", text=text)
    
    async def test_audio_placeholder(self):
        """Test audio placeholder"""
        await self.send_message("audio_data", 
                               audio_data="placeholder_audio_data",
                               sample_rate=16000,
                               channels=1)
    
    async def test_status_request(self):
        """Test status request"""
        await self.send_message("status_request")
    
    async def close(self):
        """Sluit verbinding"""
        if self.websocket:
            await self.websocket.close()
            print("🔌 WebSocket disconnected")


async def run_simple_test():
    """Simpele geautomatiseerde test voor simple server"""
    client = VoiceAITestClient()
    
    print("🎙️ Simple WebSocket Test (Simple Server)")
    print("=" * 40)
    
    try:
        await client.connect_websocket()
        await asyncio.sleep(1)
        
        await client.test_ping()
        await asyncio.sleep(0.5)
        
        await client.test_text_message("Simple server test successful!")
        await asyncio.sleep(1)
        
        await client.test_audio_placeholder()
        await asyncio.sleep(0.5)
        
        await client.test_status_request()
        await asyncio.sleep(0.5)
        
        print("✅ Simple test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(run_simple_test())
