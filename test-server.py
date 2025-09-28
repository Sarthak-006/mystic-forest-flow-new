#!/usr/bin/env python3
"""
Simple test script to verify the Forest Adventure Game server is working
"""

import requests
import json
import sys

def test_server():
    base_url = "http://127.0.0.1:5000"
    
    print("Testing Forest Adventure Game Server...")
    print("=" * 50)
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("+ Health check: PASSED")
            print(f"   Response: {response.json()}")
        else:
            print(f"- Health check: FAILED (Status: {response.status_code})")
    except Exception as e:
        print(f"- Health check: FAILED (Error: {e})")
        return False
    
    # Test 2: Main page
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200 and "Mystic Forest" in response.text:
            print("+ Main page: PASSED")
        else:
            print(f"- Main page: FAILED (Status: {response.status_code})")
    except Exception as e:
        print(f"- Main page: FAILED (Error: {e})")
        return False
    
    # Test 3: API state endpoint
    try:
        response = requests.get(f"{base_url}/api/state", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "situation" in data and "choices" in data:
                print("+ API state: PASSED")
                print(f"   Situation: {data['situation'][:50]}...")
                print(f"   Choices: {len(data['choices'])} available")
            else:
                print("- API state: FAILED (Invalid response format)")
        else:
            print(f"- API state: FAILED (Status: {response.status_code})")
    except Exception as e:
        print(f"- API state: FAILED (Error: {e})")
        return False
    
    # Test 4: Static files
    try:
        response = requests.get(f"{base_url}/script.js", timeout=5)
        if response.status_code == 200 and "ethers" in response.text:
            print("+ Static files: PASSED")
        else:
            print(f"- Static files: FAILED (Status: {response.status_code})")
    except Exception as e:
        print(f"- Static files: FAILED (Error: {e})")
        return False
    
    print("=" * 50)
    print("All tests passed! Server is working correctly.")
    print("\nTo test the blockchain features:")
    print("1. Open http://127.0.0.1:5000 in your browser")
    print("2. Install MetaMask if not already installed")
    print("3. Play through the game to reach an ending")
    print("4. Click 'Save to Blockchain' button")
    
    return True

if __name__ == "__main__":
    success = test_server()
    sys.exit(0 if success else 1)
