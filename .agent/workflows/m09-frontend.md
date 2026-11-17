---
description: M09 — Build the Intake Desk UI (mock first, then live) (Front end lane)
---

# M09 · Build the Intake Desk UI (mock first, then live)

Follow AGENTS.md. Spec: docs/IMPLEMENTATION.md (Part B sections referenced below).

Build frontend/ per Part B §13.2 as index.html + app.js + styles.css, no build step.
Phase 1 (now): create frontend/mock/*.json replaying the Part B §3 conversation from the tool output shapes in §8, and make the UI work on ?mock=1.
Phase 2 (after M08): connect to the deployed ADK server (/run_sse), update the Case File panel from functionResponse events per tool name.
Use the browser to open the page, run the mock conversation end to end, and attach screenshots at 1280×720 to a walkthrough artifact. Serve it from the agent's Cloud Run service or a static bucket — ask me which.

## Done when
Mock and live modes both complete turns 1–7 in the browser; screenshots in docs/rigor/09_ui/.

## Human checkpoint
Front-end lead checks it at 1280×720 (video size) and approves the look.

When finished, produce a walkthrough artifact summarizing what changed, then commit on the current lane branch with a message starting "M09:".
