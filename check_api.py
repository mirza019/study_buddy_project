from google import genai
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("❌ GEMINI_API_KEY missing in .env!")

client = genai.Client(api_key=API_KEY)

print("🔍 Testing Gemini API…")

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Hello! Can you verify that my Gemini API key is working?"
    )
    print("\n✅ GEMINI API KEY WORKS!\n")
    print("Model response:")
    print(response.text)

except Exception as e:
    print("\n❌ GEMINI TEST FAILED\n")
    print(e)
