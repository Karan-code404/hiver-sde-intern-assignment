"""
Auto-agreement: runs proxy annotator on 30 rows, computes metrics,
and writes the agreement section into REPORT.md automatically.
"""
import os, json, time, random
import pandas as pd
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PROXY_PROMPT = """
You are a QUALITY REVIEWER evaluating customer-support replies.
Score the reply on a single 1-5 integer scale for OVERALL QUALITY:
1 = Poor, 2 = Below average, 3 = Average, 4 = Good, 5 = Excellent.
Return STRICT JSON: {"overall": <int 1-5>, "reason": "<short sentence>"}
"""

MODELS = ["gemini-3.7-flash", "gemini-3.8-flash", "gemini-3.5-flash-lite"]


def proxy_score(ai_reply, max_attempts=3):
    shuffled = MODELS.copy(); random.shuffle(shuffled)
    last_err = None
    for m in shuffled:
        for attempt in range(max_attempts):
            try:
                r = client.models.generate_content(
                    model=m,
                    contents=f"REPLY:\n{ai_reply}\n\nReturn strict JSON.",
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        system_instruction=PROXY_PROMPT,
                    )
                )
                d = json.loads(r.text); d["_model"] = m
                return d
            except Exception as e:
                last_err = str(e)
                if any(x in last_err for x in ["503","429","unavailable","RESOURCE_EXHAUSTED"]):
                    break
                time.sleep(2 * (attempt + 1))
    return {"error": last_err}


def main():
    df = pd.read_csv("evaluation_results/judge_results.csv")
    df["error"] = df["error"].fillna("")
    df = df[(df["error"] == "") & (df["overall"].notna())].reset_index(drop=True)

    n = min(30, len(df))
    sample = df.sample(n=n, random_state=42)
    print(f"Running proxy annotator on {n} rows...\n")

    results = []
    for i, row in sample.iterrows():
        print(f"[{i+1}/{n}] tweet_id={row['tweet_id']}")
        s = proxy_score(str(row["ai_reply"]))
        results.append({
            "tweet_id": row["tweet_id"],
            "judge_overall": float(row["overall"]),
            "proxy_overall": s.get("overall"),
            "proxy_reason": s.get("reason", ""),
            "error": s.get("error", ""),
        })
        time.sleep(3)

    out = pd.DataFrame(results)
    out.to_csv("evaluation_results/proxy_agreement.csv", index=False)

    valid = out[out["error"].fillna("") == ""].copy()
    valid["judge_overall"] = valid["judge_overall"].astype(float)
    valid["proxy_overall"] = valid["proxy_overall"].astype(float)

    print("\n" + "=" * 55)
    print("JUDGE vs PROXY ANNOTATOR AGREEMENT")
    print("=" * 55)
    print(f"Rows compared : {len(valid)}")
    print(f"Errors        : {len(out) - len(valid)}")

    mae = pearson = kappa = None
    if len(valid) >= 2:
        mae = (valid["judge_overall"] - valid["proxy_overall"]).abs().mean()
        pearson = valid["judge_overall"].corr(valid["proxy_overall"])
        try:
            from sklearn.metrics import cohen_kappa_score
            j = valid["judge_overall"].round().astype(int)
            p = valid["proxy_overall"].round().astype(int)
            kappa = cohen_kappa_score(j, p, weights="quadratic")
        except ImportError:
            print("(install scikit-learn for kappa)")

        print(f"Mean Abs Error: {mae:.2f}")
        print(f"Pearson r     : {pearson:.3f}")
        if kappa is not None:
            print(f"Cohen's kappa : {kappa:.3f}")
    print("=" * 55)

    # Auto-write agreement section into REPORT.md
    section = f"""
## 11. Inter-Annotator Agreement (LLM-as-Judge Reliability)

The LLM judge was validated against a second independent LLM annotator
with a differently-worded rubric, on a random 30-row sample.

| Metric | Value |
|---|---|
| Rows compared | {len(valid)} |
| Mean Absolute Error | {f'{mae:.2f}' if mae is not None else 'N/A'} |
| Pearson correlation | {f'{pearson:.3f}' if pearson is not None else 'N/A'} |
| Cohen's kappa (quadratic) | {f'{kappa:.3f}' if kappa is not None else 'N/A'} |

**Interpretation:** {"Strong" if kappa and kappa > 0.6 else "Moderate" if kappa and kappa > 0.4 else "Weak"} agreement between the two judges.
Because both annotators are LLMs, this represents an upper bound on human
agreement. True human agreement would likely be lower.

*Note: Human annotation was not feasible within the assignment window; a proxy LLM annotator was used and this limitation is disclosed.*
"""
    with open("REPORT.md", "a", encoding="utf-8") as f:
        f.write(section)
    print("Appended agreement section to REPORT.md")


if __name__ == "__main__":
    main()