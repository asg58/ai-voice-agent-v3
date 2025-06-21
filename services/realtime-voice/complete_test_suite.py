#!/usr/bin/env python3
"""
WebSocket Test Client voor Simple Test Server
Test alle basis functionaliteiten
"""
import asyncio
import json
import websockets
import httpx
from datetime import datetime


class SimpleTestClient:
    """Test client voor de Simple Test Server"""
    
    def __init__(self, base_url="http://localhost:8081"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http://", "ws://")
        self.session_id = None
        self.websocket = None
    
    async def test_health_endpoint(self):
        """Test de health endpoint"""
        print("\n🔍 Testing health endpoint...")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            data = response.json()
            print(f"✅ Health check: {data['status']}")
            print(f"   Components: {data['components']}")
            return response.status_code == 200
    
    async def test_root_endpoint(self):
        """Test de root endpoint"""
        print("\n🔍 Testing root endpoint...")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/")
            data = response.json()
            print(f"✅ Service: {data['service']}")
            print(f"   Version: {data['version']}")
            print(f"   Status: {data['status']}")
            return response.status_code == 200
    
    async def create_session(self):
        """Maak een nieuwe sessie aan"""
        print("\n🔍 Testing session creation...")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/sessions",
                json={"user_id": "test_client"}
            )
            data = response.json()
            self.session_id = data["session_id"]
            print(f"✅ Session created: {self.session_id}")
            return self.session_id
    
    async def test_websocket_connection(self):
        """Test WebSocket verbinding"""
        print("\n🔍 Testing WebSocket connection...")
        if not self.session_id:
            await self.create_session()
        
        ws_url = f"{self.ws_url}/ws/{self.session_id}"
        print(f"   Connecting to: {ws_url}")
        
        try:
            self.websocket = await websockets.connect(ws_url)
            print("✅ WebSocket connected!")
            
            # Wacht op welcome message
            welcome_msg = await self.websocket.recv()
            welcome_data = json.loads(welcome_msg)
            print(f"   Welcome: {welcome_data.get('message', 'No message')}")
            
            return True
        except Exception as e:
            print(f"❌ WebSocket connection failed: {e}")
            return False
    
    async def test_ping_pong(self):
        """Test ping/pong functionaliteit"""
        print("\n🔍 Testing ping/pong...")
        if not self.websocket:
            return False
        
        try:
            ping_msg = {
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            }
            await self.websocket.send(json.dumps(ping_msg))
            print("   📤 Ping sent")
            
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "pong":
                print(f"   ✅ Pong received: {data.get('timestamp')}")
                return True
            else:
                print(f"   ❌ Unexpected response: {data}")
                return False
        except Exception as e:
            print(f"   ❌ Ping/pong failed: {e}")
            return False
    
    async def test_text_messaging(self):
        """Test tekst berichten"""
        print("\n🔍 Testing text messaging...")
        if not self.websocket:
            return False
        
        try:
            test_messages = [
                "Hello, this is a test message!",
                "Kunnen we Nederlandse tekst verwerken?",
                "Test met emoji 🚀🎤🤖",
                "Korte test",
                "Dit is een langere test om te kijken of het systeem goed omgaat met meer tekst en verschillende karakters."
            ]
            
            success_count = 0
            for i, text in enumerate(test_messages, 1):
                print(f"\n   Test {i}: Sending '{text[:50]}...'")
                
                msg = {
                    "type": "text_message",
                    "text": text,
                    "timestamp": datetime.now().isoformat()
                }
                await self.websocket.send(json.dumps(msg))
                
                response = await self.websocket.recv()
                data = json.loads(response)
                
                if data.get("type") == "text_response":
                    print(f"   ✅ Response: {data.get('text', 'No text')}")
                    success_count += 1
                else:
                    print(f"   ❌ Unexpected response: {data}")
                
                await asyncio.sleep(0.1)  # Small delay between messages
            
            print(f"\n   📊 Text messaging: {success_count}/{len(test_messages)} successful")
            return success_count == len(test_messages)
            
        except Exception as e:
            print(f"   ❌ Text messaging failed: {e}")
            return False
    
    async def test_audio_simulation(self):
        """Test audio data verwerking (gesimuleerd)"""
        print("\n🔍 Testing audio data processing...")
        if not self.websocket:
            return False
        
        try:
            audio_msg = {
                "type": "audio_data",
                "audio_data": "simulated_audio_base64_data",
                "sample_rate": 16000,
                "channels": 1,
                "timestamp": datetime.now().isoformat()
            }
            await self.websocket.send(json.dumps(audio_msg))
            print("   📤 Audio data sent")
            
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "audio_processed":
                print(f"   ✅ Audio processed: {data.get('message')}")
                return True
            else:
                print(f"   ❌ Unexpected response: {data}")
                return False
        except Exception as e:
            print(f"   ❌ Audio processing failed: {e}")
            return False
    
    async def test_status_request(self):
        """Test status verzoek"""
        print("\n🔍 Testing status request...")
        if not self.websocket:
            return False
        
        try:
            status_msg = {
                "type": "status_request",
                "timestamp": datetime.now().isoformat()
            }
            await self.websocket.send(json.dumps(status_msg))
            print("   📤 Status request sent")
            
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "status":
                print(f"   ✅ Status: {data.get('status')} - {data.get('message')}")
                return True
            else:
                print(f"   ❌ Unexpected response: {data}")
                return False
        except Exception as e:
            print(f"   ❌ Status request failed: {e}")
            return False
    
    async def test_error_handling(self):
        """Test error handling met ongeldige berichten"""
        print("\n🔍 Testing error handling...")
        if not self.websocket:
            return False
        
        try:
            # Test unknown message type
            invalid_msg = {
                "type": "unknown_message_type",
                "data": "test data",
                "timestamp": datetime.now().isoformat()
            }
            await self.websocket.send(json.dumps(invalid_msg))
            print("   📤 Invalid message sent")
            
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "error":
                print(f"   ✅ Error handled: {data.get('error_message')}")
                return True
            else:
                print(f"   ❌ Expected error response, got: {data}")
                return False
        except Exception as e:
            print(f"   ❌ Error handling test failed: {e}")
            return False
    
    async def close(self):
        """Sluit verbinding"""
        if self.websocket:
            await self.websocket.close()
            print("\n🔌 WebSocket disconnected")


async def run_complete_test_suite():
    """Voer een complete test suite uit"""
    client = SimpleTestClient()
    
    print("🧪 COMPLETE FUNCTIONALITY TEST SUITE")
    print("=" * 60)
    
    test_results = []
    
    try:
        # Test 1: Root endpoint
        result = await client.test_root_endpoint()
        test_results.append(("Root Endpoint", result))
        
        # Test 2: Health endpoint
        result = await client.test_health_endpoint()
        test_results.append(("Health Endpoint", result))
        
        # Test 3: Session creation
        result = await client.create_session()
        test_results.append(("Session Creation", bool(result)))
        
        # Test 4: WebSocket connection
        result = await client.test_websocket_connection()
        test_results.append(("WebSocket Connection", result))
        
        if result:  # Only proceed if WebSocket connected
            # Test 5: Ping/Pong
            result = await client.test_ping_pong()
            test_results.append(("Ping/Pong", result))
            
            # Test 6: Text messaging
            result = await client.test_text_messaging()
            test_results.append(("Text Messaging", result))
            
            # Test 7: Audio simulation
            result = await client.test_audio_simulation()
            test_results.append(("Audio Processing", result))
            
            # Test 8: Status request
            result = await client.test_status_request()
            test_results.append(("Status Request", result))
            
            # Test 9: Error handling
            result = await client.test_error_handling()
            test_results.append(("Error Handling", result))
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
    
    finally:
        await client.close()
    
    # Test results summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"TOTAL: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! System is ready for production.")
    elif passed >= total * 0.8:
        print("⚠️  Most tests passed. Minor issues detected.")
    else:
        print("❌ Multiple failures detected. System needs attention.")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(run_complete_test_suite())
