# test_groq_models.py
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def test_model(model_name, description):
    print(f"\nTesting → {model_name} ({description})")
    print("-" * 60)
    
    try:
        response = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": "In 3 sentences, explain quantum entanglement like I'm your girlfriend and you're proud of me for asking. Be cute, romantic, and smart."
            }],
            model=model_name,
            temperature=0.7,
            max_tokens=200
        )
        print(response.choices[0].message.content.strip())
        print(f"Success! Speed: very fast on Groq")
    except Exception as e:
        print(f"Failed: {e}")

# Run the test
print("Study Buddy Model Test — December 2025\n")

test_model("llama3-8b-8192", "Your current weak model")
test_model("llama-3.3-70b-versatile", "BEST FREE MODEL — RECOMMENDED")
test_model("gemma2-9b-it", "Fast & cute alternative")
test_model("mixtral-8x7b-32768", "Creative but slower")

print("\nDone! See the difference?")
print("Replace all 'llama3-8b-8192' → 'llama-3.3-70b-versatile' in your query_pdf.py")