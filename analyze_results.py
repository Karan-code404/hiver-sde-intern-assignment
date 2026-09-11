import pandas as pd

df = pd.read_csv("evaluation_results/detailed_results.csv")

print("=" * 60)
print("INTENT CONFUSION ANALYSIS")
print("=" * 60)

# Intent mismatch rows
mismatch = df[df["intent_match"] == False]
print(f"\nTotal intent mismatches: {len(mismatch)}/{len(df)}\n")

print("Confusion pairs (gold -> predicted):")
print("-" * 60)
pairs = mismatch.groupby(["gold_intent", "pred_intent"]).size().sort_values(ascending=False)
for (g, p), count in pairs.items():
    print(f"  {g:22} -> {p:22} : {count}")

print("\n" + "=" * 60)
print("ESCALATION MISMATCH ANALYSIS")
print("=" * 60)

esc_mismatch = df[df["escalate_match"] == False]
print(f"\nTotal escalation mismatches: {len(esc_mismatch)}/{len(df)}\n")

print("Escalation confusion (gold -> predicted):")
print("-" * 60)
esc_pairs = esc_mismatch.groupby(["gold_escalate", "pred_escalate"]).size().sort_values(ascending=False)
for (g, p), count in esc_pairs.items():
    print(f"  {g:6} -> {p:6} : {count}")

print("\n" + "=" * 60)
print("PER-CLASS INTENT ACCURACY")
print("=" * 60)
for intent in df["gold_intent"].unique():
    sub = df[df["gold_intent"] == intent]
    acc = sub["intent_match"].mean() * 100
    print(f"  {intent:22} : {acc:5.1f}%  ({sub['intent_match'].sum()}/{len(sub)})")