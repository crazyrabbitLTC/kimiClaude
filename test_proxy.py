#!/usr/bin/env python3
"""
Test script to verify the Kimi proxy is working correctly
"""
import requests
import json
import sys
import time

def test_proxy():
    proxy_url = "http://localhost:8090"
    
    print("Testing Kimi proxy...")
    
    # Test 1: Health check (GET request)
    print("\n1. Testing health check (GET /health):")
    try:
        response = requests.get(f"{proxy_url}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.text}")
            print("   ✓ Health check passed")
        else:
            print(f"   ✗ Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ✗ Health check failed: {e}")
        return False
    
    # Test 2: OPTIONS request (CORS preflight)
    print("\n2. Testing CORS preflight (OPTIONS):")
    try:
        response = requests.options(f"{proxy_url}/v1/messages", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✓ OPTIONS request handled")
        else:
            print(f"   ✗ OPTIONS request failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ OPTIONS request failed: {e}")
    
    # Test 3: HEAD request
    print("\n3. Testing HEAD request:")
    try:
        response = requests.head(f"{proxy_url}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✓ HEAD request handled")
        else:
            print(f"   ✗ HEAD request failed: {response.status_code}")
    except Exception as e:
        print(f"   ✗ HEAD request failed: {e}")
    
    # Test 4: POST to /v1/messages with query params (the original issue)
    print("\n4. Testing POST /v1/messages?beta=true (simulating Claude Code):")
    try:
        test_message = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 100,
            "messages": [
                {"role": "user", "content": "Hello, this is a test message"}
            ]
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-key"
        }
        
        # This should NOT return 404 anymore
        response = requests.post(
            f"{proxy_url}/v1/messages?beta=true", 
            json=test_message, 
            headers=headers,
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 404:
            print("   ✗ Still getting 404 - the original issue persists!")
            print(f"   Response: {response.text}")
            return False
        elif response.status_code in [200, 401, 429, 500]:
            # 401 = auth error (expected with test key)
            # 429 = rate limit (possible)
            # 500 = server error (possible with invalid key)
            print("   ✓ No 404 error - proxy is routing correctly!")
            print(f"   Response indicates proxy processed the request (status {response.status_code})")
            return True
        else:
            print(f"   ? Unexpected status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ✗ POST request failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Kimi Proxy Test Suite")
    print("=" * 40)
    
    # Wait a moment for proxy to be ready if just started
    time.sleep(1)
    
    if test_proxy():
        print("\n✅ Proxy tests completed successfully!")
        print("The 404 issue should be resolved.")
        sys.exit(0)
    else:
        print("\n❌ Proxy tests failed!")
        print("The 404 issue may still exist.")
        sys.exit(1)