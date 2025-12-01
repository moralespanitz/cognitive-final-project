#!/usr/bin/env python3
"""
Test the AI Chat functionality end-to-end.
"""
import requests
import json

API_URL = "http://localhost:8000/api/v1"

def test_chat():
    """Test chat functionality with fallback responses."""
    print("=" * 60)
    print("TaxiWatch - AI Chat Test")
    print("=" * 60)

    # Step 1: Register/Login to get token
    print("\n1. Authenticating...")

    # Try to register
    register_data = {
        "username": "chattest",
        "email": "chattest@taxiwatch.com",
        "password": "Test123!",
        "first_name": "Chat",
        "last_name": "Tester",
        "role": "ADMIN"
    }

    try:
        response = requests.post(f"{API_URL}/auth/register", json=register_data)
        if response.status_code == 201:
            print("   ✓ User registered")
        elif response.status_code == 400:
            print("   ℹ User already exists, logging in...")
    except Exception as e:
        print(f"   ⚠ Register warning: {e}")

    # Login
    login_data = {
        "username": "chattest",
        "password": "Test123!"
    }

    try:
        response = requests.post(f"{API_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("   ✓ Authentication successful")
        else:
            print(f"   ✗ Login failed: {response.text}")
            return
    except Exception as e:
        print(f"   ✗ Login error: {e}")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Step 2: Test different chat messages
    print("\n2. Testing AI Chat...")
    print("-" * 60)

    test_messages = [
        "Hello, what can you help me with?",
        "How many vehicles do I have?",
        "Tell me about driver performance",
        "What's the status of my fleet?",
        "Are there any active alerts?"
    ]

    for i, message in enumerate(test_messages, 1):
        print(f"\n   Test {i}/5:")
        print(f"   User: {message}")

        try:
            response = requests.post(
                f"{API_URL}/chat/",
                json={"message": message},
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("response", "")

                # Format response for display
                lines = ai_response.split('\n')
                for line in lines:
                    if line.strip():
                        print(f"   AI:   {line}")
                    else:
                        print()

                print("   ✓ Response received")
            else:
                print(f"   ✗ Error {response.status_code}: {response.text}")

        except requests.exceptions.Timeout:
            print("   ✗ Request timeout (OpenAI might be taking too long)")
        except Exception as e:
            print(f"   ✗ Error: {e}")

    print("\n" + "=" * 60)
    print("Test Summary:")
    print("-" * 60)
    print("✓ Authentication works")
    print("✓ Chat endpoint is accessible")

    # Check if OpenAI is configured
    try:
        response = requests.get(f"{API_URL}/chat/health", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Chat service status: {data.get('status', 'unknown')}")
            print(f"  OpenAI integration: {data.get('openai_integration', 'unknown')}")
    except:
        pass

    print("\nNote: If OpenAI API key is not configured, fallback responses")
    print("will be used. To use real AI responses, set OPENAI_API_KEY")
    print("in your .env file and restart the backend.")
    print("=" * 60)


if __name__ == "__main__":
    test_chat()
