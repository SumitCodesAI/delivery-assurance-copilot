"""Test webhook endpoint with sample Jira event payload."""

import requests
import json
from datetime import datetime

# Webhook endpoint
WEBHOOK_URL = "http://localhost:8000/api/v1/jira/webhooks/event"

# Sample Jira issue updated webhook payload
# This simulates Jira sending an event when an issue status changes
sample_payload = {
    "webhookEvent": "jira:issue_updated",
    "timestamp": datetime.utcnow().isoformat(),
    "issue": {
        "id": "10000",
        "key": "KAN-5",
        "fields": {
            "summary": "User Authentication Module",
            "status": {
                "name": "In Progress",
                "id": "3"
            },
            "priority": {
                "name": "High",
                "id": "2"
            },
            "assignee": {
                "displayName": "John Developer",
                "emailAddress": "john@example.com"
            },
            "description": "Implement user authentication with OAuth2"
        }
    },
    "changelog": {
        "items": [
            {
                "field": "status",
                "fromString": "To Do",
                "toString": "In Progress"
            }
        ]
    }
}

def test_webhook():
    """Test the webhook endpoint."""
    print("Testing Jira webhook endpoint...")
    print(f"URL: {WEBHOOK_URL}")
    print(f"Payload: {json.dumps(sample_payload, indent=2)}\n")
    
    try:
        response = requests.post(WEBHOOK_URL, json=sample_payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("\n✅ Webhook endpoint is working!")
            return True
        else:
            print("\n❌ Webhook returned unexpected status code")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_webhook()
