#!/usr/bin/env python3
"""
Test script to verify the backend streaming API is working correctly.
This will help isolate if the issue is with the backend or frontend.
"""

import requests
import sys
from datetime import datetime

# Configuration
SERVER_BASE_URL = "http://100.67.83.60:8000"
API_BASE_URL = f"{SERVER_BASE_URL}/api"

def test_health_endpoint():
    """Test if the backend is running and accessible"""
    try:
        print(f"🔍 Testing health endpoint: {API_BASE_URL}/health/")
        response = requests.get(f"{API_BASE_URL}/health/", timeout=10)
        print(f"✅ Health check - Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_auth_login():
    """Test login to get authentication token"""
    try:
        print(f"\n🔐 Testing authentication...")
        # You'll need to replace these with actual credentials
        login_data = {
            "username": "test@example.com",  # Replace with actual username
            "password": "testpassword"       # Replace with actual password
        }
        
        response = requests.post(f"{API_BASE_URL}/auth/login", json=login_data, timeout=10)
        print(f"   Login - Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Login successful")
            return token_data.get("access_token")
        else:
            print(f"❌ Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_search_endpoint(token):
    """Test searching for songs"""
    try:
        print(f"\n🔍 Testing search endpoint...")
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        
        search_data = {"query": "test", "limit": 5}
        response = requests.post(f"{API_BASE_URL}/search/local", 
                               json=search_data, 
                               headers=headers, 
                               timeout=10)
        
        print(f"   Search - Status: {response.status_code}")
        
        if response.status_code == 200:
            songs = response.json()
            print(f"✅ Found {len(songs)} songs")
            return songs[:1] if songs else []  # Return first song for testing
        else:
            print(f"❌ Search failed: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Search error: {e}")
        return []

def test_streaming_endpoint(token, song):
    """Test streaming a specific song"""
    if not song or not song.get('spotify_id'):
        print("❌ No valid song to test streaming")
        return False
        
    try:
        print(f"\n🎵 Testing streaming endpoint...")
        print(f"   Song: {song.get('title', 'Unknown')} by {song.get('artist', 'Unknown')}")
        print(f"   Spotify ID: {song['spotify_id']}")
        
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        stream_url = f"{API_BASE_URL}/stream/play/{song['spotify_id']}"
        
        print(f"   Streaming URL: {stream_url}")
        
        # Make a HEAD request first to check if the endpoint responds
        response = requests.head(stream_url, headers=headers, timeout=10)
        print(f"   Stream HEAD - Status: {response.status_code}")
        
        if response.status_code == 200:
            # Try to get a small portion of the file
            response = requests.get(stream_url, headers=headers, timeout=10, stream=True)
            print(f"   Stream GET - Status: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', 'unknown')
                content_length = response.headers.get('content-length', 'unknown')
                
                print(f"✅ Streaming successful!")
                print(f"   Content-Type: {content_type}")
                print(f"   Content-Length: {content_length}")
                
                # Read first 1KB to verify it's actual audio data
                chunk = next(response.iter_content(1024))
                print(f"   First chunk size: {len(chunk)} bytes")
                return True
            else:
                print(f"❌ Stream GET failed: {response.text}")
                return False
        else:
            print(f"❌ Stream HEAD failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Streaming error: {e}")
        return False

def test_direct_file_access(song):
    """Test direct file access via static file serving"""
    if not song or not song.get('file_path'):
        print("❌ No file path available for direct access test")
        return False
        
    try:
        print(f"\n📁 Testing direct file access...")
        
        # Extract filename from file path
        file_path = song['file_path']
        filename = file_path.split('/')[-1]
        direct_url = f"{SERVER_BASE_URL}/music/{filename}"
        
        print(f"   Direct URL: {direct_url}")
        
        response = requests.head(direct_url, timeout=10)
        print(f"   Direct access - Status: {response.status_code}")
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', 'unknown')
            content_length = response.headers.get('content-length', 'unknown')
            
            print(f"✅ Direct access successful!")
            print(f"   Content-Type: {content_type}")
            print(f"   Content-Length: {content_length}")
            return True
        else:
            print(f"❌ Direct access failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Direct access error: {e}")
        return False

def main():
    print("🎵 MREE Backend API Test")
    print("=" * 50)
    print(f"Testing server: {SERVER_BASE_URL}")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Test 1: Health check
    if not test_health_endpoint():
        print("\n❌ Backend is not accessible. Please check if it's running.")
        sys.exit(1)
    
    # Test 2: Authentication
    token = test_auth_login()
    if not token:
        print("\n⚠️  Authentication failed. Testing without token...")
    
    # Test 3: Search for songs
    songs = test_search_endpoint(token)
    if not songs:
        print("\n❌ No songs found to test streaming")
        sys.exit(1)
    
    song = songs[0]
    
    # Test 4: Streaming endpoint
    streaming_success = test_streaming_endpoint(token, song)
    
    # Test 5: Direct file access
    direct_success = test_direct_file_access(song)
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 50)
    print(f"Health Check: ✅")
    print(f"Authentication: {'✅' if token else '❌'}")
    print(f"Search: {'✅' if songs else '❌'}")
    print(f"Streaming API: {'✅' if streaming_success else '❌'}")
    print(f"Direct File Access: {'✅' if direct_success else '❌'}")
    
    if streaming_success or direct_success:
        print(f"\n✅ Backend streaming is working! The issue is likely in the Flutter app.")
    else:
        print(f"\n❌ Backend streaming is not working. Check backend configuration.")

if __name__ == "__main__":
    main()
