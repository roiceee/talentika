#!/usr/bin/env python
"""Quick test script for authentication endpoints"""
import requests
import json

BASE_URL = "http://localhost:8000/api"


def test_register():
    """Test user registration"""
    print("Testing user registration...")
    url = f"{BASE_URL}/register/"
    data = {
        "email": "testuser@example.com",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "password": "TestPass123!",
        "password_confirm": "TestPass123!",
    }

    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    return response.status_code in [200, 201]


def test_login():
    """Test login"""
    print("Testing login...")
    url = f"{BASE_URL}/auth/login/"
    data = {"email": "testuser@example.com", "password": "TestPass123!"}

    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}\n")

    if response.status_code == 200:
        return result.get("access"), result.get("refresh")
    return None, None


def test_refresh(refresh_token):
    """Test token refresh"""
    print("Testing token refresh...")
    url = f"{BASE_URL}/auth/refresh/"
    data = {"refresh": refresh_token}

    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")


def test_protected_endpoint(access_token):
    """Test accessing protected endpoint"""
    print("Testing protected endpoint (list organizations)...")
    url = f"{BASE_URL}/organizations/"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Talentika Authentication")
    print("=" * 60 + "\n")

    # Test registration (might fail if user exists)
    test_register()

    # Test login
    access_token, refresh_token = test_login()

    if access_token:
        # Test refresh
        test_refresh(refresh_token)

        # Test protected endpoint
        test_protected_endpoint(access_token)

        print("✅ All authentication tests passed!")
    else:
        print("❌ Login failed")
