# Hiver AI Agent — Apple Support Tweet Classifier

An LLM-powered support agent that reads Apple Support tweets and returns structured triage: **Intent classification**, **drafted reply**, and **escalation decision**. Built with Google Gemini and evaluated on a 200-row manually labeled golden dataset.

## Results

| Metric | Score |
|---|---|
| Intent Classification Accuracy | **85.0%** (170/200) |
| Escalation Decision Accuracy | **88.5%** (177/200) |
| API Errors | 0 / 200 |
| Evaluation Runtime | ~21 min |

See [REPORT.md](REPORT.md) for full analysis and [DECISION_LOG.md](DECISION_LOG.md) for engineering choices.

## Project Structure

    hiver-ai-agent/
    ├── agent.py                      # Core LLM agent (Gemini + fallback chain)
    ├── evaluate.py                   # Evaluation harness (2-pass, retry, metrics)
    ├── analyze_results.py            # Confusion matrix + per-class analysis
    ├── golden_dataset_labeled.csv    # 200 manually labeled tweets
    ├── evaluation_results/
    │   ├── metrics.json              # Final metrics
    │   └── detailed_results.csv      # Per-row predictions vs gold labels
    ├── REPORT.md                     # Evaluation report
    ├── DECISION_LOG.md               # Engineering decision log
    ├── requirements.txt
    ├── .env.example
    └── README.md

## Setup

1. Clone the repo

        git clone <your-repo-url>
        cd hiver-ai-agent

2. Create virtual environment

        python -m venv venv
        venv\Scripts\activate        # Windows
        source venv/bin/activate     # Mac/Linux

3. Install dependencies

        pip install -r requirements.txt

4. Set up API key

        copy .env.example .env       # Windows
        cp .env.example .env         # Mac/Linux

   Then edit `.env` and add your Gemini API key:

        GEMINI_API_KEY=your_key_here

   Get a free key at https://aistudio.google.com/apikey

## Usage

Test the agent on a single tweet:

    python agent.py

Run full evaluation (200 tweets, ~21 min):

    python evaluate.py

Results are saved to `evaluation_results/`.

Analyze confusion matrix:

    python analyze_results.py

## Agent Output Format

`process_tweet(tweet_text)` returns a strict JSON:

    {
      "Intent": "Hardware_Issue",
      "Ideal_Reply": "We're sorry about your screen...",
      "Escalate_Yes_No": "Yes",
      "Escalate_Reason": "Potential hardware failure"
    }

**Valid Intent values:** `Software_Update`, `Hardware_Issue`, `Apple_ID_Security`, `App_Store_Purchases`, `General_Query`, `Other`

## Design Highlights

- Structured JSON output enforced by Gemini's `response_mime_type` — no regex parsing.
- Multi-model fallback chain with random rotation to avoid per-model quota limits.
- Two-pass evaluation with 30s cooldown — recovers transient network failures.
- Few-shot prompt engineering — improved intent accuracy from 65% → 85% without model changes.

## Requirements

- Python 3.9+
- Google Gemini API key (free tier works)
- See `requirements.txt`

## License

For Hiver take-home assignment evaluation only.