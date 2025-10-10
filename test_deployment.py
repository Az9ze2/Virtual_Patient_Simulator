#!/usr/bin/env python3
"""
Post-Deployment Testing Script
Tests deployed backend and frontend endpoints
"""

import requests
import json
import time
from pathlib import Path

class DeploymentTester:
    def __init__(self, backend_url, frontend_url):
        self.backend_url = backend_url.rstrip('/')
        self.frontend_url = frontend_url.rstrip('/')
        
    def test_backend_health(self):
        """Test backend health endpoint"""
        print("🏥 Testing backend health...")
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                print(f"   ✅ Health check passed: {response.json()}")
                return True
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
            return False
    
    def test_backend_docs(self):
        """Test backend API documentation"""
        print("📚 Testing backend API docs...")
        try:
            response = requests.get(f"{self.backend_url}/docs", timeout=10)
            if response.status_code == 200:
                print("   ✅ API documentation accessible")
                return True
            else:
                print(f"   ❌ API docs failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ API docs error: {e}")
            return False
    
    def test_cases_endpoint(self):
        """Test cases listing endpoint"""
        print("📋 Testing cases endpoint...")
        try:
            response = requests.get(f"{self.backend_url}/api/cases/list", timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data', {}).get('cases'):
                    cases_count = len(data['data']['cases'])
                    print(f"   ✅ Cases endpoint working: {cases_count} cases found")
                    return True
                else:
                    print("   ❌ Cases endpoint returned invalid data")
                    return False
            else:
                print(f"   ❌ Cases endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Cases endpoint error: {e}")
            return False
    
    def test_frontend_access(self):
        """Test frontend accessibility"""
        print("🌐 Testing frontend access...")
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                if "Virtual Patient Simulator" in response.text or "React" in response.text:
                    print("   ✅ Frontend accessible and contains expected content")
                    return True
                else:
                    print("   ⚠️  Frontend accessible but content might be incorrect")
                    return False
            else:
                print(f"   ❌ Frontend failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Frontend error: {e}")
            return False
    
    def test_cors(self):
        """Test CORS configuration"""
        print("🔗 Testing CORS configuration...")
        try:
            headers = {
                'Origin': self.frontend_url,
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            response = requests.options(f"{self.backend_url}/api/cases/list", 
                                      headers=headers, timeout=10)
            
            cors_headers = response.headers
            if 'Access-Control-Allow-Origin' in cors_headers:
                allowed_origin = cors_headers['Access-Control-Allow-Origin']
                if allowed_origin == '*' or self.frontend_url in allowed_origin:
                    print("   ✅ CORS properly configured")
                    return True
                else:
                    print(f"   ❌ CORS misconfigured. Allowed: {allowed_origin}")
                    return False
            else:
                print("   ❌ CORS headers missing")
                return False
        except Exception as e:
            print(f"   ❌ CORS test error: {e}")
            return False
    
    def test_full_integration(self):
        """Test a complete integration flow"""
        print("🔄 Testing full integration...")
        
        try:
            # Test session creation
            user_data = {
                "user_info": {
                    "name": "Test User",
                    "student_id": "TEST123"
                },
                "case_filename": "",  # We'll get this from cases list
                "config": {
                    "model_choice": "gpt-4.1-mini",
                    "memory_mode": "summarize",
                    "temperature": 0.7,
                    "exam_mode": False
                }
            }
            
            # First, get available cases
            cases_response = requests.get(f"{self.backend_url}/api/cases/list", timeout=15)
            if cases_response.status_code != 200:
                print("   ❌ Could not fetch cases for integration test")
                return False
            
            cases_data = cases_response.json()
            if not cases_data.get('success') or not cases_data.get('data', {}).get('cases'):
                print("   ❌ No cases available for integration test")
                return False
            
            # Use the first available case
            first_case = cases_data['data']['cases'][0]
            user_data['case_filename'] = first_case['filename']
            
            print(f"   📝 Testing with case: {first_case['filename']}")
            
            # Create session
            session_response = requests.post(
                f"{self.backend_url}/api/sessions/start",
                json=user_data,
                timeout=20
            )
            
            if session_response.status_code == 200:
                session_data = session_response.json()
                if session_data.get('success'):
                    session_id = session_data['data']['session_id']
                    print(f"   ✅ Session created: {session_id[:8]}...")
                    
                    # Clean up: end the session
                    requests.post(f"{self.backend_url}/api/sessions/{session_id}/end", timeout=10)
                    return True
                else:
                    print(f"   ❌ Session creation failed: {session_data.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"   ❌ Session creation failed: {session_response.status_code}")
                if session_response.content:
                    try:
                        error_data = session_response.json()
                        print(f"       Error: {error_data.get('detail', 'Unknown error')}")
                    except:
                        print(f"       Raw error: {session_response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Integration test error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all deployment tests"""
        print("🧪 Running deployment tests...")
        print("=" * 50)
        
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Backend Docs", self.test_backend_docs), 
            ("Cases Endpoint", self.test_cases_endpoint),
            ("Frontend Access", self.test_frontend_access),
            ("CORS Configuration", self.test_cors),
            ("Full Integration", self.test_full_integration)
        ]
        
        results = {}
        for test_name, test_func in tests:
            print()
            results[test_name] = test_func()
            time.sleep(1)  # Brief pause between tests
        
        # Summary
        print("\n" + "=" * 50)
        print("🎯 Test Results Summary:")
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status} {test_name}")
            if result:
                passed += 1
        
        print(f"\n📊 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("\n🎉 All tests passed! Your deployment is working correctly.")
            return True
        else:
            print(f"\n⚠️  {total-passed} test(s) failed. Check the issues above.")
            return False

def main():
    print("🚀 Virtual Patient Simulator - Deployment Tester")
    print("=" * 50)
    
    # Get URLs from user or use defaults
    backend_url = input("Backend URL (Railway): ").strip()
    if not backend_url:
        backend_url = "https://virtual-patient-simulator.railway.app"
    
    frontend_url = input("Frontend URL (Vercel): ").strip()
    if not frontend_url:
        frontend_url = "https://virtual-patient-simulator.vercel.app"
    
    print(f"\n🎯 Testing deployment:")
    print(f"   🚂 Backend: {backend_url}")
    print(f"   🌐 Frontend: {frontend_url}")
    
    tester = DeploymentTester(backend_url, frontend_url)
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Deployment is ready for testing with users!")
    else:
        print("\n❌ Please fix the issues before proceeding with user testing.")

if __name__ == "__main__":
    main()
