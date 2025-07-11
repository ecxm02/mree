import requests
import json

# Test basic connectivity to your backend
SERVER_URL = "http://100.67.83.60:8000"

print("Testing MREE Backend API...")
print(f"Server URL: {SERVER_URL}")
print("-" * 50)

# Test 1: Basic health check
try:
    response = requests.get(f"{SERVER_URL}/health", timeout=5)
    print(f"✅ Basic Health Check: {response.status_code}")
    if response.status_code == 200:
        print(f"   Response: {response.json()}")
except Exception as e:
    print(f"❌ Basic Health Check Failed: {e}")

# Test 2: API health check  
try:
    response = requests.get(f"{SERVER_URL}/api/health/", timeout=5)
    print(f"✅ API Health Check: {response.status_code}")
    if response.status_code == 200:
        print(f"   Response: {response.json()}")
except Exception as e:
    print(f"❌ API Health Check Failed: {e}")

# Test 3: Check if static files are accessible
try:
    response = requests.head(f"{SERVER_URL}/music/", timeout=5)
    print(f"✅ Static Files Check: {response.status_code}")
    print(f"   (This may be 404 if no music files, but should not be connection error)")
except Exception as e:
    print(f"❌ Static Files Check Failed: {e}")

print("\nIf all tests show connection errors, the backend may not be running on 100.67.83.60:8000")
print("If tests pass, the issue is likely in the Flutter app configuration or authentication.")
