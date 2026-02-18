
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load env if present
load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    api_key = input("Enter your GOOGLE_API_KEY: ").strip()

genai.configure(api_key=api_key)

print("Listing available models for this API Key...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
