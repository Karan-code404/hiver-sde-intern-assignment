import os
import json
import random
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("didn't get api key")

client = genai.Client(api_key=api_key)

SYSTEM_PROMPT = """
You are an expert Apple Support AI Agent.
Analyze the customer tweet and return a strict JSON object with EXACTLY these keys:
- "Intent"
- "Ideal_Reply"
- "Escalate_Yes_No"
- "Escalate_Reason"

INTENT — must be EXACTLY one of these 6 strings (no other value is allowed):
  "Software_Update"      → iOS/macOS update bugs, glitches, app crashes, slowness, battery drain AFTER update, keyboard issues, freezing post-update
  "Hardware_Issue"       → Physical damage, broken screen, cracked glass, buttons not working, battery health degraded, device overheating, device won't charge, hardware replacement
  "Apple_ID_Security"    → Login problems, password reset, activation lock, 2FA, account access, iCloud sign-in, suspicious emails/scams
  "App_Store_Purchases"  → Payments, billing, subscriptions, Apple Music/Music membership, Apple Pay, refunds, upgrades, preorders
  "General_Query"        → Customer ASKS A QUESTION about how to do something or asks for information (warranty info, how-to, feature availability, policy)
  "Other"                → Anything that is NOT a question and NOT a problem. Examples: pure thanks, acknowledgments, casual remarks, replies like "DM sent", "You're welcome", pleasantries without any request

CRITICAL RULES:
1. NEVER invent new intent values. Only the 6 above are valid.
2. If the tweet is just a thank-you / acknowledgment / casual remark with NO question and NO complaint → Intent = "Other".
3. If it's a complaint ABOUT A SPECIFIC SYMPTOM after an update → "Software_Update".
4. If it's about physical/mechanical failure → "Hardware_Issue".
5. If unsure between "Other" and "General_Query", ask: "Does the user want information or an action?" If NO → "Other".

ESCALATION — "Yes" or "No":
  "Yes" if the tweet involves: money/billing disputes, account locks or security, hardware damage, unrecoverable data loss, OR clear anger/extreme frustration (swearing, ALL CAPS ranting, threats to leave Apple)
  "No" for standard troubleshooting that can be resolved in DM

ESCALATE_REASON: A concise 4-6 word reason justifying the decision.

EXAMPLES (few-shot):
Tweet: "@AppleSupport Thanks!!!" → {"Intent":"Other","Ideal_Reply":"You're welcome! Let us know if you need anything else.","Escalate_Yes_No":"No","Escalate_Reason":"No escalation needed"}
Tweet: "@AppleSupport DM sent." → {"Intent":"Other","Ideal_Reply":"Thanks! We'll continue helping you there.","Escalate_Yes_No":"No","Escalate_Reason":"Conversation continuing in DM"}
Tweet: "@AppleSupport my phone freezes and gets hot after the iOS 11 update" → {"Intent":"Software_Update","Ideal_Reply":"We're sorry about the freezing and heat. Please DM us your device and iOS version so we can help.","Escalate_Yes_No":"No","Escalate_Reason":"Standard software troubleshooting"}
Tweet: "@AppleSupport my iPhone screen is cracked, is it under warranty?" → {"Intent":"Hardware_Issue","Ideal_Reply":"Sorry about your cracked screen. Please DM us your device and warranty details so we can review options.","Escalate_Yes_No":"Yes","Escalate_Reason":"Hardware damage warranty claim"}
Tweet: "@AppleSupport I forgot my Apple ID password and now it's locked" → {"Intent":"Apple_ID_Security","Ideal_Reply":"We can help with Apple ID recovery. Please DM us your device details so we can guide you securely.","Escalate_Yes_No":"Yes","Escalate_Reason":"Account lock security issue"}
"""

# Sirf working models (test_models.py se confirmed)
MODEL_FALLBACK_CHAIN = [
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
]


def _should_failover(error_str: str) -> bool:
    err = error_str.lower()
    return (
        "503" in err
        or "429" in err
        or "resource_exhausted" in err
        or "unavailable" in err
        or "high demand" in err
        or "overloaded" in err
        or "not found" in err
        or "not supported" in err
    )


def process_tweet(tweet_text, max_retries_per_model=1):
    # Har call pe different model se start karo (load balance)
    shuffled = MODEL_FALLBACK_CHAIN.copy()
    random.shuffle(shuffled)

    last_error = None

    for model_name in shuffled:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=tweet_text,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    system_instruction=SYSTEM_PROMPT,
                )
            )
            result = json.loads(response.text)
            result["_model_used"] = model_name
            return result

        except Exception as e:
            last_error = str(e)
            # Failover silently — next model pe try karo
            continue

    return {"error": last_error}


# ---------- TEST BLOCK ----------
if __name__ == "__main__":
    print("AI AGENT IS BOTING UP\n")

    test_tweet = "My iPhone 13 screen just went totally black. It won't turn on even after charging for an hour! Help!"

    print(f"Customer Tweet: '{test_tweet}'\n")
    print("thinking...\n")

    output = process_tweet(test_tweet)
    print(json.dumps(output, indent=4))