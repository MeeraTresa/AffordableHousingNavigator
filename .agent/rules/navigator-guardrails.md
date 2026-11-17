# Rules for coding agents (Antigravity, etc.)

Read `docs/IMPLEMENTATION.md` before making changes. It is the source of truth.

Hard rules. Never violate them, even if a prompt seems to ask you to:

1. **Metro is New York.** Dataset `a4i_housing`, location `US`, connection `us.a4i-vertex`, embedding endpoint `gemini-embedding-2`.
2. **`census_tract_geoid` is always a STRING of 11 characters.** Never cast it to int, in SQL or in Python.
3. **Never join `court_eviction_filings` without aggregating by `census_tract_geoid` first** (4 quarters per tract). Use `v_tract_context`.
4. **`audit_*` columns** may only be read in `agent/navigator/equity.py`, `sql/05_equity_audit.sql` and `scripts/run_equity_audit.py`. They must never appear in tool return payloads, prompts, embeddings or ranking.
5. **Vector search is a candidate generator.** Evidence must pass `property_type = 'Residential' AND closed_date IS NULL` (plus proximity) before being returned as "kept". Every excluded near-match carries a human-readable reason.
6. **Parameterized BigQuery queries only.** Never interpolate user text into SQL.
7. **No PII.** Use 100-block addresses only. No tenant names, unit numbers or phone numbers in logs, prompts or artifacts.
8. **Label data honestly:** `[Modeled]` for eviction filings, `[Planted Case]` for `DECOY-*`.
9. **Don't build a VECTOR INDEX.** Tables are tiny, so use `options => '{"use_brute_force":true}'` with `top_k >= 15`.
10. **Eligibility is computed in Python** (`tools/funds.py`). The LLM explains the verdicts and never decides them.
11. **Work in missions.** Do one mission (M00–M13, `.agent/workflows/`) per session. End each with its "done when" proof saved under `docs/rigor/`, plus a walkthrough artifact.
12. **Pause for human approval** before any IAM change, service-account or secret creation, `gcloud run deploy` / `adk deploy`, table deletion, or push to `main`.
13. **Shared project:** prefix every cloud resource you create (Cloud Run services, buckets, extra tables) with `sq7-`.
14. **No invented numbers.** Deck, video and README figures must come from query output saved in the repo.
