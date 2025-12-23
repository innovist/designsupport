#!/usr/bin/env python3
"""
Fashion AI Generation System - Launch Script
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"Python version: {sys.version}")


def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


def setup_environment():
    """Setup environment variables"""
    env_file = Path(".env")
    if not env_file.exists():
        print("Creating .env file with default values...")
        with open(env_file, "w") as f:
            f.write("""# Fashion AI Generation System Configuration

# Database
DATABASE_URL=sqlite:///./fashion_ai.db
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=fashion-ai-secret-key-change-in-production

# AI API Keys (Set these in the application settings)
GEMINI_API_KEY=
GLM_API_KEY=
Z_IMAGE_API_KEY=
SEEDREAM_API_KEY=
NANO_BANANA_API_KEY=

# Server Settings
HOST=0.0.0.0
PORT=8000
DEBUG=false
ENVIRONMENT=development

# Crawler Settings
MAX_CRAWL_PAGES=100
CRAWL_DELAY_SECONDS=1
MAX_CONCURRENT_CRAWLS=10

# AI Settings
MAX_PROMPT_LENGTH=4000
ANALYSIS_TIMEOUT_SECONDS=300
GENERATION_TIMEOUT_SECONDS=600
MAX_RETRIES=3

# Quality Thresholds
CONSISTENCY_THRESHOLD=0.85
PROMPT_FIDELITY_THRESHOLD=0.90
REPRODUCTION_THRESHOLD=0.95

# Storage
UPLOAD_DIR=./uploads
STATIC_DIR=./static
MAX_FILE_SIZE_MB=10

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
LOG_ROTATION=daily
LOG_RETENTION_DAYS=30

# GPU Settings
GPU_ENABLED=true
CUDA_VISIBLE_DEVICES=0

# External URLs
COMFYUI_API_URL=http://localhost:8188
SEEDREAM_API_URL=https://api.seedream.com
NANO_BANANA_API_URL=https://api.nano-banana.com

# Features
ENABLE_CRAWLING=true
ENABLE_ANALYSIS=true
ENABLE_GENERATION=true
ENABLE_BLUEPRINT=true
ENABLE_I18N=true
""")


def create_directories():
    """Create necessary directories"""
    directories = [
        "storage/references",
        "storage/results",
        "storage/temp",
        "logs",
        "uploads"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")


def main():
    """Main entry point"""
    print("=" * 60)
    print("Fashion AI Generation System")
    print("=" * 60)

    # Check Python version
    check_python_version()

    # Create directories
    create_directories()

    # Setup environment
    setup_environment()

    # Install dependencies
    if "--no-install" not in sys.argv:
        install_dependencies()

    # Start the server
    print("\nStarting Fashion AI Generation System...")
    print("Access the application at: http://localhost:8000")
    print("API Documentation at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server\n")

    try:
        import uvicorn
        uvicorn.run(
            "server:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    main()