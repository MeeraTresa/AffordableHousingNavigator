---
description: M04 — Build the evidence search tool and decoy tests (Agent lane)
---

# M04 · Build the evidence search tool and decoy tests

Follow AGENTS.md. Spec: docs/IMPLEMENTATION.md (Part B sections referenced below).

Implement agent/navigator/config.py, bq.py, tools/case_file.py, tools/evidence.py and tools/search.sql per Part B §8.1–8.4.
Use parameterized BigQuery queries only. Then write tests/test_decoys.py (Part B §13.3): 10 hazard phrasings, assert no DECOY-* id is ever in `kept`, and every DECOY-* in the raw top-20 has an `excluded_because`.
Run the tests against the live dataset and show results. Tune MIN_SIMILARITY only if real NYC hazard records are being dropped; record the final value and why in docs/rigor/04_threshold.md.

## Done when
`pytest agent/tests/test_decoys.py` passes against live BigQuery.

## Human checkpoint
Agent lead reviews the diff of evidence.py (/diff) with special attention to the exclusion rules.

When finished, produce a walkthrough artifact summarizing what changed, then commit on the current lane branch with a message starting "M04:".
