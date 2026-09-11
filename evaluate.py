import os
import json
import time
from datetime import datetime, timezone
import pandas as pd
from agent import process_tweet

GOLDEN_CSV = "golden_dataset_labeled.csv"
OUTPUT_DIR = "evaluation_results"
SLEEP_BETWEEN_CALLS = 4      # 4 sec = safe for free tier
TEST_ALL = True              # True = full 200 rows
HEAD_N = 20                  # only if TEST_ALL=False

os.makedirs(OUTPUT_DIR, exist_ok=True)

try:
    df = pd.read_csv(GOLDEN_CSV)
except FileNotFoundError:
    print(f"Error: '{GOLDEN_CSV}' nahi mili.")
    exit()

test_data = df if TEST_ALL else df.head(HEAD_N)
total_tested = len(test_data)

print(f"Evaluation Pipeline Started... Testing on {total_tested} tweets.\n")

results = []
correct_intents = 0
correct_escalations = 0
api_errors = 0
start_time = time.time()


def process_row(tweet_id, tweet_text, human_intent, human_escalate, gold_reply):
    """Process one row and return (result_dict, is_error)."""
    try:
        ai_response = process_tweet(tweet_text)
    except Exception as e:
        ai_response = {"error": str(e)}

    if "error" in ai_response:
        return {
            "tweet_id": tweet_id,
            "text": tweet_text,
            "gold_intent": human_intent,
            "pred_intent": "",
            "intent_match": False,
            "gold_escalate": human_escalate,
            "pred_escalate": "",
            "escalate_match": False,
            "gold_reply": gold_reply,
            "pred_reply": "",
            "pred_reason": "",
            "error": ai_response["error"][:120],
        }, True

    ai_intent = str(ai_response.get("Intent", "")).strip()
    ai_escalate = str(ai_response.get("Escalate_Yes_No", "")).strip()
    ai_reply = str(ai_response.get("Ideal_Reply", "")).strip()
    ai_reason = str(ai_response.get("Escalate_Reason", "")).strip()

    return {
        "tweet_id": tweet_id,
        "text": tweet_text,
        "gold_intent": human_intent,
        "pred_intent": ai_intent,
        "intent_match": ai_intent.lower() == human_intent.lower(),
        "gold_escalate": human_escalate,
        "pred_escalate": ai_escalate,
        "escalate_match": ai_escalate.lower() == human_escalate.lower(),
        "gold_reply": gold_reply,
        "pred_reply": ai_reply,
        "pred_reason": ai_reason,
        "error": "",
    }, False


# ---------------- PASS 1: MAIN RUN ----------------
print(">>> PASS 1: Processing all tweets\n")

for i, (index, row) in enumerate(test_data.iterrows(), start=1):
    tweet_id = row.get("tweet_id", index)
    tweet_text = str(row["text"])
    human_intent = str(row.get("Intent", "")).strip()
    human_escalate = str(row.get("Escalate_Yes_No", "")).strip()
    gold_reply = str(row.get("Ideal_Reply", "")).strip()

    print(f"[{i}/{total_tested}] tweet_id={tweet_id}")

    result, is_err = process_row(tweet_id, tweet_text, human_intent, human_escalate, gold_reply)
    results.append(result)

    if is_err:
        api_errors += 1
        print(f"   -> API Error: {result['error'][:80]}")
    else:
        if result["intent_match"]:
            correct_intents += 1
        if result["escalate_match"]:
            correct_escalations += 1

    time.sleep(SLEEP_BETWEEN_CALLS)

# ---------------- PASS 2: RETRY FAILED ROWS ----------------
failed_indexes = [i for i, r in enumerate(results) if r["error"]]
if failed_indexes:
    print(f"\n>>> PASS 2: Retrying {len(failed_indexes)} failed rows after 30s cooldown\n")
    time.sleep(30)

    retried_ok = 0
    for idx in failed_indexes:
        r = results[idx]
        print(f"[retry] tweet_id={r['tweet_id']}")

        new_result, is_err = process_row(
            r["tweet_id"], r["text"], r["gold_intent"], r["gold_escalate"], r["gold_reply"]
        )

        if not is_err:
            # Pehle jo galti se count hua tha, agar tha, adjust nahi karna — pehle count nahi hua
            results[idx] = new_result
            api_errors -= 1
            retried_ok += 1

            if new_result["intent_match"]:
                correct_intents += 1
            if new_result["escalate_match"]:
                correct_escalations += 1

            print(f"   -> FIXED")
        else:
            print(f"   -> Still failing: {new_result['error'][:60]}")

        time.sleep(SLEEP_BETWEEN_CALLS)

    print(f"\nRetry summary: {retried_ok}/{len(failed_indexes)} recovered\n")

# ---------------- FINAL METRICS ----------------
elapsed = round(time.time() - start_time, 2)
successful = total_tested - api_errors

intent_acc = round((correct_intents / successful) * 100, 2) if successful else 0
esc_acc = round((correct_escalations / successful) * 100, 2) if successful else 0

metrics = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "total_tested": total_tested,
    "successful_responses": successful,
    "api_errors": api_errors,
    "intent_accuracy_pct": intent_acc,
    "escalation_accuracy_pct": esc_acc,
    "intent_correct": correct_intents,
    "escalation_correct": correct_escalations,
    "elapsed_seconds": elapsed,
    "avg_sec_per_call": round(elapsed / total_tested, 2) if total_tested else 0,
}

pd.DataFrame(results).to_csv(
    os.path.join(OUTPUT_DIR, "detailed_results.csv"), index=False
)
with open(os.path.join(OUTPUT_DIR, "metrics.json"), "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)

print("=" * 45)
print("FINAL EVALUATION REPORT")
print("=" * 45)
print(f"Total Tested        : {total_tested}")
print(f"Successful          : {successful}")
print(f"API Errors          : {api_errors}")
print(f"Intent Accuracy     : {intent_acc}% ({correct_intents}/{successful})")
print(f"Escalation Accuracy : {esc_acc}% ({correct_escalations}/{successful})")
print(f"Time Taken          : {elapsed}s (~{elapsed/60:.1f} min)")
print("=" * 45)
print(f"Detailed CSV : {OUTPUT_DIR}/detailed_results.csv")
print(f"Metrics JSON : {OUTPUT_DIR}/metrics.json")