"""Test script to verify Anthropic API credentials"""
import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("ANTHROPIC_API_KEY")

print(f"API Key found: {api_key[:20]}..." if api_key else "No API key found!")

if not api_key:
    print("ERROR: No ANTHROPIC_API_KEY found in .env file")
    exit(1)

print("\nTesting Anthropic API...")

try:
    # Initialize Anthropic client
    client = Anthropic(api_key=api_key)

    # Make a simple test request
    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": "Say 'Hello, API test successful!'"
            }
        ]
    )

    # Extract the response
    response_text = response.content[0].text.strip()

    print("\n[SUCCESS] Anthropic API key is valid and working!")
    print(f"Response: {response_text}")
    print(f"\nModel: {response.model}")
    print(f"Role: {response.role}")

except Exception as e:
    print(f"\n[FAILED] Anthropic API error: {str(e)}")
    print(f"\nError type: {type(e).__name__}")

    # Check for specific error types
    if "authentication" in str(e).lower() or "api key" in str(e).lower() or "credential" in str(e).lower():
        print("\n*** This appears to be an authentication/credential error ***")
        print("The API key may be:")
        print("  1. Invalid or expired")
        print("  2. Not activated")
        print("  3. Missing required permissions")
        print("\nPlease check your Anthropic API key at: https://console.anthropic.com/")
