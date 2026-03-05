#!/usr/bin/env python3

import requests
import json

BACKEND_URL = "https://agency-andre-dev.preview.emergentagent.com"

# Test user login
login_data = {
    "email": "teste.stripe@example.com",
    "password": "teste123"
}

response = requests.post(f"{BACKEND_URL}/api/auth/login", json=login_data)
if response.status_code == 200:
    token_data = response.json()
    token = token_data["access_token"]
    user = token_data["user"]
    print(f"Logged in as: {user['name']} ({user['role']})")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test mark notifications as read without body (query params)
    print("=== Testing Mark Notifications Read (no params) ===")
    mark_response = requests.post(f"{BACKEND_URL}/api/notifications/mark-read", headers=headers)
    print(f"Status: {mark_response.status_code}")
    print(f"Response: {mark_response.text}")
    
    # Test mark notifications as read with empty list query param
    print("=== Testing Mark Notifications Read (empty list) ===")
    mark_response2 = requests.post(f"{BACKEND_URL}/api/notifications/mark-read?notification_ids=", headers=headers)
    print(f"Status: {mark_response2.status_code}")
    print(f"Response: {mark_response2.text}")
    
else:
    print(f"Login failed: {response.text}")