#!/usr/bin/env python3
"""
Startup script for Virtual Patient Simulator API
Works in both local development and Railway deployment.
"""

import os
import sys
import uvicorn
from pathlib import Path

# -----------------------------
# 🧭 Path Configuration
# -----------------------------
current_dir = Path(__file__).parent
api_dir = current_dir / "api"
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(api_dir))

# -----------------------------
# 🔐 Environment Variable Setup
# -----------------------------
# Check for .env file in local dev only
if not os.getenv("RAILWAY_ENVIRONMENT"):
    env_locations = [
        current_dir / ".env",
        current_dir / "src" / ".env",
        current_dir / ".." / ".env"
    ]

    env_file = None
    for location in env_locations:
        if location.exists():
            env_file = location
            print(f"✓ Found .env file at: {location}")
            from dotenv import load_dotenv
            load_dotenv(location)
            break

    if not env_file:
        print("⚠️  Warning: .env file not found!")
        print("Please create a .env file with your OpenAI API key in one of these locations:")
        for loc in env_locations:
            print(f"  - {loc}")
        print("File content should be:")
        print("OPENAI_API_KEY=your_api_key_here")
        print()

# -----------------------------
# 🚀 API Startup
# -----------------------------
if __name__ == "__main__":
    environment = "Railway" if os.getenv("RAILWAY_ENVIRONMENT") else "Local"
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0" if environment == "Railway" else "127.0.0.1"

    print(f"🚀 Starting Virtual Patient Simulator API ({environment} mode)...")
    print(f"📁 Working directory: {current_dir}")
    print(f"🌐 API available at: http://{host}:{port}")
    print(f"📖 Docs: http://{host}:{port}/docs")
    print(f"🔧 ReDoc: http://{host}:{port}/redoc\n")

    try:
        uvicorn.run(
            "api.app:app",
            host=host,
            port=port,
            log_level="info",
            reload=(environment == "Local"),
            reload_dirs=[str(api_dir)] if environment == "Local" else None
        )
    except KeyboardInterrupt:
        print("\n👋 API server stopped manually")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("\nTroubleshooting:")
        print("1. Check if the required dependencies are installed: pip install -r requirements.txt")
        print("2. Verify that all import paths are correct")
        print("3. Ensure environment variables (like OPENAI_API_KEY) are set")
        sys.exit(1)
