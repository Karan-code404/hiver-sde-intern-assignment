"""
LLM-as-Judge for reply quality evaluation.

Rates each AI-generated reply on 4 dimensions (1-5 scale):
- Empathy: Does it acknowledge the customer's frustration?
- Relevance: Does it address the actual issue?
- Actionability: Does it move toward resolution?
- Professionalism: Is the tone Apple-appropriate?

Overall score = average of 4 dimensions.
"""

import os
import json
import time
import random
import pandas as pd
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

JUDGE_MODELS = [
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
]

JUDGE_SYSTEM_PROMPT = """
You are an expert evaluator of customer-support replies for Apple Support.

Rate the ASSISTANT_REPLY on 4 dimensions, each on a 1-5 integer scale:

1. Empathy (1-5):
   1 = Cold, robotic, dismissive
   3 = Neutral acknowledgment
   5 = Genuinely acknowledges the customer's frustration

2. Relevance (1-5):
   1 = Off-topic or ignores the actual issue
   3 = Partially addresses the issue
   5 = Directly addresses the exact problem described

3. Actionability (1-5):
   1 = No next step offered
   3 = Vague next step ("contact us")
   5 = Clear, specific next step (e.g., "DM us your device + iOS version")

4. Professionalism (1-5):
   1 = Rude, unprofessional, or emoji-heavy
   3 = Acceptable but generic
   5 = Polished, Apple-brand-appropriate

Return STRICT JSON only, with these exact keys:
{
  "empathy": <int 1-5>,
  "relevance": <int 1-5>,
  "actionability": <int 1-5>,
  "professionalism": <int 1-5>,
  "overall": <float, average of the four>,
  "reason": "<one short sentence justifying the overall score>"
}
"""


def judge_reply(tweet_text: str, gold_reply: str, ai_reply: str, max_attempts=3):
    """Rate one AI reply. Returns dict with scores."""
    prompt = f"""
CUSTOMER_TWEET:
{tweet_text}

HUMAN_REFERENCE_REPLY (for context, not required to match):
{gold_reply}

ASSISTANT_REPLY (to evaluate):
{ai_reply}

Return your scores as strict JSON.
"""
    shuffled = JUDGE_MODELS.copy()
    random.shuffle(shuffled)
    last_err = None

    for model_name in shuffled:
        for attempt in range(max_attempts):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        system_instruction=JUDGE_SYSTEM_PROMPT,
                    )
                )
                result = json.loads(response.text)
                result["_judge_model"] = model_name
                return result
            except Exception as e:
                last_err = str(e)
                if "503" in last_err or "429" in last_err or "unavailable" in last_err.lower():
                    break
                time.sleep(2 * (attempt + 1))

    return {"error": last_err}


def main():
    input_csv = "evaluation_results/detailed_results.csv"
    output_csv = "evaluation_results/judge_results.csv"

    if not os.path.exists(input_csv):
        print(f"Error: {input_csv} not found. Run evaluate.py first.")
        return

    df = pd.read_csv(input_csv)
    print(f"Judging {len(df)} replies...\n")

    results = []
    for i, row in df.iterrows():
        if not row.get("pred_reply"):
            # Skip rows with no AI reply
            continue

        print(f"[{i+1}/{len(df)}] tweet_id={row['tweet_id']}")

        scores = judge_reply(
            tweet_text=str(row["text"]),
            gold_reply=str(row.get("gold_reply", "")),
            ai_reply=str(row["pred_reply"]),
        )

        results.append({
            "tweet_id": row["tweet_id"],
            "ai_reply": row["pred_reply"],
            "empathy": scores.get("empathy"),
            "relevance": scores.get("relevance"),
            "actionability": scores.get("actionability"),
            "professionalism": scores.get("professionalism"),
            "overall": scores.get("overall"),
            "reason": scores.get("reason"),
            "judge_model": scores.get("_judge_model"),
            "error": scores.get("error", ""),
        })

        time.sleep(3)

    out_df = pd.DataFrame(results)
    out_df.to_csv(output_csv, index=False)

    # Summary
    valid = out_df[out_df["error"] == ""]
    print("\n" + "=" * 50)
    print("JUDGE SUMMARY")
    print("=" * 50)
    print(f"Total judged   : {len(valid)}")
    print(f"Errors         : {len(out_df) - len(valid)}")
    print(f"Mean overall   : {valid['overall'].mean():.2f} / 5.00")
    print(f"Mean empathy   : {valid['empathy'].mean():.2f}")
    print(f"Mean relevance : {valid['relevance'].mean():.2f}")
    print(f"Mean actionab. : {valid['actionability'].mean():.2f}")
    print(f"Mean profess.  : {valid['professionalism'].mean():.2f}")
    print("=" * 50)
    print(f"Saved: {output_csv}")


if __name__ == "__main__":
    main()