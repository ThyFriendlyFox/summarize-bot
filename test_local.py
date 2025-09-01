#!/usr/bin/env python3
"""
Local development test script for Discord Summarize Bot
"""

import os
import requests
import json
import time
from datetime import datetime

def test_health_endpoint(base_url="http://localhost:8080"):
    """Test the health endpoint."""
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_discord_ping(base_url="http://localhost:8080"):
    """Test Discord ping interaction."""
    try:
        payload = {"type": 1}
        headers = {
            "Content-Type": "application/json",
            "x-signature-ed25519": "test_signature",
            "x-signature-timestamp": str(int(time.time()))
        }
        
        response = requests.post(
            f"{base_url}/discord/interactions",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("type") == 1:
                print("✅ Discord ping working")
                return True
            else:
                print(f"❌ Unexpected ping response: {data}")
                return False
        else:
            print(f"❌ Discord ping failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Discord ping error: {e}")
        return False

def check_environment():
    """Check if required environment variables are set."""
    required_vars = [
        "DISCORD_PUBLIC_KEY",
        "DISCORD_APPLICATION_ID", 
        "DISCORD_BOT_TOKEN",
        "GOOGLE_CLOUD_PROJECT_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set them before running the bot:")
        for var in missing_vars:
            print(f"  export {var}='your_value'")
        return False
    else:
        print("✅ All environment variables are set")
        return True

def main():
    """Run all tests."""
    print("🧪 Discord Summarize Bot - Local Development Tests")
    print("=" * 50)
    
    # Check environment
    env_ok = check_environment()
    
    # Test endpoints (only if server is running)
    print("\n📡 Testing endpoints...")
    health_ok = test_health_endpoint()
    ping_ok = test_discord_ping()
    
    print("\n📋 Summary:")
    print(f"Environment: {'✅' if env_ok else '❌'}")
    print(f"Health endpoint: {'✅' if health_ok else '❌'}")
    print(f"Discord ping: {'✅' if ping_ok else '❌'}")
    
    if not health_ok:
        print("\n💡 To test endpoints, start the bot first:")
        print("  python main.py")
        print("\n💡 For webhook testing, use ngrok:")
        print("  ngrok http 8080")

if __name__ == "__main__":
    main()
