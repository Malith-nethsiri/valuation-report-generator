"""Test script to verify Google Vision API credentials"""
import os
import requests
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("GOOGLE_VISION_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")

print(f"API Key found: {api_key[:20]}..." if api_key else "No API key found!")

if not api_key:
    print("ERROR: No GOOGLE_VISION_API_KEY or GOOGLE_MAPS_API_KEY found in .env file")
    exit(1)

# Create a simple test image (1x1 red pixel PNG)
test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="

# Google Vision API endpoint
url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"

# Request payload
payload = {
    "requests": [
        {
            "image": {
                "content": test_image_base64
            },
            "features": [
                {
                    "type": "TEXT_DETECTION",
                    "maxResults": 1
                }
            ]
        }
    ]
}

print("\nTesting Google Vision API...")
print(f"Endpoint: {url[:60]}...")

try:
    response = requests.post(url, json=payload, timeout=30)
    print(f"\nResponse Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")

    if response.status_code == 200:
        result = response.json()
        print("\n[SUCCESS] API key is valid and Vision API is working.")
        print(f"Response: {result}")

        # Check for errors within the response
        if 'responses' in result and len(result['responses']) > 0:
            first_response = result['responses'][0]
            if 'error' in first_response:
                print(f"\n[ERROR IN RESPONSE] Even though status is 200, Vision API returned an error:")
                print(f"Error message: {first_response['error'].get('message', 'Unknown')}")
                print(f"Error code: {first_response['error'].get('code', 'Unknown')}")
                print(f"Error details: {first_response['error'].get('details', 'None')}")
            else:
                print("\n[OK] No errors in Vision API response.")
    else:
        print(f"\n[FAILED] Status code: {response.status_code}")
        print(f"Response body: {response.text}")

        # Try to parse error
        try:
            error_data = response.json()
            if 'error' in error_data:
                print(f"\nError message: {error_data['error'].get('message', 'Unknown')}")
                print(f"Error status: {error_data['error'].get('status', 'Unknown')}")
                print(f"Error code: {error_data['error'].get('code', 'Unknown')}")
        except:
            pass

except requests.exceptions.RequestException as e:
    print(f"\n[REQUEST FAILED]: {str(e)}")
except Exception as e:
    print(f"\n[UNEXPECTED ERROR]: {str(e)}")
