
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load env if present
load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    api_key = input("Enter your GOOGLE_API_KEY: ").strip()

genai.configure(api_key=api_key)



print("Checking API Key setup...")
if api_key and len(api_key) > 8:
    print(f"Key detected: {api_key[:4]}...{api_key[-4:]}")
elif api_key:
    print("Key detected (short).")
else:
    print("No GOOGLE_API_KEY found.")

print("\n--- Listing Models ---")
try:
    models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
            models.append(m.name)
            
    if not models:
        print("WARNING: No models found. This usually means the API Key is invalid or has no access to Generative Language API.")
    else:
        print(f"\nFound {len(models)} models.")
        
        # Try a test generation
        print("\n--- Testing Generation with gemini-1.5-flash ---")
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Hello, are you working?")
        print(f"Success! Response: {response.text}")

except Exception as e:
    print(f"\nERROR: {e}")
    print("Common causes:")
    print("1. API Key is for Google Cloud Vertex AI service account (not supported by this library directly).")
    print("2. Generative Language API is not enabled in Google Cloud Console.")
    print("3. Billing is required for this project but not enabled.")
