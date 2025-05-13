import requests
import os

from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = os.getenv("GEMINI_API_URL") + API_KEY

def ask_gemini_via_api(prompt):
    headers = {
        "Content-Type": "application/json",
    }

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 1,
            "topP": 1,
            "maxOutputTokens": 1024,
            "stopSequences": []
        }
    }

    try:
        response = requests.post(BASE_URL, headers=headers, json=body)
        response.raise_for_status()
        content = response.json()
        return content["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"⚠️ Error fetching response: {e}"
