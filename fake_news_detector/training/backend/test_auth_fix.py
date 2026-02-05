#!/usr/bin/env python3
"""
Test script to verify authentication fixes
"""

import requests
import json

def test_authentication():
    """Test the authentication endpoints"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Authentication Fixes")
    print("=" * 40)
    
    # Test 1: Register with missing fields
    print("1. Testing register with missing fields...")
    try:
        response = requests.post(f"{base_url}/register", data={})
        if response.status_code == 200 and "required" in response.text.lower():
            print("   ✅ Register handles missing fields correctly")
        else:
            print("   ❌ Register doesn't handle missing fields")
    except Exception as e:
        print(f"   ⚠️  Could not test register: {e}")
    
    # Test 2: Login with missing fields
    print("2. Testing login with missing fields...")
    try:
        response = requests.post(f"{base_url}/login", data={})
        if response.status_code == 200 and ("username" in response.text.lower() or "password" in response.text.lower()):
            print("   ✅ Login handles missing fields correctly")
        else:
            print("   ❌ Login doesn't handle missing fields")
    except Exception as e:
        print(f"   ⚠️  Could not test login: {e}")
    
    # Test 3: Home page redirect
    print("3. Testing home page redirect...")
    try:
        response = requests.get(f"{base_url}/", allow_redirects=False)
        if response.status_code in [302, 401]:
            print("   ✅ Home page redirects unauthenticated users")
        else:
            print("   ❌ Home page doesn't redirect properly")
    except Exception as e:
        print(f"   ⚠️  Could not test home redirect: {e}")
    
    # Test 4: API health check
    print("4. Testing API health...")
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API health check passed: {data.get('status', 'unknown')}")
        else:
            print("   ❌ API health check failed")
    except Exception as e:
        print(f"   ⚠️  Could not test API health: {e}")
    
    print("\n🎯 Authentication fix test completed!")
    print("If all tests pass, the BadRequestKeyError should be fixed.")

if __name__ == "__main__":
    test_authentication()