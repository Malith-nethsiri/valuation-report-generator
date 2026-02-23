"""
Google Cloud Vision API client for OCR text extraction.
"""

import base64
import os
import requests


def extract_text_from_image(image_data: bytes) -> str:
    """
    Extract all text from an image using Google Cloud Vision API REST endpoint.

    Args:
        image_data: Raw image bytes

    Returns:
        Extracted text as a single string
    """
    try:
        # GOOGLE_VISION_API_KEY is required - no fallback to GOOGLE_MAPS_API_KEY
        # Vision API should use its own dedicated key with appropriate quotas
        api_key = os.getenv("GOOGLE_VISION_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_VISION_API_KEY environment variable is required")

        # Encode image to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')

        # Google Vision API endpoint
        url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"

        # Request payload with enhanced image context for better accuracy
        payload = {
            "requests": [
                {
                    "image": {
                        "content": base64_image
                    },
                    "features": [
                        {
                            "type": "DOCUMENT_TEXT_DETECTION",
                            "maxResults": 50
                        }
                    ],
                    "imageContext": {
                        "languageHints": ["en", "si"],
                        "textDetectionParams": {
                            "enableTextDetectionConfidenceScore": True
                        }
                    }
                }
            ]
        }

        # Make API request
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()

        # Extract text from response
        if 'responses' in result and len(result['responses']) > 0:
            first_response = result['responses'][0]

            if 'error' in first_response:
                error_msg = first_response['error'].get('message', 'Unknown error')
                raise Exception(f"Google Vision API error: {error_msg}")

            extracted_text = ""
            if 'fullTextAnnotation' in first_response:
                extracted_text = first_response['fullTextAnnotation']['text']
            elif 'textAnnotations' in first_response and len(first_response['textAnnotations']) > 0:
                extracted_text = first_response['textAnnotations'][0]['description']

            return extracted_text

        return ""

    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {str(e)}")
    except Exception as e:
        raise Exception(f"Text extraction failed: {str(e)}")
