#!/usr/bin/env python3
"""
Simple test script for the mobile app API endpoints.
Tests basic functionality without requiring a real Roku device.
"""

import requests
import json
import time
import sys

API_BASE = "http://localhost:5000"

def test_status():
    """Test the status endpoint"""
    print("Testing /api/status...")
    response = requests.get(f"{API_BASE}/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    print("✓ Status endpoint working")
    return data

def test_config():
    """Test configuration endpoints"""
    print("\nTesting /api/config...")
    
    # Test POST
    response = requests.post(
        f"{API_BASE}/api/config",
        json={"roku_ip": "192.168.1.100"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    print("✓ Config POST working")
    
    # Test GET
    response = requests.get(f"{API_BASE}/api/config")
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert data['roku_ip'] == "192.168.1.100"
    print("✓ Config GET working")
    
    return data

def test_keypress():
    """Test keypress endpoint (will fail without real Roku)"""
    print("\nTesting /api/keypress...")
    response = requests.post(
        f"{API_BASE}/api/keypress",
        json={"key": "Home"}
    )
    assert response.status_code == 200
    data = response.json()
    # We expect this to fail since there's no real Roku
    print(f"  Keypress result: {data}")
    print("✓ Keypress endpoint working (Roku not reachable as expected)")
    return data

def test_launch():
    """Test app launch endpoint"""
    print("\nTesting /api/launch...")
    response = requests.post(
        f"{API_BASE}/api/launch",
        json={"app_id": "12", "app_name": "Netflix"}
    )
    assert response.status_code == 200
    data = response.json()
    print(f"  Launch result: {data}")
    print("✓ Launch endpoint working")
    return data

def test_voice():
    """Test voice command endpoint"""
    print("\nTesting /api/voice...")
    response = requests.post(
        f"{API_BASE}/api/voice",
        json={"command": "play"}
    )
    assert response.status_code == 200
    data = response.json()
    print(f"  Voice result: {data}")
    print("✓ Voice endpoint working")
    return data

def test_invalid_requests():
    """Test error handling"""
    print("\nTesting error handling...")
    
    # Missing required field
    response = requests.post(
        f"{API_BASE}/api/keypress",
        json={}
    )
    assert response.status_code == 400
    print("✓ Handles missing parameters correctly")
    
    # Invalid IP
    response = requests.post(
        f"{API_BASE}/api/config",
        json={"roku_ip": "invalid-ip"}
    )
    assert response.status_code == 400
    print("✓ Validates IP address format")
    
    return True

def main():
    """Run all tests"""
    print("=" * 50)
    print("Mobile App API Test Suite")
    print("=" * 50)
    
    try:
        # Wait for server to be ready
        print("\nWaiting for server...")
        for i in range(10):
            try:
                requests.get(f"{API_BASE}/api/status", timeout=1)
                print("✓ Server is ready")
                break
            except:
                time.sleep(1)
        else:
            print("✗ Server not responding")
            sys.exit(1)
        
        # Run tests
        test_status()
        test_config()
        test_keypress()
        test_launch()
        test_voice()
        test_invalid_requests()
        
        print("\n" + "=" * 50)
        print("✓ All tests passed!")
        print("=" * 50)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
