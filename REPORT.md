# Hiver AI Agent — Apple Support Tweet Classifier

An LLM-powered support agent that reads Apple Support tweets and returns structured triage: **Intent classification**, **drafted reply**, and **escalation decision**. Built with Google Gemini and evaluated on a 200-row hand-labeled golden dataset.

---

## Headline Results

| Metric | Score |
|---|---|
| **Intent Classification Accuracy** | **85.0%** (170/200) |
| **Escalation Decision Accuracy** | **88.5%** (177/200) |
| **Reply Quality (LLM judge)** | **4.73 / 5.00** (n=109 valid) |
| API Errors (recovered) | 0 / 200 |
| Evaluation Runtime | ~21 min |

**Baseline comparison:**

| Baseline | Intent Accuracy | Escalation Accuracy |
|---|---|---|
| Trivial (majority class) | 49.5% | 65.5% |
| Keyword rules | 52.5% | 73.0% |
| **Our agent** | **85.0%** | **88.5%** |

See [REPORT.md](REPORT.md) for full analysis and [DECISION_LOG.md](DECISION_LOG.md) for engineering decisions.

---

## Project Structure

    hiver-ai-agent/
    ├── agent.py                      # Core LLM agent (Gemini + fallback chain)
    ├── evaluate.py                   # Evaluation harness (2-pass, retry, metrics)
    ├── analyze_results.py            # Confusion matrix + per-class analysis
    ├── judge.py                      # LLM-as-judge for reply quality
    ├── baselines.py                  # Trivial + keyword baselines
    ├── golden_dataset_labeled.csv    # 200 manually labeled tweets
    ├── evaluation_results/
    │   ├── metrics.json              # Final intent/escalation metrics
    │   ├── detailed_results.csv      # Per-row predictions vs gold labels
    │   ├── judge_results.csv         # Per-reply judge scores
    │   └── baseline_results.csv      # Baseline comparison numbers
    ├── REPORT.md                     # Evaluation report (14 sections)
    ├── DECISION_LOG.md               # 12 engineering decisions
    ├── requirements.txt
    ├── .env.example
    └── README.md

---

## Setup (Under 5 Minutes)

### 1. Clone the repo

    git clone <your-repo-url>
    cd hiver-ai-agent

### 2. Create virtual environment

    python -m venv venv

    # Windows
    venv\Scripts\activate

    # Mac / Linux
    source venv/bin/activate

### 3. Install dependencies

    pip install -r requirements.txt

### 4. Configure API key

    # Windows
    copy .env.example .env

    # Mac / Linux
    cp .env.example .env

Then edit `.env` and add your Gemini API key:

    GEMINI_API_KEY=your_key_here

Get a free key at https://aistudio.google.com/apikey

---

## Reproduce Headline Results (Under 15 Minutes)

The full evaluation on 200 tweets takes ~21 minutes due to rate limiting on the free tier. To reproduce **under 15 minutes**, run the quick subset:

### Option A: Fast verification (5 tweets, ~30 seconds)

Edit `evaluate.py`:

    TEST_ALL = False
    HEAD_N = 5

Then run:

    python evaluate.py

### Option B: Full reproduction (~21 min, all 200 tweets)

Edit `evaluate.py`:

    TEST_ALL = True

Then run:

    python evaluate.py

Either option produces:

- `evaluation_results/metrics.json` — headline metrics
- `evaluation_results/detailed_results.csv` — per-row output

### Option C: Full reproduction with acceleration (no rate limit wait)

Set `SLEEP_BETWEEN_CALLS = 1` in `evaluate.py`. This runs the full 200 tweets in ~5 minutes but may hit free-tier rate limits. Fallback models handle most 429/503 errors automatically.

---

## Usage

### Test the agent on a single tweet

    python agent.py

### Run full evaluation

    python evaluate.py

### Analyze confusion matrix

    python analyze_results.py

### Run LLM-as-judge on replies

    python judge.py

### Run baselines (no API needed)

    python baselines.py

---

## Agent Output Format

`process_tweet(tweet_text)` returns strict JSON:

    {
      "Intent": "Hardware_Issue",
      "Ideal_Reply": "We're sorry about your screen...",
      "Escalate_Yes_No": "Yes",
      "Escalate_Reason": "Potential hardware failure"
    }

**Valid Intent values:** `Software_Update`, `Hardware_Issue`, `Apple_ID_Security`, `App_Store_Purchases`, `General_Query`, `Other`

**Escalation rule (heuristic):** `Yes` for hardware damage, money/billing disputes, account locks, unrecoverable data loss, or extreme anger.

---

## Design Highlights

- **Structured JSON output** enforced via Gemini's `response_mime_type="application/json"` — no regex parsing, no schema drift.
- **Multi-model fallback chain** with random rotation (`gemini-3.7-flash` → `3.8-flash` → `3.5-flash-lite` → `3.6-flash`) to survive per-model quota exhaustion.
- **Two-pass evaluation** — Pass 1 processes all tweets; Pass 2 retries transient network failures after a 30s cooldown. Achieved 5/5 recovery on network errors.
- **LLM-as-judge** rates reply quality on 4 dimensions: Empathy, Relevance, Actionability, Professionalism (each 1–5).
- **Few-shot prompt engineering** lifted intent accuracy from 65% → 85% without any model change or fine-tuning.
- **Baseline comparison** against trivial (majority class) and keyword-rules approaches — the agent leads by **+32 to +35 points** on intent.

---

## What Is Misleading About Our Headline Number?

The 85% intent accuracy and 88.5% escalation accuracy come with caveats:

1. **Class imbalance:** `Software_Update` is 49.5% of the dataset. A constant classifier already hits ~50%.
2. **Self-evaluation bias:** The LLM judge is the same model family as the agent — the 4.73/5 reply-quality score is inflated.
3. **Single-annotator golden set:** No inter-annotator agreement was measured.
4. **Judge–human agreement incomplete:** Noted as a limitation in REPORT.md §8.3.

See [REPORT.md §8](REPORT.md) for the full disclosure.

---

## Requirements

- Python 3.9+
- Google Gemini API key (free tier works)
- See `requirements.txt`

---

## Documentation

- **[REPORT.md](REPORT.md)** — Full 14-section evaluation report: problem framing, results vs baselines, failure analysis, misleading-number section, next steps.
- **[DECISION_LOG.md](DECISION_LOG.md)** — 12 non-obvious engineering decisions with reasoning.

---

## Citations

- **Dataset:** Sanders, N., et al. *Customer Support on Twitter.* Kaggle. https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter
- **Banking77 (referenced):** Casanueva, I., et al. *Efficient Intent Detection with Dual Sentence Encoders.* NLP4ConvAI 2020.
- **LLM:** Google Gemini 3.6 Flash / 3.7 Flash / 3.8 Flash / 3.5 Flash-Lite. https://ai.google.dev/gemini-api/docs/models

**AI assistance disclosure:** AI coding assistants were used for code scaffolding, prompt iteration, and report drafting. All engineering decisions, dataset labeling, and metric interpretation were done by the author.

---

## License

For Hiver take-home assignment evaluation only.