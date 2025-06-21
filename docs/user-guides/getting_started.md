# Getting Started

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-repo/ai-voice-agent-v3.git
   ```

2. Navigate to the project directory:

   ```bash
   cd ai-voice-agent-v3
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements/basic.txt
   ```

## Running the Service

1. Start the service:

   ```bash
   uvicorn services.realtime-voice.main:app --reload
   ```

2. Access the API documentation:
   - Open your browser and navigate to `http://localhost:8000/docs`.

## Testing

1. Run the test suite:
   ```bash
   pytest tests/
   ```

## Troubleshooting

- **Issue**: Service not starting

  - **Solution**: Check if all dependencies are installed.

- **Issue**: Tests failing
  - **Solution**: Ensure the test environment is correctly configured.
