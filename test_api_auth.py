#!/usr/bin/env python3
"""
Test script to verify API key authentication is working correctly.
Run this script to test your API endpoints with and without authentication.
"""

import requests
import os
import sys

def test_api_authentication():
    """Test API authentication with various scenarios"""
    
    # Get API key from environment
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("❌ API_KEY environment variable not set")
        print("   Run: python generate_api_key.py")
        return False
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing API Authentication...")
    print(f"📡 API URL: {base_url}")
    print(f"🔑 API Key: {api_key[:10]}...{api_key[-10:]}")
    print()
    
    # Test 1: Public endpoints (should work without API key)
    print("1️⃣ Testing public endpoints (no API key required)...")
    
    try:
        # Test root endpoint
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("   ✅ GET / - Success")
        else:
            print(f"   ❌ GET / - Failed: {response.status_code}")
            return False
        
        # Test health endpoint
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("   ✅ GET /health - Success")
        else:
            print(f"   ❌ GET /health - Failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed - Is the API server running?")
        return False
    
    print()
    
    # Test 2: Protected endpoints without API key (should fail)
    print("2️⃣ Testing protected endpoints without API key (should fail)...")
    
    try:
        response = requests.get(f"{base_url}/users/")
        if response.status_code == 401:
            print("   ✅ GET /users/ - Correctly rejected (401)")
        else:
            print(f"   ❌ GET /users/ - Unexpected response: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed")
        return False
    
    print()
    
    # Test 3: Protected endpoints with API key (should work)
    print("3️⃣ Testing protected endpoints with API key...")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(f"{base_url}/users/", headers=headers)
        if response.status_code == 200:
            print("   ✅ GET /users/ - Success with API key")
        else:
            print(f"   ❌ GET /users/ - Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed")
        return False
    
    # Test brands endpoint
    try:
        response = requests.get(f"{base_url}/brands/", headers=headers)
        if response.status_code == 200:
            print("   ✅ GET /brands/ - Success with API key")
        else:
            print(f"   ❌ GET /brands/ - Failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed")
        return False
    
    # Test products endpoint
    try:
        response = requests.get(f"{base_url}/products/", headers=headers)
        if response.status_code == 200:
            print("   ✅ GET /products/ - Success with API key")
        else:
            print(f"   ❌ GET /products/ - Failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed")
        return False
    
    print()
    
    # Test 4: Invalid API key (should fail)
    print("4️⃣ Testing with invalid API key (should fail)...")
    
    invalid_headers = {"Authorization": "Bearer invalid-api-key"}
    
    try:
        response = requests.get(f"{base_url}/users/", headers=invalid_headers)
        if response.status_code == 401:
            print("   ✅ GET /users/ - Correctly rejected invalid API key (401)")
        else:
            print(f"   ❌ GET /users/ - Unexpected response: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed")
        return False
    
    print()
    print("🎉 All authentication tests passed!")
    print("🔒 Your API is properly secured with API key authentication")
    return True

def main():
    """Main function"""
    print("🔐 API Authentication Test Suite")
    print("=" * 40)
    
    success = test_api_authentication()
    
    if success:
        print("\n✅ Authentication setup is working correctly!")
        print("\n📝 Next steps:")
        print("1. Your API is ready for production use")
        print("2. Make sure to keep your API key secure")
        print("3. Update your NextJS frontend with the API key")
        sys.exit(0)
    else:
        print("\n❌ Authentication setup has issues")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure the API server is running")
        print("2. Check that API_KEY environment variable is set")
        print("3. Verify the API key is correct")
        sys.exit(1)

if __name__ == "__main__":
    main() 