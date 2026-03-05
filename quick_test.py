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
print(f"Login Status: {response.status_code}")
if response.status_code == 200:
    token_data = response.json()
    token = token_data["access_token"]
    user = token_data["user"]
    print(f"Logged in as: {user['name']} ({user['role']})")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test notifications
    print("\n=== Testing Notifications ===")
    notif_response = requests.get(f"{BACKEND_URL}/api/notifications", headers=headers)
    print(f"Notifications Status: {notif_response.status_code}")
    if notif_response.status_code == 200:
        notif_data = notif_response.json()
        print(f"Notifications: {json.dumps(notif_data, indent=2)}")
    else:
        print(f"Notifications Error: {notif_response.text}")
    
    # Test mark notifications as read
    print("\n=== Testing Mark Notifications Read ===")
    mark_response = requests.post(f"{BACKEND_URL}/api/notifications/mark-read", json={}, headers=headers)
    print(f"Mark Read Status: {mark_response.status_code}")
    print(f"Mark Read Response: {mark_response.text}")
    
    # Test project chat
    test_project_id = "9e670e52-350a-4e40-8813-808bb1c14e6b"
    print(f"\n=== Testing Project Chat ({test_project_id}) ===")
    chat_response = requests.get(f"{BACKEND_URL}/api/projects/{test_project_id}/chat", headers=headers)
    print(f"Chat Status: {chat_response.status_code}")
    if chat_response.status_code == 200:
        chat_data = chat_response.json()
        print(f"Chat Messages: {len(chat_data.get('messages', []))} messages")
    else:
        print(f"Chat Error: {chat_response.text}")
        
    # Test send chat message with form data
    print("\n=== Testing Send Chat Message ===")
    form_data = {"content": "Test message from quick test"}
    send_response = requests.post(f"{BACKEND_URL}/api/projects/{test_project_id}/chat", data=form_data, headers=headers)
    print(f"Send Message Status: {send_response.status_code}")
    print(f"Send Message Response: {send_response.text}")
    
    # Test analytics (admin only)
    if user.get('role') == 'admin':
        print("\n=== Testing Analytics (Admin) ===")
        analytics_response = requests.get(f"{BACKEND_URL}/api/admin/analytics/revenue", headers=headers)
        print(f"Analytics Status: {analytics_response.status_code}")
        if analytics_response.status_code == 200:
            analytics_data = analytics_response.json()
            print(f"Analytics Keys: {list(analytics_data.keys())}")
        else:
            print(f"Analytics Error: {analytics_response.text}")
    else:
        print(f"\n=== User is not admin, skipping analytics test ===")
        
else:
    print(f"Login failed: {response.text}")