---
description: M11 — Assemble the rigor evidence pack (Data lane)
---

# M11 · Assemble the rigor evidence pack

Follow AGENTS.md. Spec: docs/IMPLEMENTATION.md (Part B sections referenced below).

Create docs/rigor/README.md: one row per Rigor & judgment criterion in the challenge README (real vs modeled, validation, 4x join, GEOIDs, decoys, audit_* exclusion, equity audit, evidentiary limits) with a link to the proof file in docs/rigor/.
Re-run all tests (pytest agent/tests) and the validation SQL against the current tables and refresh the outputs. Flag anything that regressed.

## Done when
docs/rigor/README.md table has no empty proof cells; all tests pass.

## Human checkpoint
Lead confirms every Rigor & judgment bullet in the README rubric has a file behind it.

When finished, produce a walkthrough artifact summarizing what changed, then commit on the current lane branch with a message starting "M11:".
