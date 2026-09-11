import pandas as pd

df = pd.read_csv("evaluation_results/judge_results.csv")

# Fix: NaN ko empty string banao
df["error"] = df["error"].fillna("")

df = df[df["error"] == ""].reset_index(drop=True)

print(f"Total valid judged rows: {len(df)}")

if len(df) < 15:
    print(f"WARNING: Only {len(df)} valid rows. Need at least 15 for human sample.")
    exit()

# Reproducible random sample
sample = df.sample(n=15, random_state=42)

output = sample[["tweet_id", "ai_reply", "empathy", "relevance",
                 "actionability", "professionalism", "overall"]].copy()
output = output.rename(columns={
    "empathy": "judge_empathy",
    "relevance": "judge_relevance",
    "actionability": "judge_actionability",
    "professionalism": "judge_professionalism",
    "overall": "judge_overall",
})
output["human_empathy"] = ""
output["human_relevance"] = ""
output["human_actionability"] = ""
output["human_professionalism"] = ""
output["human_overall"] = ""

output.to_csv("evaluation_results/human_sample.csv", index=False)
print(f"\nSampled 15 rows -> evaluation_results/human_sample.csv")
print("Judge scores already filled in judge_* columns.")
print("Now fill in human_* columns manually (1-5 scale).")