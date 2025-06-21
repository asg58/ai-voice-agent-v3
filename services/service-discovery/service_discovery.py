from flask import Flask, request, jsonify
from loguru import logger
import os
import json
import time
import threading

app = Flask(__name__)

class ServiceDiscovery:
    def __init__(self):
        self.services = {}
        self.load_initial_services()
        
    def load_initial_services(self):
        """Load initial services for demonstration purposes"""
        self.services = {
            "realtime-voice": {
                "id": "realtime-voice-ai",
                "name": "Realtime Voice AI",
                "host": "realtime-voice-ai",
                "port": 8080,
                "health_check": "/health",
                "status": "healthy",
                "last_check": int(time.time())
            },
            "api-gateway": {
                "id": "api-gateway",
                "name": "API Gateway",
                "host": "api-gateway",
                "port": 8000,
                "health_check": "/health",
                "status": "healthy",
                "last_check": int(time.time())
            },
            "edge-ai": {
                "id": "edge-ai",
                "name": "Edge AI",
                "host": "edge-ai",
                "port": 8500,
                "health_check": "/health",
                "status": "healthy",
                "last_check": int(time.time())
            }
        }
        
    def discover_services(self):
        """Return all registered services"""
        return list(self.services.values())
    
    def register_service(self, service_data):
        """Register a new service"""
        if not service_data or 'id' not in service_data or 'name' not in service_data:
            return False
        
        service_id = service_data['id']
        service_data['last_check'] = int(time.time())
        self.services[service_id] = service_data
        return True
    
    def deregister_service(self, service_id):
        """Deregister a service"""
        if service_id in self.services:
            del self.services[service_id]
            return True
        return False
    
    def get_service(self, service_id):
        """Get a specific service by ID"""
        return self.services.get(service_id)
    
    def update_service_health(self, service_id, status):
        """Update the health status of a service"""
        if service_id in self.services:
            self.services[service_id]['status'] = status
            self.services[service_id]['last_check'] = int(time.time())
            return True
        return False

# Initialize service discovery
service_discovery = ServiceDiscovery()

# Start health check background thread
def health_check_worker():
    """Background thread to periodically check service health"""
    import requests
    from requests.exceptions import RequestException, Timeout, ConnectionError
    
    # Create a session for connection pooling
    session = requests.Session()
    
    while True:
        try:
            for service_id, service in list(service_discovery.services.items()):
                try:
                    if 'host' in service and 'port' in service and 'health_check' in service:
                        url = f"http://{service['host']}:{service['port']}{service['health_check']}"
                        # Use connect and read timeouts
                        response = session.get(url, timeout=(2, 5))  # 2s connect, 5s read
                        if response.status_code == 200:
                            service_discovery.update_service_health(service_id, "healthy")
                        else:
                            logger.warning(f"Service {service_id} returned HTTP {response.status_code}")
                            service_discovery.update_service_health(service_id, "unhealthy")
                except (Timeout, ConnectionError) as e:
                    logger.warning(f"Connection failed for {service_id}: {str(e)}")
                    service_discovery.update_service_health(service_id, "unhealthy")
                except RequestException as e:
                    logger.warning(f"Request failed for {service_id}: {str(e)}")
                    service_discovery.update_service_health(service_id, "unknown")
                except Exception as e:
                    logger.error(f"Unexpected error during health check for {service_id}: {str(e)}")
                    service_discovery.update_service_health(service_id, "unknown")
        except Exception as e:
            logger.error(f"Error in health check worker: {str(e)}")
        
        # Sleep for 30 seconds before next check
        time.sleep(30)

# Start health check thread
health_check_thread = threading.Thread(target=health_check_worker)
health_check_thread.daemon = True
health_check_thread.start()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/services', methods=['GET'])
def get_services():
    services = service_discovery.discover_services()
    return jsonify({"services": services}), 200

@app.route('/services/<service_id>', methods=['GET'])
def get_service(service_id):
    service = service_discovery.get_service(service_id)
    if service:
        return jsonify({"service": service}), 200
    return jsonify({"error": "Service not found"}), 404

@app.route('/services', methods=['POST'])
def register_service():
    data = request.json
    if service_discovery.register_service(data):
        return jsonify({"status": "success", "message": "Service registered"}), 201
    return jsonify({"status": "error", "message": "Invalid service data"}), 400

@app.route('/services/<service_id>', methods=['DELETE'])
def deregister_service(service_id):
    if service_discovery.deregister_service(service_id):
        return jsonify({"status": "success", "message": "Service deregistered"}), 200
    return jsonify({"status": "error", "message": "Service not found"}), 404

@app.route('/services/<service_id>/health', methods=['PUT'])
def update_health(service_id):
    data = request.json
    if not data or 'status' not in data:
        return jsonify({"status": "error", "message": "Invalid health data"}), 400
    
    if service_discovery.update_service_health(service_id, data['status']):
        return jsonify({"status": "success", "message": "Health status updated"}), 200
    return jsonify({"status": "error", "message": "Service not found"}), 404

if __name__ == '__main__':
    logger.info("Starting Service Discovery...")
    port = int(os.environ.get('PORT', 8500))
    app.run(host='0.0.0.0', port=port, debug=False)