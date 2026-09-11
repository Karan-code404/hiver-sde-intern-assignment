import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

candidates = [
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]

for m in candidates:
    try:
        r = client.models.generate_content(model=m, contents="say hi")
        print(f"OK   {m}")
    except Exception as e:
        short = str(e)[:80]
        print(f"FAIL {m} -> {short}")