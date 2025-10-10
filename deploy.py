#!/usr/bin/env python3
"""
Deployment Automation Script
Helps set up and validate deployment configuration
"""

import os
import sys
import json
import subprocess
from pathlib import Path

class DeploymentHelper:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.backend_dir = self.root_dir / "Backend"
        self.frontend_dir = self.root_dir / "Frontend"
        
    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        print("🔍 Checking deployment prerequisites...")
        
        checks = {
            "Git repository": self._check_git(),
            "Backend files": self._check_backend_files(),
            "Frontend files": self._check_frontend_files(),
            "Environment files": self._check_env_files(),
        }
        
        all_good = True
        for check, status in checks.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {check}")
            if not status:
                all_good = False
        
        return all_good
    
    def _check_git(self):
        """Check if git is initialized"""
        return (self.root_dir / ".git").exists()
    
    def _check_backend_files(self):
        """Check if backend deployment files exist"""
        required_files = [
            "requirements.txt",
            "Procfile", 
            "railway.toml",
            "api/app.py"
        ]
        return all((self.backend_dir / file).exists() for file in required_files)
    
    def _check_frontend_files(self):
        """Check if frontend deployment files exist"""
        required_files = [
            "package.json",
            "vercel.json",
            ".env.example",
            "src/services/apiService.js"
        ]
        return all((self.frontend_dir / file).exists() for file in required_files)
    
    def _check_env_files(self):
        """Check if environment configuration is ready"""
        return (
            (self.frontend_dir / ".env.example").exists() and
            (self.backend_dir / "railway.toml").exists()
        )
    
    def generate_deployment_urls(self, project_name="virtual-patient-simulator"):
        """Generate suggested deployment URLs"""
        print(f"\n🌐 Suggested deployment URLs for '{project_name}':")
        
        railway_suggestions = [
            f"https://{project_name}.railway.app",
            f"https://{project_name}-backend.railway.app", 
            f"https://vps-backend.railway.app"
        ]
        
        vercel_suggestions = [
            f"https://{project_name}.vercel.app",
            f"https://vps-frontend.vercel.app",
            f"https://virtual-patient-sim.vercel.app"
        ]
        
        print("\n   🚂 Railway (Backend):")
        for url in railway_suggestions:
            print(f"      • {url}")
        
        print("\n   🌐 Vercel (Frontend):")  
        for url in vercel_suggestions:
            print(f"      • {url}")
        
        return railway_suggestions[0], vercel_suggestions[0]
    
    def create_env_template(self, railway_url, vercel_url):
        """Create environment variable templates"""
        print(f"\n📝 Environment variable templates:")
        
        print(f"\n   🚂 Railway Environment Variables:")
        print(f"      OPENAI_API_KEY=sk-your-openai-api-key-here")
        print(f"      ENVIRONMENT=production")
        print(f"      FRONTEND_URL={vercel_url}")
        
        print(f"\n   🌐 Vercel Environment Variables:")
        print(f"      REACT_APP_API_URL={railway_url}")
        print(f"      REACT_APP_ENVIRONMENT=production")
        
        # Create .env.production template
        env_production = self.frontend_dir / ".env.production"
        with open(env_production, "w") as f:
            f.write(f"# Production Environment Variables\n")
            f.write(f"# DO NOT COMMIT THIS FILE\n")
            f.write(f"REACT_APP_API_URL={railway_url}\n")
            f.write(f"REACT_APP_ENVIRONMENT=production\n")
        
        print(f"\n   ✅ Created {env_production}")
    
    def validate_configuration(self):
        """Validate deployment configuration"""
        print("\n🔧 Validating deployment configuration...")
        
        # Check package.json
        package_json = self.frontend_dir / "package.json"
        if package_json.exists():
            with open(package_json) as f:
                data = json.load(f)
                if "proxy" in data:
                    print("   ⚠️  Warning: Found 'proxy' in package.json - this won't work in production")
                else:
                    print("   ✅ package.json looks good")
        
        # Check API service configuration
        api_service = self.frontend_dir / "src" / "services" / "apiService.js"
        if api_service.exists():
            try:
                with open(api_service, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "REACT_APP_API_URL" in content:
                        print("   ✅ apiService.js is configured for environment variables")
                    else:
                        print("   ❌ apiService.js needs environment variable support")
            except UnicodeDecodeError:
                print("   ⚠️  Could not read apiService.js (encoding issue)")
    
    def show_deployment_steps(self):
        """Show deployment steps"""
        print(f"\n🚀 Deployment Steps:")
        print(f"\n1. 📱 Push to GitHub:")
        print(f"   git add .")
        print(f"   git commit -m 'Ready for deployment'")
        print(f"   git push origin main")
        
        print(f"\n2. 🚂 Deploy Backend (Railway):")
        print(f"   • Go to https://railway.app")
        print(f"   • Deploy from GitHub repo")
        print(f"   • Set root directory to 'Backend'")
        print(f"   • Add environment variables")
        
        print(f"\n3. 🌐 Deploy Frontend (Vercel):")
        print(f"   • Go to https://vercel.com")
        print(f"   • Import from GitHub")
        print(f"   • Set root directory to 'Frontend'")  
        print(f"   • Add environment variables")
        
        print(f"\n4. 🔗 Connect Frontend & Backend:")
        print(f"   • Update CORS in Railway")
        print(f"   • Test full integration")
        
        print(f"\n📖 Full guide: ./DEPLOYMENT_GUIDE.md")

def main():
    helper = DeploymentHelper()
    
    print("🚀 Virtual Patient Simulator - Deployment Helper")
    print("=" * 50)
    
    # Check prerequisites
    if not helper.check_prerequisites():
        print("\n❌ Some prerequisites are missing. Please check the issues above.")
        return
    
    # Generate URLs
    railway_url, vercel_url = helper.generate_deployment_urls()
    
    # Create environment templates  
    helper.create_env_template(railway_url, vercel_url)
    
    # Validate configuration
    helper.validate_configuration()
    
    # Show deployment steps
    helper.show_deployment_steps()
    
    print("\n✅ Deployment configuration ready!")
    print("📖 See DEPLOYMENT_GUIDE.md for detailed instructions")

if __name__ == "__main__":
    main()
