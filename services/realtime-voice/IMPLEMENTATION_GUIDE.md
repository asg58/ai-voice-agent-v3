# 🚀 **Implementatie-instructies: Voice-AI Container Verbeteringen**

## 📋 **Overzicht**

Deze verbeteringen zullen de performance, schaalbaarheid en betrouwbaarheid van de voice-ai container drastisch verbeteren.

---

## 🎯 **Fase 1: Optimized Audio Pipeline (Week 1-2)**

### **Stap 1: Installeer nieuwe pipeline**

```bash
# In services/realtime-voice/
pip install redis asyncio-mqtt psutil
```

### **Stap 2: Update main.py WebSocket endpoint**

Vervang de huidige WebSocket handler in `src/main.py`:

```python
# OUDE implementatie (regel ~1200)
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    # ... oude code ...

# NIEUWE implementatie
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    from src.core.audio.optimized_pipeline import optimized_pipeline
    from src.core.websocket.enhanced_manager import enhanced_websocket_manager

    # Check session exists
    if session_id not in active_sessions:
        await websocket.close(code=1008, reason="Session not found")
        return

    session = active_sessions[session_id]

    # Connect via enhanced manager
    success = await enhanced_websocket_manager.connect(
        websocket, session_id, session.user_id,
        tags={"voice_ai", "real_time"}
    )

    if not success:
        return

    try:
        while True:
            # Receive message
            message_data = await enhanced_websocket_manager.receive_from_session(session_id)

            if not message_data:
                continue

            if message_data.get("type") == "audio":
                # Process via optimized pipeline
                task = AudioProcessingTask(
                    session_id=session_id,
                    audio_data=message_data["data"],
                    websocket=websocket,
                    timestamp=time.time(),
                    priority=message_data.get("priority", 1)
                )

                await optimized_pipeline.process_audio_async(task)

            elif message_data.get("type") == "text":
                # Handle text messages
                await process_text_message_enhanced(websocket, session, message_data)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    finally:
        await enhanced_websocket_manager.disconnect(session_id)
```

### **Stap 3: Start nieuwe componenten bij applicatie start**

Update de `initialize_components()` functie in `main.py`:

```python
async def initialize_components():
    """Initialize all application components"""
    global audio_pipeline

    # Existing initialization...

    # Initialize optimized pipeline
    from src.core.audio.optimized_pipeline import optimized_pipeline
    await optimized_pipeline.start()

    # Initialize enhanced WebSocket manager
    from src.core.websocket.enhanced_manager import enhanced_websocket_manager
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    enhanced_websocket_manager.redis_client = redis.from_url(redis_url)
    await enhanced_websocket_manager.start()

    # Initialize monitoring
    from src.core.monitoring.advanced_metrics import voice_ai_metrics, metrics_collector
    asyncio.create_task(metrics_collector())

    logger.info("Enhanced components initialized")
```

---

## 🎯 **Fase 2: Monitoring Dashboard (Week 3-4)**

### **Stap 1: Voeg monitoring endpoints toe**

Voeg deze endpoints toe aan `main.py`:

```python
@app.get("/metrics")
async def get_prometheus_metrics():
    """Prometheus metrics endpoint"""
    from src.core.monitoring.advanced_metrics import voice_ai_metrics
    return Response(
        voice_ai_metrics.export_prometheus_metrics(),
        media_type="text/plain"
    )

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with performance metrics"""
    from src.core.monitoring.advanced_metrics import voice_ai_metrics
    from src.core.websocket.enhanced_manager import enhanced_websocket_manager
    from src.core.audio.optimized_pipeline import optimized_pipeline

    health_data = voice_ai_metrics.get_health_status()

    # Add component-specific health
    health_data["components"].update({
        "websocket_manager": enhanced_websocket_manager.get_stats(),
        "audio_pipeline": optimized_pipeline.get_performance_metrics()
    })

    return health_data

@app.get("/performance/summary")
async def performance_summary():
    """Performance summary for monitoring dashboard"""
    from src.core.monitoring.advanced_metrics import voice_ai_metrics
    return voice_ai_metrics.get_performance_summary()
```

### **Stap 2: Update Docker Compose voor monitoring**

Update `docker-compose.all.yml`:

```yaml
voice-ai:
  # ... existing config ...
  labels:
    - 'prometheus.io/scrape=true'
    - 'prometheus.io/path=/metrics'
    - 'prometheus.io/port=8080'
  environment:
    # ... existing env vars ...
    - ENABLE_PROMETHEUS=true
    - METRICS_COLLECTION_INTERVAL=30
```

---

## 🎯 **Fase 3: Performance Testing (Week 5)**

### **Stap 1: Test script maken**

```python
# test_performance.py
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor

async def test_websocket_performance():
    """Test WebSocket performance under load"""
    concurrent_connections = 50
    messages_per_connection = 100

    async def websocket_client(session_id):
        uri = f"ws://localhost:8091/ws/{session_id}"

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(uri) as ws:
                start_time = time.time()

                # Send test messages
                for i in range(messages_per_connection):
                    await ws.send_json({
                        "type": "text",
                        "content": f"Test message {i}",
                        "timestamp": time.time()
                    })

                    # Receive response
                    response = await ws.receive()

                duration = time.time() - start_time
                return duration

    # Run concurrent connections
    tasks = []
    for i in range(concurrent_connections):
        task = asyncio.create_task(websocket_client(f"test_session_{i}"))
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    print(f"Performance Test Results:")
    print(f"Concurrent connections: {concurrent_connections}")
    print(f"Messages per connection: {messages_per_connection}")
    print(f"Average duration: {sum(results)/len(results):.2f}s")
    print(f"Max duration: {max(results):.2f}s")
    print(f"Min duration: {min(results):.2f}s")

if __name__ == "__main__":
    asyncio.run(test_websocket_performance())
```

### **Stap 2: Performance benchmarks**

```bash
# Run performance test
cd services/realtime-voice/
python test_performance.py

# Monitor during test
curl http://localhost:8091/health/detailed
curl http://localhost:8091/performance/summary
```

---

## 🎯 **Fase 4: Production Deployment (Week 6)**

### **Stap 1: Update production configuration**

```yaml
# docker-compose.production.yml
services:
  voice-ai:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - REDIS_URL=redis://redis:6379/0
      - MAX_WORKERS=8
      - QUEUE_SIZE=2000
      - MAX_WEBSOCKET_CONNECTIONS=500
```

### **Stap 2: Monitoring setup**

```yaml
# Prometheus config voor voice-ai metrics
- job_name: 'voice-ai'
  static_configs:
    - targets: ['voice-ai:8080']
  metrics_path: '/metrics'
  scrape_interval: 30s
```

---

## 📊 **Verwachte Resultaten**

### **Performance Improvements:**

- ⚡ **Latency**: Van ~1.5s naar ~300ms (5x sneller)
- 📈 **Throughput**: Van ~10 naar ~100 concurrent users (10x meer)
- 💾 **Memory**: 50% effiënter gebruik
- 🔄 **Error Rate**: Van 5% naar <1%

### **Monitoring Capabilities:**

- 📊 Real-time performance dashboards
- 🚨 Proactive alerting bij problemen
- 📈 Trend analysis voor capacity planning
- 🔍 Detailed error tracking en debugging

### **Scalability:**

- 🌐 Horizontale scaling tot 10+ replicas
- ⚖️ Automatische load balancing
- 🗄️ Distributed session management
- 🔧 Zero-downtime deployments

---

## ⚠️ **Implementatie Tips**

1. **Gefaseerde uitrol**: Test elke fase grondig voordat je verder gaat
2. **Monitoring eerst**: Implementeer monitoring voordat je performance changes maakt
3. **Backwards compatibility**: Behoud oude endpoints tijdens transitie
4. **Performance baselines**: Meet huidige performance voordat je wijzigingen maakt
5. **Rollback plan**: Heb altijd een rollback strategie klaar

---

## 🔧 **Troubleshooting**

### **Veel voorkomende problemen:**

**1. High Memory Usage**

```python
# Check memory leaks
curl http://localhost:8091/health/detailed | jq .system_stats.peak_memory_usage
```

**2. WebSocket Connection Issues**

```python
# Check connection stats
curl http://localhost:8091/health/detailed | jq .components.websocket_manager
```

**3. Queue Backlog**

```python
# Check processing queues
curl http://localhost:8091/performance/summary | jq .metrics.audio_processing
```

Met deze verbeteringen krijg je een enterprise-grade voice AI service die schaalbaar, betrouwbaar en monitoorbaar is! 🚀
