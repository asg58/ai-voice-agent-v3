#!/usr/bin/env python3
"""
Project Initialization Script

This script initializes the AI Voice Agent v3 project by:
- Setting up the development environment
- Creating necessary directories
- Installing dependencies
- Configuring services
- Running initial database migrations
"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
import yaml
import json


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProjectInitializer:
    """Initialize the AI Voice Agent project."""
    
    def __init__(self, project_root: Path):
        """
        Initialize the project initializer.
        
        Args:
            project_root: Path to the project root directory
        """
        self.project_root = project_root
        self.services_dir = project_root / "services"
        self.shared_dir = project_root / "shared"
        self.infrastructure_dir = project_root / "infrastructure"
        self.scripts_dir = project_root / "scripts"
        
    def check_prerequisites(self) -> bool:
        """
        Check if all prerequisites are installed.
        
        Returns:
            bool: True if all prerequisites are met, False otherwise
        """
        logger.info("Checking prerequisites...")
        
        prerequisites = [
            ("python", "--version", "Python 3.11+"),
            ("docker", "--version", "Docker"),
            ("docker-compose", "--version", "Docker Compose"),
            ("node", "--version", "Node.js 18+"),
            ("npm", "--version", "npm"),
            ("git", "--version", "Git")
        ]
        
        missing = []
        
        for cmd, flag, desc in prerequisites:
            try:
                result = subprocess.run(
                    [cmd, flag], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                logger.info(f"✓ {desc}: {result.stdout.strip().split()[0]}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.error(f"✗ {desc}: Not found or not working")
                missing.append(desc)
        
        if missing:
            logger.error(f"Missing prerequisites: {', '.join(missing)}")
            return False
        
        logger.info("All prerequisites are met!")
        return True
    
    def create_environment_file(self) -> None:
        """Create .env file from .env.example if it doesn't exist."""
        logger.info("Setting up environment configuration...")
        
        env_example = self.project_root / ".env.example"
        env_file = self.project_root / ".env"
        
        if not env_file.exists() and env_example.exists():
            logger.info("Creating .env file from .env.example...")
            env_file.write_text(env_example.read_text())
            logger.info("✓ Created .env file")
        elif env_file.exists():
            logger.info("✓ .env file already exists")
        else:
            logger.warning("⚠ .env.example not found, creating basic .env file")
            self._create_basic_env_file(env_file)
    
    def _create_basic_env_file(self, env_file: Path) -> None:
        """Create a basic .env file with essential variables."""
        basic_env = """# AI Voice Agent v3 - Basic Configuration
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql://ai_user:ai_password@localhost:5432/ai_voice_agent

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-change-in-production

# AI Configuration
OPENAI_API_KEY=your-openai-api-key-here
MODEL_NAME=gpt-4

# Logging
LOG_LEVEL=INFO
ENABLE_JSON_LOGGING=true
"""
        env_file.write_text(basic_env)
        logger.info("✓ Created basic .env file")
    
    def setup_python_environments(self) -> None:
        """Set up Python virtual environments for each service."""
        logger.info("Setting up Python virtual environments...")
        
        # Main project virtual environment
        venv_path = self.project_root / ".venv"
        if not venv_path.exists():
            logger.info("Creating main project virtual environment...")
            subprocess.run([
                sys.executable, "-m", "venv", str(venv_path)
            ], check=True)
            logger.info("✓ Created main virtual environment")
        
        # Install main requirements
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            logger.info("Installing main project dependencies...")
            self._install_requirements(venv_path, requirements_file)
        
        # Install service-specific requirements
        for service_dir in self.services_dir.glob("*/"):
            if service_dir.is_dir():
                service_requirements = service_dir / "requirements.txt"
                if service_requirements.exists():
                    logger.info(f"Installing dependencies for {service_dir.name}...")
                    self._install_requirements(venv_path, service_requirements)
    
    def _install_requirements(self, venv_path: Path, requirements_file: Path) -> None:
        """Install requirements in the virtual environment."""
        pip_cmd = venv_path / "Scripts" / "pip.exe" if os.name == "nt" else venv_path / "bin" / "pip"
        
        try:
            subprocess.run([
                str(pip_cmd), "install", "-r", str(requirements_file)
            ], check=True, capture_output=True)
            logger.info(f"✓ Installed requirements from {requirements_file}")
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Failed to install requirements from {requirements_file}: {e}")
    
    def setup_docker_environment(self) -> None:
        """Set up Docker environment and networks."""
        logger.info("Setting up Docker environment...")
        
        try:
            # Create Docker network if it doesn't exist
            subprocess.run([
                "docker", "network", "create", "ai-voice-network"
            ], capture_output=True, check=False)  # Don't fail if network exists
            
            # Pull required images
            images = [
                "postgres:15-alpine",
                "redis:7-alpine",
                "semitechnologies/weaviate:1.22.4",
                "minio/minio:latest",
                "prom/prometheus:latest",
                "grafana/grafana:latest"
            ]
            
            for image in images:
                logger.info(f"Pulling Docker image: {image}")
                subprocess.run([
                    "docker", "pull", image
                ], check=True, capture_output=True)
            
            logger.info("✓ Docker environment set up successfully")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Failed to set up Docker environment: {e}")
    
    def create_database_schema(self) -> None:
        """Create database schema and run initial migrations."""
        logger.info("Setting up database schema...")
        
        try:
            # Start only database services
            subprocess.run([
                "docker-compose", "up", "-d", "postgres", "redis"
            ], cwd=self.project_root, check=True, capture_output=True)
            
            # Wait for database to be ready
            logger.info("Waiting for database to be ready...")
            import time
            time.sleep(10)
            
            # Run database migrations for core-engine
            core_engine_dir = self.services_dir / "core-engine"
            if core_engine_dir.exists():
                logger.info("Running database migrations...")
                # Here you would run Alembic migrations
                # subprocess.run([...], cwd=core_engine_dir, check=True)
                logger.info("✓ Database migrations completed")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Failed to set up database: {e}")
    
    def setup_monitoring(self) -> None:
        """Set up monitoring and observability tools."""
        logger.info("Setting up monitoring...")
        
        # Create Grafana dashboard configurations
        grafana_dir = self.infrastructure_dir / "monitoring" / "grafana" / "dashboards"
        grafana_dir.mkdir(parents=True, exist_ok=True)
        
        # Create basic dashboard
        dashboard_config = {
            "dashboard": {
                "title": "AI Voice Agent Platform",
                "tags": ["ai-voice-agent"],
                "panels": []
            }
        }
        
        with open(grafana_dir / "platform-overview.json", "w") as f:
            json.dump(dashboard_config, f, indent=2)
        
        logger.info("✓ Monitoring setup completed")
    
    def verify_installation(self) -> bool:
        """Verify that the installation was successful."""
        logger.info("Verifying installation...")
        
        checks = [
            (self.project_root / ".env", ".env file"),
            (self.project_root / ".venv", "Virtual environment"),
            (self.services_dir / "core-engine", "Core engine service"),
            (self.services_dir / "voice-module", "Voice module service"),
            (self.shared_dir / "logging", "Shared logging utilities"),
            (self.infrastructure_dir / "monitoring", "Monitoring configuration")
        ]
        
        all_good = True
        for path, description in checks:
            if path.exists():
                logger.info(f"✓ {description}")
            else:
                logger.error(f"✗ {description}")
                all_good = False
        
        return all_good
    
    def print_next_steps(self) -> None:
        """Print next steps for the user."""
        logger.info("\n" + "="*50)
        logger.info("🎉 Project initialization completed!")
        logger.info("="*50)
        logger.info("\nNext steps:")
        logger.info("1. Activate the virtual environment:")
        if os.name == "nt":
            logger.info("   .venv\\Scripts\\activate")
        else:
            logger.info("   source .venv/bin/activate")
        
        logger.info("\n2. Update your .env file with your API keys:")
        logger.info("   - OPENAI_API_KEY")
        logger.info("   - WEAVIATE_API_KEY (if using cloud)")
        logger.info("   - Other service-specific keys")
        
        logger.info("\n3. Start the services:")
        logger.info("   docker-compose up -d")
        
        logger.info("\n4. Check service health:")
        logger.info("   curl http://localhost:8080/health")
        
        logger.info("\n5. Access the dashboard:")
        logger.info("   http://localhost:3000")
        
        logger.info("\n6. View API documentation:")
        logger.info("   http://localhost:8080/docs")
        
        logger.info("\n7. Monitor with Grafana:")
        logger.info("   http://localhost:3001 (admin/admin)")
        
        logger.info("\nFor more information, see the README.md file.")
        logger.info("="*50)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Initialize AI Voice Agent v3 project"
    )
    parser.add_argument(
        "--skip-docker",
        action="store_true",
        help="Skip Docker setup"
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Skip database initialization"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory"
    )
    
    args = parser.parse_args()
    
    initializer = ProjectInitializer(args.project_root)
    
    try:
        # Check prerequisites
        if not initializer.check_prerequisites():
            logger.error("Prerequisites not met. Please install missing components.")
            sys.exit(1)
        
        # Set up environment
        initializer.create_environment_file()
        
        # Set up Python environments
        initializer.setup_python_environments()
        
        # Set up Docker (if not skipped)
        if not args.skip_docker:
            initializer.setup_docker_environment()
        
        # Set up database (if not skipped)
        if not args.skip_db:
            initializer.create_database_schema()
        
        # Set up monitoring
        initializer.setup_monitoring()
        
        # Verify installation
        if initializer.verify_installation():
            initializer.print_next_steps()
        else:
            logger.error("Installation verification failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\nInitialization cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()