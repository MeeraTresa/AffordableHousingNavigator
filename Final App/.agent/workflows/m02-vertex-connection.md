---
description: M02 — Create the Vertex AI connection (Data lane)
---

# M02 · Create the Vertex AI connection

Follow AGENTS.md. Spec: docs/IMPLEMENTATION.md (Part B sections referenced below).

Implement sql/01_connection.sh exactly as Part B §6.1 and run it.
Before running the `gcloud projects add-iam-policy-binding` line, STOP and show me the exact command and service account for approval.
After it succeeds, wait 60s, then run a one-row smoke test:
SELECT AI.EMBED('test', connection_id => 'us.a4i-vertex', endpoint => 'gemini-embedding-2').status
and confirm the status is an empty string.

## Done when
Smoke query returns status = '' ; output appended to docs/rigor/02_connection.txt.

## Human checkpoint
A human approves the IAM binding command before Antigravity runs it (Antigravity must pause and ask).

When finished, produce a walkthrough artifact summarizing what changed, then commit on the current lane branch with a message starting "M02:".
