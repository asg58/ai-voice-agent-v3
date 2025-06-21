from flask import Flask, request

app = Flask(__name__)

@app.route('/api', methods=['POST'])
def handle_request():
    """
    API Gateway voor het beheren van verzoeken.
    """
    data = request.json
    # Mock implementatie
    return {"status": "success", "data": data}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
