#!/usr/bin/env python3
"""
Development setup script for Real-time Conversational AI
"""
import os
import subprocess
import sys
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return None

def setup_environment():
    """Setup development environment"""
    print("🚀 Setting up Real-time Conversational AI Development Environment")
    
    # Change to service directory
    service_dir = Path(__file__).parent / "services" / "realtime-voice"
    os.chdir(service_dir)
    
    # Copy environment file
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            shutil.copy(".env.example", ".env")
            print("✅ Created environment file")
        else:
            print("⚠️  .env.example not found, skipping environment file creation")
    
    # Create virtual environment
    if not os.path.exists("venv"):
        run_command("python -m venv venv", "Creating virtual environment")
    
    # Activate and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = ".\\venv\\Scripts\\activate"
        pip_cmd = ".\\venv\\Scripts\\pip"
    else:  # Unix/Linux/Mac
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip")
    run_command(f"{pip_cmd} install -r requirements.txt", "Installing Python dependencies")
    
    # Create storage directories
    os.makedirs("storage/audio", exist_ok=True)
    os.makedirs("storage/models", exist_ok=True)
    os.makedirs("storage/logs", exist_ok=True)
    print("✅ Created storage directories")
    
    print("\n🎉 Development environment setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your configuration")
    print("2. Run: python -m uvicorn src.main:app --reload")
    print("3. Open http://localhost:8080 in your browser")

def setup_docker():
    """Setup Docker environment"""
    print("🐳 Setting up Docker environment")
    
    # Go to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Build Docker images
    run_command("docker-compose -f docker-compose.realtime-voice.yml build", "Building Docker images")
    
    # Start services
    run_command("docker-compose -f docker-compose.realtime-voice.yml up -d", "Starting Docker services")
    
    print("\n🎉 Docker environment setup complete!")
    print("\nServices running:")
    print("- Real-time Voice AI: http://localhost:8080")
    print("- Grafana Dashboard: http://localhost:3000 (admin/admin123)")
    print("- Prometheus: http://localhost:9091")

def download_models():
    """Download required AI models"""
    print("📥 Downloading AI models...")
    
    # Download Ollama models
    models = ["llama3", "mistral"]
    for model in models:
        run_command(f"docker exec ollama-llm ollama pull {model}", f"Downloading {model}")
    
    print("✅ AI models downloaded successfully")

def run_tests():
    """Run tests"""
    print("🧪 Running tests...")
    
    service_dir = Path(__file__).parent / "services" / "realtime-voice"
    os.chdir(service_dir)
    
    # Run Python tests
    run_command("python -m pytest tests/ -v", "Running Python tests")
    
    # Run health checks
    run_command("curl -f http://localhost:8080/health", "Testing health endpoint")

def main():
    """Main setup function"""
    if len(sys.argv) < 2:
        print("Usage: python setup.py [local|docker|models|test]")
        print("\nCommands:")
        print("  local  - Setup local development environment")
        print("  docker - Setup Docker environment")
        print("  models - Download AI models")
        print("  test   - Run tests")
        return
    
    command = sys.argv[1]
    
    if command == "local":
        setup_environment()
    elif command == "docker":
        setup_docker()
    elif command == "models":
        download_models()
    elif command == "test":
        run_tests()
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
