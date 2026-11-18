---
description: M03 — Build embeddings and fan-out-safe views (Data lane)
---

# M03 · Build embeddings and fan-out-safe views

Follow AGENTS.md. Spec: docs/IMPLEMENTATION.md (Part B sections referenced below).

Create and run, in order: sql/02_embed_complaints.sql, sql/03_embed_rules.sql, sql/04_views.sql (Part B §7.1–7.3).
After each file run its sanity checks and report row counts.
Then run the Part B §7.4 search with queries ['no heat radiators cold', 'black mold around tub', 'water leak through bathroom wall'], block_hint '1000 block st nicholas', and show the top 10 RAW rows including DECOY-* rows.
Save outputs to docs/rigor/03_embeddings.txt. Do not create a VECTOR INDEX.

## Done when
complaints_embedded = 174 rows; v_tract_context = 168 rows with quarters_aggregated = 4 everywhere; raw search shows at least one DECOY-* in top 10.

## Human checkpoint
Data lead eyeballs one VECTOR_SEARCH result list and confirms decoys appear in the RAW results (that's the point).

When finished, produce a walkthrough artifact summarizing what changed, then commit on the current lane branch with a message starting "M03:".
