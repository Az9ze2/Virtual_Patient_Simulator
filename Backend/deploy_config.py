#!/usr/bin/env python3
"""
Deployment Configuration Setup
Sets up environment-specific configurations for Railway deployment
"""

import os
import sys
from pathlib import Path

def setup_production_config():
    """Set up production environment configurations"""
    print("🔧 Setting up production configuration...")
    
    # Get the current directory
    current_dir = Path(__file__).parent
    
    # Environment variables that Railway should have
    required_env_vars = [
        "OPENAI_API_KEY",
        "PORT",
        "RAILWAY_ENVIRONMENT"  # Railway sets this automatically
    ]
    
    print("📋 Required environment variables for Railway:")
    for var in required_env_vars:
        if var == "PORT":
            print(f"  ✓ {var}: Set automatically by Railway")
        elif var == "RAILWAY_ENVIRONMENT":
            print(f"  ✓ {var}: Set automatically by Railway")
        else:
            print(f"  ⚠️  {var}: You need to set this in Railway dashboard")
    
    print("\n🚀 Railway deployment checklist:")
    print("  1. Push code to GitHub repository")
    print("  2. Connect Railway to your GitHub repo")
    print("  3. Set OPENAI_API_KEY in Railway environment variables")
    print("  4. Deploy and test the /health endpoint")
    
    return True

if __name__ == "__main__":
    setup_production_config()
