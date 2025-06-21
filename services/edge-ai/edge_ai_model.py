from flask import Flask, request, jsonify
from loguru import logger
import os

app = Flask(__name__)

class EdgeAIModel:
    def process_on_edge(self, data):
        """
        Verwerk AI-modellen direct op edge-apparaten.
        """
        # Mock implementatie
        return f"Processed data on edge: {data}"

edge_model = EdgeAIModel()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/process', methods=['POST'])
def process_data():
    data = request.json
    if not data or 'input' not in data:
        return jsonify({"error": "Invalid input data"}), 400
    
    result = edge_model.process_on_edge(data['input'])
    return jsonify({"result": result}), 200

if __name__ == '__main__':
    logger.info("Starting Edge AI Service...")
    port = int(os.environ.get('PORT', 8500))
    app.run(host='0.0.0.0', port=port, debug=False)