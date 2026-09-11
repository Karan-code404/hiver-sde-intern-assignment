"""
Baselines for comparison against the AI agent.

1. Trivial baseline: always predict majority class + always "No" escalate
2. Keyword baseline: hand-written rules for intent + escalation
"""
import pandas as pd
import re

GOLDEN_CSV = "golden_dataset_labeled.csv"
OUTPUT_CSV = "evaluation_results/baseline_results.csv"

df = pd.read_csv(GOLDEN_CSV)
df["Intent"] = df["Intent"].astype(str).str.strip()
df["Escalate_Yes_No"] = df["Escalate_Yes_No"].astype(str).str.strip()

print(f"Loaded {len(df)} rows\n")

# ---------- TRIVIAL BASELINE ----------
majority_intent = df["Intent"].value_counts().idxmax()
majority_escalate = df["Escalate_Yes_No"].value_counts().idxmax()

trivial_intent_correct = (df["Intent"] == majority_intent).sum()
trivial_esc_correct = (df["Escalate_Yes_No"] == majority_escalate).sum()

trivial_intent_acc = trivial_intent_correct / len(df) * 100
trivial_esc_acc = trivial_esc_correct / len(df) * 100

print("=" * 55)
print("TRIVIAL BASELINE")
print("=" * 55)
print(f"Always predict Intent    : {majority_intent}")
print(f"Always predict Escalate  : {majority_escalate}")
print(f"Intent Accuracy          : {trivial_intent_acc:.1f}% ({trivial_intent_correct}/{len(df)})")
print(f"Escalation Accuracy      : {trivial_esc_acc:.1f}% ({trivial_esc_correct}/{len(df)})")


# ---------- KEYWORD BASELINE ----------
def keyword_intent(text):
    t = text.lower()

    # Order matters: most specific first
    if any(k in t for k in ["password", "apple id", "locked", "activation lock",
                             "sign in", "signin", "forgot my", "verification",
                             "2fa", "security"]):
        return "Apple_ID_Security"
    if any(k in t for k in ["charged", "payment", "paid", "billing", "refund",
                             "subscription", "membership", "apple pay",
                             "preorder", "purchase", "upgrade program"]):
        return "App_Store_Purchases"
    if any(k in t for k in ["crack", "broken", "screen", "battery health",
                             "won't charge", "not charging", "button",
                             "headphone", "earphone", "cable", "overheat",
                             "hardware", "repair"]):
        return "Hardware_Issue"
    if any(k in t for k in ["update", "ios 11", "ios11", "macos", "sierra",
                             "freez", "glitch", "crash", "slow", "lag",
                             "keyboard", "app won't", "won't open"]):
        return "Software_Update"

    # Pleasantries / acknowledgments
    stripped = re.sub(r"@\w+", "", t).strip()
    if len(stripped) < 40 and any(k in stripped for k in
        ["thanks", "thank you", "thx", "dm sent", "okay", "ok ", "done",
         "you're welcome", "cheers"]):
        return "Other"

    # Questions
    if any(k in t for k in ["how", "when", "what", "why", "can i",
                             "does", "is there", "warranty"]):
        return "General_Query"

    return "Other"


def keyword_escalate(text, intent):
    t = text.lower()

    # Escalate signals
    if intent in ("Apple_ID_Security", "App_Store_Purchases"):
        return "Yes"
    if intent == "Hardware_Issue" and any(k in t for k in
        ["crack", "broken", "damage", "won't turn on", "dead"]):
        return "Yes"
    if any(k in t for k in ["fuck", "damn", "shit", "wtf", "screw you",
                             "unprofessional", "lawsuit", "refund"]):
        return "Yes"
    if "all caps" in t:  # placeholder
        return "Yes"

    return "No"


kw_intent_correct = 0
kw_esc_correct = 0

for _, row in df.iterrows():
    pred_intent = keyword_intent(str(row["text"]))
    pred_esc = keyword_escalate(str(row["text"]), pred_intent)

    if pred_intent.lower() == str(row["Intent"]).lower():
        kw_intent_correct += 1
    if pred_esc.lower() == str(row["Escalate_Yes_No"]).lower():
        kw_esc_correct += 1

kw_intent_acc = kw_intent_correct / len(df) * 100
kw_esc_acc = kw_esc_correct / len(df) * 100

print("\n" + "=" * 55)
print("KEYWORD BASELINE")
print("=" * 55)
print(f"Intent Accuracy          : {kw_intent_acc:.1f}% ({kw_intent_correct}/{len(df)})")
print(f"Escalation Accuracy      : {kw_esc_acc:.1f}% ({kw_esc_correct}/{len(df)})")


# ---------- AI AGENT (from previous run) ----------
print("\n" + "=" * 55)
print("AI AGENT (from evaluation_results/metrics.json)")
print("=" * 55)
try:
    import json
    with open("evaluation_results/metrics.json") as f:
        m = json.load(f)
    print(f"Intent Accuracy          : {m['intent_accuracy_pct']}%")
    print(f"Escalation Accuracy      : {m['escalation_accuracy_pct']}%")
except FileNotFoundError:
    print("(metrics.json not found — run evaluate.py first)")


# ---------- SAVE ----------
summary = pd.DataFrame([
    {"Baseline": "Trivial (majority class)", "Intent_Acc": round(trivial_intent_acc, 1), "Esc_Acc": round(trivial_esc_acc, 1)},
    {"Baseline": "Keyword rules", "Intent_Acc": round(kw_intent_acc, 1), "Esc_Acc": round(kw_esc_acc, 1)},
])
summary.to_csv(OUTPUT_CSV, index=False)
print(f"\nSaved: {OUTPUT_CSV}")