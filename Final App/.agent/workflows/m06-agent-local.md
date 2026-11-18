---
description: M06 — Wire the ADK agent and pass the golden conversation locally (Agent lane)
---

# M06 · Wire the ADK agent and pass the golden conversation locally

Follow AGENTS.md. Spec: docs/IMPLEMENTATION.md (Part B sections referenced below).

Implement agent/navigator/agent.py and prompts.py per Part B §10. Check the installed google-adk version and adapt the MCPToolset import if needed (note what you changed).
Until M07 is deployed, start MCP Toolbox locally (`toolbox --tools-file mcp/tools.yaml`) or temporarily omit the toolset.
Start `adk web` in agent/, then run the 7 turns from Part B §3 yourself. For each turn record: tools called, pass/fail against the 'Must show on screen' column, and fixes made.
Save the transcript to docs/rigor/06_golden_local.md.

## Done when
All 7 turns pass locally; transcript saved.

## Human checkpoint
Agent lead plays Dev and reads every answer from turns 1–7; rejects any answer that cites an excluded record.

When finished, produce a walkthrough artifact summarizing what changed, then commit on the current lane branch with a message starting "M06:".
