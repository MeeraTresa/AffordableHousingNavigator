---
description: M05 — Build statutes, funds, brief and equity code (Agent lane)
---

# M05 · Build statutes, funds, brief and equity code

Follow AGENTS.md. Spec: docs/IMPLEMENTATION.md (Part B sections referenced below).

Implement tools/statutes.py, tools/funds.py, tools/brief.py and equity.py per Part B §8.5–8.7 and §12.1.
render_brief_markdown must produce exactly the Part B §11 structure.
Write tests/test_eligibility.py with the Marisol fixture from §8.6 (expect 4x ELIGIBLE; with evidence=[] expect BUL-NY-02 and BUL-NY-04 INELIGIBLE), tests/test_no_audit_leak.py, tests/test_geoid.py, and a snapshot test for the brief.
Run all tests. Finish with a walkthrough artifact that includes `grep -rn audit_ agent/` output.

## Done when
All tests in agent/tests pass; grep shows audit_ only in equity.py.

## Human checkpoint
Agent lead confirms equity.py is the ONLY place audit_* is read (grep proof in the walkthrough).

When finished, produce a walkthrough artifact summarizing what changed, then commit on the current lane branch with a message starting "M05:".
