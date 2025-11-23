import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("Error: GOOGLE_API_KEY not found in environment variables.")
    exit(1)

print(f"API Key found: {api_key[:4]}...{api_key[-4:]}")

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    print("Attempting to generate content...")
    response = model.generate_content("Hello, are you working?")
    
    print("Response received:")
    print(response.text)
    print("API Key verification SUCCESSFUL.")
    
except Exception as e:
    print(f"API Key verification FAILED. Error: {e}")
