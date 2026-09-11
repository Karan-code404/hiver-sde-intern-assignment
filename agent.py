import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
api_key=os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("didn't get api key")

client=genai.Client(api_key=api_key)

SYSTEM_PROMPT = """
You are an expert Apple Support AI Agent. 
Analyze the customer tweet and return a strict JSON object with EXACTLY these keys:
- "Intent": (Must be exactly one of: Software_Update, Hardware_Issue, Apple_ID_Security, App_Store_Purchases, General_Query, Other)
- "Ideal_Reply": (Short, highly empathetic, professional Apple-style reply. Max 2 sentences)
- "Escalate_Yes_No": ("Yes" or "No". Yes if it involves hardware damage, money, account locks, or extreme frustration)
- "Escalate_Reason": (A concise 4-6 word reason justifying the escalation decision)
"""


def process_tweet(tweet_text):

    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=tweet_text,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                system_instruction=SYSTEM_PROMPT,
            )
        )
        
        result_dict = json.loads(response.text)
        return result_dict

    except Exception as e:
        return {"error": str(e)}

if __name__=="__main__":
    print("AI AGENT IS BOTING UP\n")

    test_tweet="My iPhone 13 screen just went totally black. It won't turn on even after charging for an hour! Help!"

    print(f"Customer Tweet: '{test_tweet}'\n")
    print("thinking...\n")
    
  
    output = process_tweet(test_tweet)
    
    print(json.dumps(output, indent=4))
