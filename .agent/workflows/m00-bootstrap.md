---
description: M00 — Bootstrap the workspace (Lead lane)
---

# M00 · Bootstrap the workspace

Follow AGENTS.md. Spec: docs/IMPLEMENTATION.md (Part B sections referenced below).

Read AGENTS.md and docs/IMPLEMENTATION.md end to end. Then:
1. Confirm you can see the guardrails in .agent/rules/ and the workflows in .agent/workflows/. List them.
2. Run `gcloud config get-value project` and `bq ls` and tell me the project id and whether dataset a4i_housing exists.
3. Create the empty skeleton from Part B §5 (folders and placeholder files only, no logic), plus agent/.env.example from §10.3.
4. Produce an implementation-plan artifact that maps missions M01–M13 to files you will touch.
Do not deploy anything or change IAM in this mission.

## Done when
`tree -L 3 agent mcp sql` matches Part B §5; plan artifact is posted to the team channel.

## Human checkpoint
Lead reads the plan Antigravity produces and confirms metro = New York, track = intake + funds.

When finished, produce a walkthrough artifact summarizing what changed, then commit on the current lane branch with a message starting "M00:".
