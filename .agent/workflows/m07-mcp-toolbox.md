---
description: M07 — Deploy MCP Toolbox to Cloud Run (Agent lane)
---

# M07 · Deploy MCP Toolbox to Cloud Run

Follow AGENTS.md. Spec: docs/IMPLEMENTATION.md (Part B sections referenced below).

Create mcp/tools.yaml and mcp/deploy_toolbox.sh per Part B §9. Show me the script and the roles it grants, wait for my approval, then run it.
Use service name `sq7-mcp-toolbox` (shared project: avoid name collisions). Keep --min-instances=1.
Smoke test: call get_tract_context with census_tract_geoid '36061024500' through the deployed server and show the JSON.

## Done when
Toolbox URL returns tract 36061024500 with severe_rent_burden_pct ≈ 32.8.

## Human checkpoint
A human approves service-account creation and the IAM roles before Antigravity runs them.

When finished, produce a walkthrough artifact summarizing what changed, then commit on the current lane branch with a message starting "M07:".
