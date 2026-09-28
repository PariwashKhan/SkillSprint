"""Direct GenAI test via OpenRouter."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import os
from dotenv import load_dotenv
load_dotenv()

print("=" * 70)
print("OPENROUTER TEST")
print("=" * 70)
key = os.getenv("OPENAI_API_KEY", "")
print(f"Key:   {key[:20]}... (len {len(key)})")
print(f"Base:  {os.getenv('OPENAI_BASE_URL')}")
print(f"Model: {os.getenv('OPENAI_MODEL')}")
print(f"Provider: {os.getenv('GENAI_PROVIDER')}")
print("=" * 70)

print("\nTEST: Real call to OpenRouter")
print("-" * 70)
try:
    from openai import OpenAI
    client = OpenAI(
        api_key=key,
        base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"),
    )
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "google/gemini-2.0-flash-exp:free"),
        messages=[{"role": "user", "content": "Say hello in exactly 3 words."}],
    )
    print("SUCCESS")
    print("Response:", response.choices[0].message.content)
except Exception as e:
    print("FAILED")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {e}")
    import traceback
    traceback.print_exc()