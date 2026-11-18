---
description: M08 — Deploy the agent to Cloud Run (Agent lane)
---

# M08 · Deploy the agent to Cloud Run

Follow AGENTS.md. Spec: docs/IMPLEMENTATION.md (Part B sections referenced below).

Deploy with `adk deploy cloud_run` per Part B §13.1 using service name `sq7-stabilization-navigator`, --with_ui, region us-central1.
Show me the command and the IAM roles you will grant the agent's service account (bigquery.dataViewer, bigquery.jobUser, bigquery.connectionUser, aiplatform.user, run.invoker on the toolbox) and wait for approval.
Set env vars TOOLBOX_URL, NAVIGATOR_MODEL, A4I_DATASET on the service. Then curl-test: create a session and send turn 1 of Part B §3. Write the URL into README.md under a new 'Live demo' heading.

## Done when
Deployed URL answers turn 1 with kept + excluded evidence; URL committed to README.

## Human checkpoint
A human approves the deploy command and IAM grants; then opens the URL and runs turn 1 themselves.

When finished, produce a walkthrough artifact summarizing what changed, then commit on the current lane branch with a message starting "M08:".
