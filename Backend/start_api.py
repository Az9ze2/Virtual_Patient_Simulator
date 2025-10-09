#!/usr/bin/env python3
"""
Startup script for Virtual Patient Simulator API
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
api_dir = current_dir / "api"
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(api_dir))

# Check for .env file in multiple locations
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
        break

if not env_file:
    print("⚠️  Warning: .env file not found!")
    print("Please create a .env file with your OpenAI API key in one of these locations:")
    for loc in env_locations:
        print(f"  - {loc}")
    print("File content should be:")
    print("OPENAI_API_KEY=your_api_key_here")
    print()

if __name__ == "__main__":
    print("🚀 Starting Virtual Patient Simulator API...")
    print("📁 Working directory:", current_dir)
    print("🌐 API will be available at: http://127.0.0.1:8000")
    print("📖 API documentation: http://127.0.0.1:8000/docs")
    print("🔧 Alternative docs: http://127.0.0.1:8000/redoc")
    print()
    
    try:
        uvicorn.run(
            "api.app:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info",
            reload_dirs=[str(api_dir)]
        )
    except KeyboardInterrupt:
        print("\n👋 API server stopped")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("\nTroubleshooting:")
        print("1. Check if port 8000 is already in use")
        print("2. Verify all dependencies are installed: pip install -r requirements.txt")
        print("3. Ensure .env file exists with OPENAI_API_KEY")
        sys.exit(1)
