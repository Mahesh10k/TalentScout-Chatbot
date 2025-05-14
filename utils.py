import requests
import os
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Gemini API setup
API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = os.getenv("GEMINI_API_URL") + API_KEY

def apply_custom_css():
    st.markdown("""
        <style>
        @media only screen and (max-width: 768px) {
            .element-container {
                padding: 0 !important;
                margin: 0 !important;
                color: black !important;
            }
            .stChatInput input {
                font-size: 16px !important;
            }
        }
        .stChatMessage {
            background-color: #f1f1f1;
            padding: 10px 15px;
            border-radius: 10px;
            margin-bottom: 8px;
            max-width: 95%;
            word-wrap: break-word;
        }
        .stMarkdown p, .stMarkdown span {
            color: black !important;
        }
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)

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

# MongoDB integration
MONGO_URI = os.getenv("MONGO_URI")

def store_user_data(data):
    try:
        client = MongoClient(MONGO_URI)
        db = client["Talent_Scout"]
        collection = db["interviews"]
        collection.insert_one(data)
    except Exception as e:
        st.error(f"❌ Failed to save to MongoDB: {e}")
