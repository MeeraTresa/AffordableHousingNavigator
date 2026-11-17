---
description: M10 — Run the batch Equity Audit (Data lane)
---

# M10 · Run the batch Equity Audit

Follow AGENTS.md. Spec: docs/IMPLEMENTATION.md (Part B sections referenced below).

Implement sql/05_equity_audit.sql and scripts/run_equity_audit.py per Part B §12.2. Run it.
Write docs/equity_audit_results.md with the A/B/C table, the filled-in deck sentence (N tracts, M households, X% no-vehicle), and a one-paragraph interpretation.
Never use audit_* anywhere except these two files and agent/navigator/equity.py.

## Done when
docs/equity_audit_results.md exists with real numbers from the query output.

## Human checkpoint
Story lead copies the real numbers into the deck — no rounding beyond what the query returns.

When finished, produce a walkthrough artifact summarizing what changed, then commit on the current lane branch with a message starting "M10:".
