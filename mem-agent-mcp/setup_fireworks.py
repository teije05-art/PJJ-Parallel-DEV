#!/usr/bin/env python3
"""
Setup script for Fireworks AI integration.
This script helps you test the Fireworks AI connection and set up your environment.
"""

import os
import sys

def test_fireworks_connection():
    """Test if Fireworks AI is properly configured."""
    try:
        # Check if API key is set
        api_key = os.getenv("FIREWORKS_API_KEY")
        if not api_key:
            print("❌ FIREWORKS_API_KEY environment variable not set!")
            print("   Please run: export FIREWORKS_API_KEY='your_api_key_here'")
            return False
        
        # Check if fireworks package is installed
        try:
            from fireworks import LLM
            print("✅ Fireworks AI package is installed")
        except ImportError:
            print("❌ Fireworks AI package not installed!")
            print("   Please run: pip install --upgrade fireworks-ai")
            return False
        
        # Test API connection
        print("🔄 Testing Fireworks AI connection...")
        llm = LLM(
            model="accounts/fireworks/models/llama-v3p3-70b-instruct",
            deployment_type="serverless",
            api_key=api_key
        )
        
        # Simple test request
        response = llm.chat.completions.create(
            messages=[{"role": "user", "content": "Hello! Please respond with just 'Hi there!'"}],
            max_tokens=50,
            temperature=0.1
        )
        
        print("✅ Fireworks AI connection successful!")
        print(f"   Model response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Fireworks AI connection failed: {e}")
        return False

def main():
    print("🚀 Fireworks AI Setup Test")
    print("=" * 40)
    
    if test_fireworks_connection():
        print("\n🎉 Everything is working! Your system is ready to use Llama 3.3 70B.")
        print("\nNext steps:")
        print("1. Start your MCP server: cd mem-agent-mcp && uv run python mcp_server/server.py")
        print("2. Connect Claude to your MCP server")
        print("3. Ask questions and enjoy the power of Llama 3.3 70B!")
    else:
        print("\n❌ Setup incomplete. Please fix the issues above and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
