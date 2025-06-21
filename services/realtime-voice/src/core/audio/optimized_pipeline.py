"""
Optimized Audio Processing Pipeline
Real-time voice processing with async queues and background workers
"""
import asyncio
import time
import logging
from typing import Dict, Any
from collections import defaultdict, deque
from dataclasses import dataclass
import psutil

logger = logging.getLogger(__name__)

@dataclass
class AudioProcessingTask:
    session_id: str
    audio_data: bytes
    websocket: Any
    timestamp: float
    priority: int = 1

class OptimizedAudioPipeline:
    """
    High-performance audio processing pipeline with:
    - Async task queues
    - Background workers
    - Priority processing
    - Circuit breaker pattern
    """
    
    def __init__(self, max_workers: int = 4, queue_size: int = 1000):
        self.max_workers = max_workers
        self.queue_size = queue_size
        
        # Processing queues
        self.high_priority_queue = asyncio.Queue(maxsize=queue_size // 4)
        self.normal_priority_queue = asyncio.Queue(maxsize=queue_size)
        
        # Worker management
        self.workers = []
        self.running = False
        
        # Performance tracking
        self.processing_times = deque(maxlen=1000)
        self.error_count = defaultdict(int)
        self.last_error_time = defaultdict(float)
        
        # Circuit breaker
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 30
        
    async def start(self):
        """Start background workers"""
        self.running = True
        
        # Start high-priority workers
        for i in range(max(1, self.max_workers // 2)):
            worker = asyncio.create_task(
                self._priority_worker(f"high-priority-{i}")
            )
            self.workers.append(worker)
            
        # Start normal-priority workers
        for i in range(self.max_workers // 2):
            worker = asyncio.create_task(
                self._normal_worker(f"normal-priority-{i}")
            )
            self.workers.append(worker)
            
        logger.info(f"Started {len(self.workers)} audio processing workers")
        
    async def stop(self):
        """Stop all workers gracefully"""
        self.running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
            
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("Stopped all audio processing workers")
        
    async def process_audio_async(self, task: AudioProcessingTask) -> bool:
        """
        Queue audio processing task
        Returns immediately with True if queued successfully
        """
        try:
            # Check circuit breaker
            if self._is_circuit_open(task.session_id):
                await self._send_error(task.websocket, "Service temporarily unavailable")
                return False
                
            # Send immediate acknowledgment
            await task.websocket.send_json({
                "type": "audio_received",
                "session_id": task.session_id,
                "status": "queued",
                "timestamp": task.timestamp
            })
            
            # Queue based on priority
            if task.priority > 5:  # High priority (e.g., voice commands)
                await self.high_priority_queue.put(task)
            else:
                await self.normal_priority_queue.put(task)
                
            return True
            
        except asyncio.QueueFull:
            await self._send_error(task.websocket, "Processing queue full, try again")
            return False
        except Exception as e:
            logger.error(f"Error queueing audio task: {e}")
            await self._send_error(task.websocket, "Internal server error")
            return False
            
    async def _priority_worker(self, worker_name: str):
        """High-priority audio processing worker"""
        logger.info(f"Started {worker_name}")
        
        while self.running:
            try:
                # Get task with timeout
                task = await asyncio.wait_for(
                    self.high_priority_queue.get(),
                    timeout=1.0
                )
                
                await self._process_audio_task(task, worker_name)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in {worker_name}: {e}")
                await asyncio.sleep(0.1)
                
    async def _normal_worker(self, worker_name: str):
        """Normal-priority audio processing worker"""
        logger.info(f"Started {worker_name}")
        
        while self.running:
            try:
                # Check if high-priority queue needs help
                if self.high_priority_queue.qsize() > 0:
                    try:
                        task = self.high_priority_queue.get_nowait()
                        await self._process_audio_task(task, worker_name)
                        continue
                    except asyncio.QueueEmpty:
                        pass
                        
                # Process normal priority
                task = await asyncio.wait_for(
                    self.normal_priority_queue.get(),
                    timeout=1.0
                )
                
                await self._process_audio_task(task, worker_name)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in {worker_name}: {e}")
                await asyncio.sleep(0.1)
                
    async def _process_audio_task(self, task: AudioProcessingTask, worker_name: str):
        """Process individual audio task"""
        start_time = time.time()
        
        try:
            # Check if WebSocket is still alive
            if task.websocket.client_state.value == 3:  # CLOSED
                logger.debug(f"WebSocket closed for session {task.session_id}")
                return
                
            # Send processing status
            await task.websocket.send_json({
                "type": "processing_started",
                "session_id": task.session_id,
                "worker": worker_name,
                "timestamp": time.time()
            })
            
            # Actual audio processing
            result = await self._process_audio_data(task.audio_data, task.session_id)
            
            # Send result
            await task.websocket.send_json({
                "type": "processing_complete",
                "session_id": task.session_id,
                "result": result,
                "processing_time": time.time() - start_time,
                "worker": worker_name,
                "timestamp": time.time()
            })
            
            # Track performance
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            
            # Reset error count on success
            if task.session_id in self.error_count:
                self.error_count[task.session_id] = 0
                
        except Exception as e:
            # Track errors
            self.error_count[task.session_id] += 1
            self.last_error_time[task.session_id] = time.time()
            
            logger.error(f"Error processing audio for {task.session_id}: {e}")
            
            await self._send_error(task.websocket, f"Processing error: {str(e)}")
            
    async def _process_audio_data(self, audio_data: bytes, session_id: str) -> Dict[str, Any]:
        """
        Actual audio processing logic
        This would integrate with your STT, TTS, and LLM services
        """
        # Simulate processing time (replace with actual implementation)
        await asyncio.sleep(0.1)  # Simulate fast processing
        
        return {
            "transcription": "Sample transcription",
            "response": "Sample AI response",
            "confidence": 0.95,
            "language": "nl"
        }
        
    def _is_circuit_open(self, session_id: str) -> bool:
        """Check if circuit breaker is open for session"""
        error_count = self.error_count.get(session_id, 0)
        last_error = self.last_error_time.get(session_id, 0)
        
        if error_count >= self.circuit_breaker_threshold:
            if time.time() - last_error < self.circuit_breaker_timeout:
                return True
            else:
                # Reset circuit breaker
                self.error_count[session_id] = 0
                
        return False
        
    async def _send_error(self, websocket, message: str):
        """Send error message to WebSocket"""
        try:
            await websocket.send_json({
                "type": "error",
                "message": message,
                "timestamp": time.time()
            })
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
            
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        if not self.processing_times:
            return {"status": "no_data"}
            
        times = list(self.processing_times)
        
        return {
            "average_processing_time": sum(times) / len(times),
            "min_processing_time": min(times),
            "max_processing_time": max(times),
            "total_processed": len(times),
            "queue_sizes": {
                "high_priority": self.high_priority_queue.qsize(),
                "normal_priority": self.normal_priority_queue.qsize()
            },
            "worker_count": len(self.workers),
            "circuit_breaker_status": dict(self.error_count),
            "memory_usage": psutil.virtual_memory().percent,
            "cpu_usage": psutil.cpu_percent()
        }

# Global instance
optimized_pipeline = OptimizedAudioPipeline()
