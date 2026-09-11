# Decision Log

Track of key engineering decisions made during development.

---

### D1. Choose Gemini over OpenAI / Anthropic
Decision: Use Google Gemini 3.6 Flash as the LLM.
Reason: Free tier available, fast inference, native JSON mode via `response_mime_type`.
Alternatives considered: OpenAI GPT-4o (cost), Llama via Groq (extra setup).

### D2. Structured JSON output instead of free-form text
Decision: Force model to return strict JSON with `response_mime_type="application/json"`.
Reason: Eliminates regex parsing, guarantees all four keys present, makes evaluation deterministic.
Trade-off: Slightly higher token cost due to schema instruction.

### D3. Six fixed intent classes
Decision: Restrict Intent to exactly 6 values: Software_Update, Hardware_Issue, Apple_ID_Security, App_Store_Purchases, General_Query, Other.
Reason: Matches a plausible Apple triage taxonomy; keeps classification learnable from a small dataset.
Trade-off: Forces some tweets into "closest fit" rather than accurate sub-labels.

### D4. Manual annotation of 200-row golden dataset
Decision: Manually label 200 tweets rather than rely on synthetic labels.
Reason: Real labels expose model weaknesses more honestly than self-generated labels.
Trade-off: Single-annotator bias; no inter-annotator agreement measured.

### D5. Multi-model fallback chain with random rotation
Decision: Maintain a fallback list [3.7-flash, 3.8-flash, 3.5-flash-lite, 3.6-flash] and shuffle per call.
Reason: Free-tier quota is per-model; rotation avoids a single model's quota exhausting mid-run. Fixes 429 and 503 errors automatically.
Trade-off: Slight inconsistency in style across models — acceptable because output schema is enforced.

### D6. Two-pass evaluation with retry
Decision: After Pass 1, retry all failed rows in Pass 2 after a 30s cooldown.
Reason: Network errors (WinError 10013, getaddrinfo failed, connection forcibly closed) are transient.
Result: 5/5 failed rows recovered in Pass 2, achieving 0 net errors.
Trade-off: Longer total runtime.

### D7. 4-second sleep between calls
Decision: Sleep 4s between every API call.
Reason: Free-tier Gemini rate limit is 15 RPM; 4s sleep keeps us comfortably under.
Trade-off: Full evaluation takes ~21 min instead of ~5 min.

### D8. Iteration 1 prompt (baseline) → Iteration 2 (few-shot)
Decision: Add strict enum enforcement + 5 few-shot examples + decision rules to the system prompt.
Reason: Iteration 1 achieved 65% intent accuracy with Other class collapsing to 12.2%.
Result: 65% → 85% intent accuracy, 85% → 88.5% escalation accuracy.
Lesson: Prompt engineering gave +20 pts without any model or dataset change.

### D9. Case-insensitive comparison in evaluation
Decision: Compare intents after .lower().
Reason: Model occasionally returns software_update instead of Software_Update — semantically identical.
Trade-off: Masks potential formatting drift; acceptable for current scope.

### D10. Persist results as both JSON and CSV
Decision: Save metrics.json (for programmatic use) and detailed_results.csv (for human inspection).
Reason: JSON gives a clean summary; CSV enables per-row debugging and confusion-matrix analysis.

### D11. Not use .env values in git
Decision: .env is in .gitignore; only .env.example committed.
Reason: Prevents accidental API-key leak to public GitHub.
Verified: git status after git add . shows no .env tracked.

### D12. Do not re-tune after achieving 85%
Decision: Stop iterating at 85% intent / 88.5% escalation.
Reason: Diminishing returns; remaining errors are label ambiguity, not model failure. Further gains require dataset expansion or inter-annotator agreement study — out of scope.