---
description: M01 — Load New York data and prove it's valid (Data lane)
---

# M01 · Load New York data and prove it's valid

Follow AGENTS.md. Spec: docs/IMPLEMENTATION.md (Part B sections referenced below).

Load the New York metro into BigQuery dataset a4i_housing:
1. Run `bash scripts/load.sh new-york` from the repo root and stream the output.
2. Run the validation checks equivalent to notebook Section 12 against the loaded tables (write them as sql/00_validate.sql if you need a file). Report PASS/WARN/FAIL per check.
3. Save the full output to docs/rigor/01_load_validation.txt.
Stop and show me any FAIL. Never cast census_tract_geoid to a number.

## Done when
docs/rigor/01_load_validation.txt shows 174 complaints, 168 tracts, 672 filing rows, 9 decoys, 0 FAIL.

## Human checkpoint
Data lead checks the validation summary shows 0 FAIL before anyone moves on.

When finished, produce a walkthrough artifact summarizing what changed, then commit on the current lane branch with a message starting "M01:".
