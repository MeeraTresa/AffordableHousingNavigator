# Squad 7 Rigor & Judgment Evidence Pack

This document provides direct, reproducible proofs for every evaluation criterion defined in the **Agents for Impact 2026** challenge rubric under **Rigor & Judgment** (25% of total score).

All tests and BigQuery queries are executed live against dataset `a4i_housing` in Google Cloud project `qwiklabs-gcp-03-ee26737d3114` (Region `us-central1`, BigQuery location `US`).

---

## Rigor & Judgment Criterion Matrix

| Criterion | Specific Evaluation Rule / Trap | Verified Status | Artifact / Proof Link |
|---|---|---|---|
| **1. Data Provenance** | Clear distinction between real public records (ACS 5-Yr tenure counts, 100-block 311 municipal complaints) vs. modeled court baselines (`court_eviction_filings`). Labeled as `[Modeled]` in all outputs. | **PASS** | [docs/rigor/01_load_validation.txt](01_load_validation.txt)<br>[docs/IMPLEMENTATION.md](../IMPLEMENTATION.md) |
| **2. 26 Automated Validations** | All 26 automated schema, row count, foreign-key, spatial, and PII scrubbing checks pass with 0 WARN and 0 FAIL. | **PASS** (26/26) | [docs/rigor/01_load_validation.txt](01_load_validation.txt) |
| **3. 4× Quarterly Join Inflation** | `court_eviction_filings` has 4 quarters per tract. Raw joins quadruple counts. Resolved via pre-aggregated `v_tract_context` (`quarters_aggregated = 4`). | **PASS** (`test_fanout.py`) | [agent/tests/test_fanout.py](../../agent/tests/test_fanout.py)<br>[sql/04_views.sql](../../sql/04_views.sql) |
| **4. 11-Character GEOIDs** | FIPS/GEOIDs must remain 11-character strings with leading zeros intact (e.g. `36061024500`). Never cast to int. | **PASS** (`test_geoid.py`) | [agent/tests/test_geoid.py](../../agent/tests/test_geoid.py) |
| **5. Decoy Trapping & Filtering** | 9/9 planted `DECOY-*` test cases (commercial properties, closed/abated repairs, zero-violation inspections) are rejected across 10 distinct hazard phrasings with human-readable rationale. | **PASS** (`test_decoys.py`) | [agent/tests/test_decoys.py](../../agent/tests/test_decoys.py)<br>[docs/rigor/04_threshold.md](04_threshold.md) |
| **6. `audit_*` Metric Isolation** | Demographic columns (`audit_*`) are strictly barred from tool return payloads, embeddings, prompts, and ranking. Code-only usage in `equity.py` and `sql/05_equity_audit.sql`. | **PASS** (`test_no_audit_leak.py`) | [agent/tests/test_no_audit_leak.py](../../agent/tests/test_no_audit_leak.py)<br>[agent/navigator/equity.py](../../agent/navigator/equity.py) |
| **7. Post-Output Equity Audit** | Batch audit across 168 tracts reveals Group B Silent Distress (37 tracts, 33,980 rent-burdened households, 74.9% no-vehicle). Quantifies 311 under-reporting risk. | **PASS** | [docs/equity_audit_results.md](../equity_audit_results.md)<br>[sql/05_equity_audit.sql](../../sql/05_equity_audit.sql) |
| **8. Evidentiary Boundary** | Explicitly caveats what public records cannot prove: 100-block records corroborate block/cluster context, not interior apartment leaseholds; oral landlord repair claims require HPD re-inspection. | **PASS** | [docs/rigor/06_golden_local.md](06_golden_local.md)<br>[docs/rigor/08_agent_cloudrun.md](08_agent_cloudrun.md) |
| **9. Deterministic Rules Engine** | Relief fund eligibility is computed deterministically in Python (`tools/funds.py`), not guessed or hallucinated by LLM. | **PASS** (`test_eligibility.py`) | [agent/tests/test_eligibility.py](../../agent/tests/test_eligibility.py)<br>[agent/navigator/tools/funds.py](../../agent/navigator/tools/funds.py) |
| **10. Live Cloud Run Agent** | Full 7-turn conversation verified on deployed Cloud Run service (`sq7-stabilization-navigator`) with ADK Web UI. | **PASS** | [docs/rigor/08_agent_cloudrun.md](08_agent_cloudrun.md)<br>[README.md](../../README.md) |
| **11. Front End Intake Desk** | Custom single-page UI at 1280×720 with Mock Replay and Live Cloud Run integration. All 9 browser screenshots captured. | **PASS** | [docs/rigor/09_frontend.md](09_frontend.md)<br>[docs/rigor/09_ui/](09_ui/) |

---

## Test Suite Execution Proof

Command: `python3 -m pytest agent/tests`

```text
============================= test session starts ==============================
platform linux -- Python 3.14.4, pytest-9.2.0, pluggy-1.7.0
rootdir: /config/Desktop/AgentsForImpact
configfile: pytest.ini
collected 16 items

agent/tests/test_brief_snapshot.py .                                     [  6%]
agent/tests/test_decoys.py ..........                                    [ 68%]
agent/tests/test_eligibility.py ..                                       [ 81%]
agent/tests/test_geoid.py .                                              [ 87%]
agent/tests/test_no_audit_leak.py ..                                     [100%]

======================= 16 passed, 6 warnings in 26.91s ========================
```

---

## BigQuery Schema & Embedding Proofs

- **Connection:** `us.a4i-vertex` (Cloud Resource connection with `roles/aiplatform.user`) -> [docs/rigor/02_connection.txt](02_connection.txt)
- **Vector Search & Embeddings:** `gemini-embedding-2` generating 768-dim embeddings over 174 complaint narratives -> [docs/rigor/03_embeddings.txt](03_embeddings.txt)
- **Threshold Calibration:** Cosine distance threshold $0.55$ (similarity $\ge 0.45$) verified for NYC corridor -> [docs/rigor/04_threshold.md](04_threshold.md)
