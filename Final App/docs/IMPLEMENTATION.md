# Stabilization Navigator — Antigravity Build Playbook

**Agents for Impact 2026 · Challenge 02 · Affordable Housing Stability · Squad 7**

> **Operating model: Antigravity builds everything. Humans decide, approve and verify.**
> No teammate writes production code by hand. Each lane drives its own Antigravity session through numbered **missions** (M00–M13). Each mission is a ready-made prompt, also saved as a slash-command workflow in `.agent/workflows/`. People do three things: pick the mission, approve the risky steps (IAM, deploys), and check the "done when" proof.
>
> **Decisions locked:** Metro = **New York** · Track = **⚖️ Today at intake** + **🛟 relief-fund matching** · Constraint = **BigQuery Vector Search** (`AI.EMBED` + `VECTOR_SEARCH`, then filter closed / commercial / "no violation found" decoys).

---

## Contents

**Part A — Antigravity playbook (start here)**
- [A0. Setup: get every lane into Antigravity in 10 minutes](#a0-setup)
- [A1. How we drive Antigravity](#a1-how-we-drive-antigravity)
- [A2. Mission map](#a2-mission-map)
- [A3. Mission cards (prompts, proof, checkpoints)](#a3-mission-cards)
- [A4. What humans must approve (and what Antigravity must never do)](#a4-what-humans-must-approve)
- [A5. When Antigravity gets stuck](#a5-when-antigravity-gets-stuck)
- [A6. Timeline by lane](#a6-timeline-by-lane)

**Part B — Technical spec (what Antigravity implements)**
1. [Why New York](#1-why-new-york) · 2. [The story: Marisol's Monday](#2-the-story-marisols-monday) · 3. [Golden conversation](#3-the-demo-conversation-golden-path) · 4. [Architecture](#4-architecture) · 5. [Repo layout](#5-repository-layout) · 6. [Data load](#6-phase-0-load-data-and-build-embeddings) · 7. [SQL](#7-bigquery-sql-artifacts) · 8. [Custom tools](#8-custom-tools-python) · 9. [MCP Toolbox](#9-managed-mcp-mcp-toolbox-for-databases) · 10. [ADK agent](#10-the-adk-agent-and-system-prompt) · 11. [Brief contract](#11-tenant-stabilization-brief-output-contract) · 12. [Equity audit](#12-equity-audit-post-output-only) · 13. [Deploy, UI, tests](#13-deploy-front-end-tests) · 16. [Deck & video](#16-deck-and-3-minute-video-script) · 17. [Limitations](#17-limitations-we-state-out-loud)

---

# Part A — Antigravity playbook

## A0. Setup

Do this once per person. It takes about 10 minutes, and every lane does it in parallel.

1. **Open Antigravity.** Either click the **Antigravity IDE** button in the Google Skills lab environment, or open Cloud Shell (`>_` in the console, attached to the team project) and run `agy`.
2. **Clone the team repo and branch for your lane**:
   ```bash
   git clone https://github.com/<team-repo>.git && cd <repo>
   git checkout -b data      # or agent, frontend, story
   ```
3. **Open the repo as the Antigravity workspace.** In the IDE, use *Open Folder*. With the CLI, run `agy` from the repo root.
4. **Check that the guardrails loaded.** Ask Antigravity: *"What are the rules in this workspace?"* It should recite `AGENTS.md` (also mirrored in `.agent/rules/navigator-guardrails.md` and pointed to by `GEMINI.md`). If it doesn't, start every session with: *"Read AGENTS.md and docs/IMPLEMENTATION.md first."*
5. **Check that the workflows are visible.** Type `/` and look for `/m00-bootstrap` … `/m13-rehearsal`. If your Antigravity version doesn't pick up `.agent/workflows/`, paste the prompt from the mission card in A3 instead. The text is identical.
6. **Set autonomy.** Allow file edits and read-only commands (`bq ls`, `bq query` SELECTs, `pytest`, `git status`). Require approval for `gcloud … iam`, `gcloud run deploy`, `adk deploy`, `bq rm`, `git push --force`, and anything with `delete`. (CLI: `/permissions`; review pending edits with `/diff`.)

## A1. How we drive Antigravity

| Practice | Why |
|---|---|
| **One mission per conversation.** Start a fresh agent session per mission and name it after the mission (e.g. "M04 evidence tool"). | Keeps context small and the history readable for judges |
| **Plan first for big missions** (M04–M09). Ask for an implementation-plan artifact, review it, then let it execute. | Cheap to fix a plan, expensive to fix a deploy |
| **Make it prove "done".** Every mission ends with a command or test whose output goes into `docs/rigor/`. | That folder *is* our Rigor & judgment score (25 pts) |
| **Review diffs, don't rewrite.** If code is wrong, reply with what's wrong and let Antigravity fix it. | Keeps "Antigravity did everything" true and fast |
| **Run lanes in parallel** with separate sessions and separate branches. Merge to `main` when a mission's "done when" is green. | Four lanes, one shared GCP project, no collisions |
| **Paste errors verbatim.** Traceback in, fix out (see A5). | Faster than debugging by hand |
| **Use the browser agent for UI and rehearsal** (M09, M13). Let Antigravity click through the deployed app and capture screenshots. | It's the same path the video records |
| **Prefix shared cloud names with `sq7-`.** Services, buckets and tables beyond the five starter tables. | One project per team, and overwriting is easy |

**Parallel sessions at a glance:**

```
Data lane      M01 → M02 → M03 ──────────→ M10 → M11
Agent lane          M04 (after M03) → M05 → M06 → M07 → M08
Front end      M09 phase 1 (mock) ─────────────→ M09 phase 2 (live, after M08)
Story          M12 (starts at 0:30, finalizes after M10) ───────────→ M13
Lead           M00, approvals, merges ─────────────────────────────→ M13
```

## A2. Mission map

| # | Mission | Lane | Start | Workflow |
|---|---|---|---|---|
| **M00** | Bootstrap the workspace | Lead | 0:00 | `/m00-bootstrap` |
| **M01** | Load New York data and prove it's valid | Data | 0:15 | `/m01-load-data` |
| **M02** | Create the Vertex AI connection | Data | 0:25 | `/m02-vertex-connection` |
| **M03** | Build embeddings and fan-out-safe views | Data | 0:35 | `/m03-embeddings-views` |
| **M04** | Build the evidence search tool and decoy tests | Agent | 0:45 | `/m04-evidence-tool` |
| **M05** | Build statutes, funds, brief and equity code | Agent | 1:15 | `/m05-rules-tools` |
| **M06** | Wire the ADK agent and pass the golden conversation locally | Agent | 1:45 | `/m06-agent-local` |
| **M07** | Deploy MCP Toolbox to Cloud Run | Agent | 2:00 | `/m07-mcp-toolbox` |
| **M08** | Deploy the agent to Cloud Run | Agent | 2:15 | `/m08-agent-deploy` |
| **M09** | Build the Intake Desk UI (mock first, then live) | Front end | 1:00 → 2:45 | `/m09-frontend` |
| **M10** | Run the batch Equity Audit | Data | 1:45 | `/m10-equity-audit` |
| **M11** | Assemble the rigor evidence pack | Data | 2:45 | `/m11-rigor-pack` |
| **M12** | Write the deck, video script and submission README | Story | 0:30 → 3:30 | `/m12-story` |
| **M13** | Dress rehearsal on the deployed app | All | 3:30 | `/m13-rehearsal` |

## A3. Mission cards

Each card = the exact prompt (identical to the workflow file), the proof that it's done, and the moment a human must look.

### M00 · Bootstrap the workspace
**Lane:** Lead · **Start:** 0:00 · **Run:** `/m00-bootstrap` (or paste the prompt)

```text
Read AGENTS.md and docs/IMPLEMENTATION.md end to end. Then:
1. Confirm you can see the guardrails in .agent/rules/ and the workflows in .agent/workflows/. List them.
2. Run `gcloud config get-value project` and `bq ls` and tell me the project id and whether dataset a4i_housing exists.
3. Create the empty skeleton from Part B §5 (folders and placeholder files only, no logic), plus agent/.env.example from §10.3.
4. Produce an implementation-plan artifact that maps missions M01–M13 to files you will touch.
Do not deploy anything or change IAM in this mission.
```

- **Done when:** `tree -L 3 agent mcp sql` matches Part B §5; plan artifact is posted to the team channel.
- **Human checkpoint:** Lead reads the plan Antigravity produces and confirms metro = New York, track = intake + funds.

### M01 · Load New York data and prove it's valid
**Lane:** Data · **Start:** 0:15 · **Run:** `/m01-load-data` (or paste the prompt)

```text
Load the New York metro into BigQuery dataset a4i_housing:
1. Run `bash scripts/load.sh new-york` from the repo root and stream the output.
2. Run the validation checks equivalent to notebook Section 12 against the loaded tables (write them as sql/00_validate.sql if you need a file). Report PASS/WARN/FAIL per check.
3. Save the full output to docs/rigor/01_load_validation.txt.
Stop and show me any FAIL. Never cast census_tract_geoid to a number.
```

- **Done when:** docs/rigor/01_load_validation.txt shows 174 complaints, 168 tracts, 672 filing rows, 9 decoys, 0 FAIL.
- **Human checkpoint:** Data lead checks the validation summary shows 0 FAIL before anyone moves on.

### M02 · Create the Vertex AI connection
**Lane:** Data · **Start:** 0:25 · **Run:** `/m02-vertex-connection` (or paste the prompt)

```text
Implement sql/01_connection.sh exactly as Part B §6.1 and run it.
Before running the `gcloud projects add-iam-policy-binding` line, STOP and show me the exact command and service account for approval.
After it succeeds, wait 60s, then run a one-row smoke test:
SELECT AI.EMBED('test', connection_id => 'us.a4i-vertex', endpoint => 'gemini-embedding-2').status
and confirm the status is an empty string.
```

- **Done when:** Smoke query returns status = '' ; output appended to docs/rigor/02_connection.txt.
- **Human checkpoint:** A human approves the IAM binding command before Antigravity runs it (Antigravity must pause and ask).

### M03 · Build embeddings and fan-out-safe views
**Lane:** Data · **Start:** 0:35 · **Run:** `/m03-embeddings-views` (or paste the prompt)

```text
Create and run, in order: sql/02_embed_complaints.sql, sql/03_embed_rules.sql, sql/04_views.sql (Part B §7.1–7.3).
After each file run its sanity checks and report row counts.
Then run the Part B §7.4 search with queries ['no heat radiators cold', 'black mold around tub', 'water leak through bathroom wall'], block_hint '1000 block st nicholas', and show the top 10 RAW rows including DECOY-* rows.
Save outputs to docs/rigor/03_embeddings.txt. Do not create a VECTOR INDEX.
```

- **Done when:** complaints_embedded = 174 rows; v_tract_context = 168 rows with quarters_aggregated = 4 everywhere; raw search shows at least one DECOY-* in top 10.
- **Human checkpoint:** Data lead eyeballs one VECTOR_SEARCH result list and confirms decoys appear in the RAW results (that's the point).

### M04 · Build the evidence search tool and decoy tests
**Lane:** Agent · **Start:** 0:45 · **Run:** `/m04-evidence-tool` (or paste the prompt)

```text
Implement agent/navigator/config.py, bq.py, tools/case_file.py, tools/evidence.py and tools/search.sql per Part B §8.1–8.4.
Use parameterized BigQuery queries only. Then write tests/test_decoys.py (Part B §13.3): 10 hazard phrasings, assert no DECOY-* id is ever in `kept`, and every DECOY-* in the raw top-20 has an `excluded_because`.
Run the tests against the live dataset and show results. Tune MIN_SIMILARITY only if real NYC hazard records are being dropped; record the final value and why in docs/rigor/04_threshold.md.
```

- **Done when:** `pytest agent/tests/test_decoys.py` passes against live BigQuery.
- **Human checkpoint:** Agent lead reviews the diff of evidence.py (/diff) with special attention to the exclusion rules.

### M05 · Build statutes, funds, brief and equity code
**Lane:** Agent · **Start:** 1:15 · **Run:** `/m05-rules-tools` (or paste the prompt)

```text
Implement tools/statutes.py, tools/funds.py, tools/brief.py and equity.py per Part B §8.5–8.7 and §12.1.
render_brief_markdown must produce exactly the Part B §11 structure.
Write tests/test_eligibility.py with the Marisol fixture from §8.6 (expect 4x ELIGIBLE; with evidence=[] expect BUL-NY-02 and BUL-NY-04 INELIGIBLE), tests/test_no_audit_leak.py, tests/test_geoid.py, and a snapshot test for the brief.
Run all tests. Finish with a walkthrough artifact that includes `grep -rn audit_ agent/` output.
```

- **Done when:** All tests in agent/tests pass; grep shows audit_ only in equity.py.
- **Human checkpoint:** Agent lead confirms equity.py is the ONLY place audit_* is read (grep proof in the walkthrough).

### M06 · Wire the ADK agent and pass the golden conversation locally
**Lane:** Agent · **Start:** 1:45 · **Run:** `/m06-agent-local` (or paste the prompt)

```text
Implement agent/navigator/agent.py and prompts.py per Part B §10. Check the installed google-adk version and adapt the MCPToolset import if needed (note what you changed).
Until M07 is deployed, start MCP Toolbox locally (`toolbox --tools-file mcp/tools.yaml`) or temporarily omit the toolset.
Start `adk web` in agent/, then run the 7 turns from Part B §3 yourself. For each turn record: tools called, pass/fail against the 'Must show on screen' column, and fixes made.
Save the transcript to docs/rigor/06_golden_local.md.
```

- **Done when:** All 7 turns pass locally; transcript saved.
- **Human checkpoint:** Agent lead plays Dev and reads every answer from turns 1–7; rejects any answer that cites an excluded record.

### M07 · Deploy MCP Toolbox to Cloud Run
**Lane:** Agent · **Start:** 2:00 · **Run:** `/m07-mcp-toolbox` (or paste the prompt)

```text
Create mcp/tools.yaml and mcp/deploy_toolbox.sh per Part B §9. Show me the script and the roles it grants, wait for my approval, then run it.
Use service name `sq7-mcp-toolbox` (shared project: avoid name collisions). Keep --min-instances=1.
Smoke test: call get_tract_context with census_tract_geoid '36061024500' through the deployed server and show the JSON.
```

- **Done when:** Toolbox URL returns tract 36061024500 with severe_rent_burden_pct ≈ 32.8.
- **Human checkpoint:** A human approves service-account creation and the IAM roles before Antigravity runs them.

### M08 · Deploy the agent to Cloud Run
**Lane:** Agent · **Start:** 2:15 · **Run:** `/m08-agent-deploy` (or paste the prompt)

```text
Deploy with `adk deploy cloud_run` per Part B §13.1 using service name `sq7-stabilization-navigator`, --with_ui, region us-central1.
Show me the command and the IAM roles you will grant the agent's service account (bigquery.dataViewer, bigquery.jobUser, bigquery.connectionUser, aiplatform.user, run.invoker on the toolbox) and wait for approval.
Set env vars TOOLBOX_URL, NAVIGATOR_MODEL, A4I_DATASET on the service. Then curl-test: create a session and send turn 1 of Part B §3. Write the URL into README.md under a new 'Live demo' heading.
```

- **Done when:** Deployed URL answers turn 1 with kept + excluded evidence; URL committed to README.
- **Human checkpoint:** A human approves the deploy command and IAM grants; then opens the URL and runs turn 1 themselves.

### M09 · Build the Intake Desk UI (mock first, then live)
**Lane:** Front end · **Start:** 1:00 → 2:45 · **Run:** `/m09-frontend` (or paste the prompt)

```text
Build frontend/ per Part B §13.2 as index.html + app.js + styles.css, no build step.
Phase 1 (now): create frontend/mock/*.json replaying the Part B §3 conversation from the tool output shapes in §8, and make the UI work on ?mock=1.
Phase 2 (after M08): connect to the deployed ADK server (/run_sse), update the Case File panel from functionResponse events per tool name.
Use the browser to open the page, run the mock conversation end to end, and attach screenshots at 1280×720 to a walkthrough artifact. Serve it from the agent's Cloud Run service or a static bucket — ask me which.
```

- **Done when:** Mock and live modes both complete turns 1–7 in the browser; screenshots in docs/rigor/09_ui/.
- **Human checkpoint:** Front-end lead checks it at 1280×720 (video size) and approves the look.

### M10 · Run the batch Equity Audit
**Lane:** Data · **Start:** 1:45 · **Run:** `/m10-equity-audit` (or paste the prompt)

```text
Implement sql/05_equity_audit.sql and scripts/run_equity_audit.py per Part B §12.2. Run it.
Write docs/equity_audit_results.md with the A/B/C table, the filled-in deck sentence (N tracts, M households, X% no-vehicle), and a one-paragraph interpretation.
Never use audit_* anywhere except these two files and agent/navigator/equity.py.
```

- **Done when:** docs/equity_audit_results.md exists with real numbers from the query output.
- **Human checkpoint:** Story lead copies the real numbers into the deck — no rounding beyond what the query returns.

### M11 · Assemble the rigor evidence pack
**Lane:** Data · **Start:** 2:45 · **Run:** `/m11-rigor-pack` (or paste the prompt)

```text
Create docs/rigor/README.md: one row per Rigor & judgment criterion in the challenge README (real vs modeled, validation, 4x join, GEOIDs, decoys, audit_* exclusion, equity audit, evidentiary limits) with a link to the proof file in docs/rigor/.
Re-run all tests (pytest agent/tests) and the validation SQL against the current tables and refresh the outputs. Flag anything that regressed.
```

- **Done when:** docs/rigor/README.md table has no empty proof cells; all tests pass.
- **Human checkpoint:** Lead confirms every Rigor & judgment bullet in the README rubric has a file behind it.

### M12 · Write the deck, video script and submission README
**Lane:** Story · **Start:** 0:30 → 3:30 · **Run:** `/m12-story` (or paste the prompt)

```text
Using Part B §1, §2, §3, §16, §17 and docs/equity_audit_results.md:
1. docs/deck_outline.md — 10 slides, each with title, 3 bullets, and the visual to use.
2. docs/video_script.md — ≤3:00 voiceover with timestamps, matching the live turns.
3. Update README.md with a 'Squad 7 submission' section at the top: metro, track, live URL, architecture summary, real vs modeled data, how to run locally, limitations.
Use only numbers that appear in the repo docs.
```

- **Done when:** Three files committed; README top section renders on GitHub.
- **Human checkpoint:** Story lead edits for voice; nobody adds a number that isn't in the docs.

### M13 · Dress rehearsal on the deployed app
**Lane:** All · **Start:** 3:30 · **Run:** `/m13-rehearsal` (or paste the prompt)

```text
Using the browser, open the deployed Intake Desk (live mode, not mock) and run the 7 turns from Part B §3 exactly as written in docs/video_script.md.
Time each turn. Flag any turn slower than 20s, any cold start, and any answer missing 'What the record can't prove yet'.
Produce a go/no-go checklist artifact and a submission checklist (repo public, Skills project link, deck, video ≤3:00).
```

- **Done when:** Go/no-go checklist is all green; recording starts.
- **Human checkpoint:** The person recording runs the script once with Antigravity's checklist next to them; then records.

## A4. What humans must approve

**Always approve by a person, never auto-run:**
- Any `gcloud projects add-iam-policy-binding`, service-account creation, or secret creation (M02, M07, M08)
- `gcloud run deploy` / `adk deploy cloud_run` (M07, M08)
- Anything that deletes or replaces BigQuery tables other than via `scripts/load.sh`
- Pushing to `main` and the final submission

**Antigravity must never** (also in `AGENTS.md`):
- Put `audit_*` columns in a tool output, prompt, embedding or ranking
- Cast `census_tract_geoid` to a number, or join raw `court_eviction_filings` without aggregating
- Use `LIKE '%mold%'`-style keyword matching as evidence retrieval
- Commit `.env`, tokens or service-account keys
- Invent numbers for the deck. Every figure must come from a file in the repo.

## A5. When Antigravity gets stuck

Paste the matching prompt:

| Symptom | Prompt |
|---|---|
| Any traceback | *"Here is the full error and the command I ran. Read the files involved, explain the root cause in one sentence, then fix it. Don't change unrelated code."* |
| `AI.EMBED` permission error | *"Check the us.a4i-vertex connection service account has roles/aiplatform.user, wait 60s, and re-run the smoke query from M02."* |
| Empty search results | *"Show the raw VECTOR_SEARCH rows before filtering for these queries. Is top_k ≥ 15? Is the block anchor NULL? Is MIN_SIMILARITY too high?"* |
| Counts 4× too high | *"Find every join to court_eviction_filings and replace it with v_tract_context."* |
| ADK import error | *"Print the installed google-adk version and the available MCP connection param classes, then adapt agent.py."* |
| Cloud Run 403 between services | *"Grant roles/run.invoker on sq7-mcp-toolbox to the agent's service account and send an ID token in the MCP request header."* |
| Slow first response in demo | *"Set --min-instances=1 on both Cloud Run services and warm them with one request."* |
| Antigravity drifts from spec | *"Stop. Re-read docs/IMPLEMENTATION.md Part B §<n> and AGENTS.md, list where your change differs, and correct it."* |

## A6. Timeline by lane

| Time | Lead | Data | Agent | Front end | Story |
|---|---|---|---|---|---|
| 0:00–0:15 | M00 | A0 setup | A0 setup | A0 setup | A0 setup |
| 0:15–0:45 | approvals | M01, M02, M03 | review spec §8 | M09 phase 1 | M12 draft |
| 0:45–1:45 | merges | M10 prep | M04 → M05 | M09 phase 1 | M12 draft |
| 1:45–2:15 | approvals | M10 | M06 | polish mock | M12 numbers |
| 2:15–2:45 | approvals | help deploy | M07 → M08 | M09 phase 2 | rehearse |
| 2:45–3:30 | freeze | M11 | fix failures | polish live | M12 final |
| 3:30–4:00 | M13 | M13 | M13 | M13 | **record** |
| 4:00–4:30 | submit | — | — | — | upload |

**Scope-cut order if late:** M09 phase 2 → use `adk web` and justify it. Then the bulletin embeddings in M03 (keep the rules). Then the M10 batch audit → per-tract note only. **Never cut:** decoy filtering (M04), deployment (M08), the evidentiary boundary.

---

# Part B — Technical spec

> Antigravity implements this; humans use it to check the work. Section numbers are referenced by the mission prompts.

## 1. Why New York

Before choosing a metro we checked what the open residential 311 records actually *say*. We counted open, residential, non-decoy complaints whose narrative mentions heat, boiler, hot water, mold, leak, water, sewage, electrical, plumbing or pests. This is a rough keyword proxy, used only to choose a metro and never inside the product:

| Metro | Open residential 311s | …that describe a habitability hazard | Severe rent burden |
|---|---:|---:|---:|
| **New York** | 165 | **63** (HPD Class A/B/C violations) | **25.2%** |
| San Francisco | 140 | 70 | 17.5% |
| Chicago | 165 | 47 | 18.9% |
| Baton Rouge | 10 | 1 | 27.2% |
| Cincinnati | 152 | **0** (mostly trash / tall grass) | 23.1% |
| Austin | 122 | **0** | 21.1% |

**New York wins on both axes:** it has a real habitability corpus *and* the second-highest rent burden. Its narratives are written in inspector code language (`§ 27-2031 ADM CODE PROVIDE HOT WATER AT ALL HOT WATER FIXTURES…`) while tenants say "the radiators are cold", which is the exact gap vector search exists to close.

> **Deck line (Rigor & judgment):** *"Before writing code we audited all six metros. Cincinnati and Austin have zero open habitability narratives, so a navigator there would 'work' and find nothing. We chose New York because its 311 record can actually corroborate a defense."*

Other New York specifics the code must respect:
- **168 tracts** across Bronx, Kings, New York and Queens counties (4× other metros), so every tract join must be fan-out safe.
- Income rules in NYC bulletins use **FPL (Federal Poverty Level)**, not AMI. The eligibility engine supports both.
- Modeled filings: **45,471/yr**. Always label these `[Modeled]`.

---

## 2. The story: Marisol's Monday

> *Marisol is a fictional composite. Her block and every record ID below are real rows in our New York dataset.*

**Thursday, November 19, 2026, 3:40 pm. Northern Manhattan legal-aid walk-in clinic.**

Marisol is 34. She is a home health aide raising two kids, Leo (9) and Daniela (6), in a third-floor walk-up on the **1000 block of St. Nicholas Avenue** in Washington Heights. She has lived there for seven years.

In September her agency cut her shifts from five days to three. She paid half of October's rent, then nothing in November. She now owes **$3,350**. On November 2 the landlord's attorney served a written rent demand, and then a nonpayment petition. **Her hearing is Monday, November 23 at 9:30 am** in Manhattan Housing Court. She is holding a folded index-number notice.

She didn't come in about the rent. She came in because she is scared about the apartment:

> *"The radiators have been cold since the first week of November. I run the oven for heat. There's black stuff spreading around the tub, and water comes through the bathroom wall when the upstairs neighbor showers. Daniela's inhaler, she used to need it once a week, now it's every night. I told the super. He said the boiler guy is coming. Nobody came."*

Marisol doesn't know three things that could change her Monday:

1. **The city already has these conditions on record.** On November 1, HPD inspectors logged open violations on her block and the next one: a **Class C** heating-system violation (boiler room locked, `NYC-19346259`, 900 block), a **Class A** visible-mold violation (`NYC-19346354`, 1000 block), and a **Class B** water leak at a bathroom wall (`NYC-19346353`, 1000 block). None of this is in her court file.
2. **New York law ties these conditions to her defense.** Under RPL § 235-b (warranty of habitability) she can claim rent abatement. NYC Admin. Code § 27-2115 required Class C heat hazards to be fixed **within 24 hours**, and it has been 18 days. At ≤200% FPL she qualifies for **free Right to Counsel**.
3. **Money exists, but it's split across four programs with different rules.** Two of them require an open habitability case, which she has (at block level). One clears arrears up to $15,000. One needs her Housing Court index number, which she has.

**Dev, the paralegal**, has eleven families in the waiting room and about twenty minutes for Marisol. Today that means calling HPD, searching three websites and hoping. **With our navigator, Dev has a conversation.** At 4:05 pm he hands the supervising attorney a **Tenant Stabilization Brief**. It lists three corroborating city records, explains why two "perfect-match" boiler records were rejected, cites the statutes, names the funds she qualifies for, and lists what still needs proof. That includes whether the violations are in *her* building, which the 100-block public record cannot show on its own.

On Monday the attorney walks in with a habitability defense, an HP-action referral and a One Shot Deal application already started. Marisol doesn't sign a hallway settlement.

### Neighborhood context (tract `36061024500`, New York County)

| Signal | Tract | Metro |
|---|---:|---:|
| Severe rent burden (50%+ of income) | **32.8%** | 25.2% |
| Modeled annual nonpayment filings `[Modeled]` | **414** | median tract 196 |
| Modeled default judgments `[Modeled]` | 157 | — |
| Median claimed arrears `[Modeled]` | $3,411 | — |
| Households without a vehicle | 91.6% | — |
| Median household income | $51,403 | — |

Two notes for the demo. First, Marisol's $3,350 is in line with the tract's typical modeled arrears, so she is a typical case, not an edge case. Second, 92% of households here have no car, which is why the brief should flag transit to court as an access risk (a "question that needs more data" from the README).

---

## 3. The demo conversation (golden path)

This is both the **acceptance test** and the **video script**. Each turn has to work live on the deployed agent.

| # | Dev types | Agent does (tools) | Must show on screen |
|---|---|---|---|
| 1 | *"New intake. Tenant on the 1000 block of St. Nicholas Ave, Manhattan. Nonpayment hearing Monday 9:30. Radiators cold since early Nov, black mold around the tub, water coming through the bathroom wall. Anything open on her block?"* | `open_case` → `search_habitability_evidence` (3 hazard queries, top_k 20, unfiltered) → post-filter | 3+ corroborating records with request IDs, HPD class and similarity. **"Excluded: 4 records"** with reasons |
| 2 | *"Why did you drop that boiler record? It looked like an exact match."* | Reads exclusions from the case file | `DECOY-NEWY-04`: "Closed – Abated: landlord replaced boiler, inspector verified." `DECOY-NEWY-01`: "Commercial storefront, zero residential tenants." |
| 3 | *"What law covers this?"* | `match_statutes` (vector search over statutes) | RPL § 235-b, Admin Code § 27-2115 (Class C = 24 h), SSL § 143-b. Note: "Ask whether she received the 14-day written demand (RPAPL § 711(2)). The record can't tell us." |
| 4 | *"Household of 3, about $31k a year, she has the court index number. Her daughter has asthma that's gotten worse."* | `update_case` → `match_relief_funds` | Ranked funds with pass/fail per rule: Right to Counsel + Class C defense ✅, ERP heat/mold clinic ✅, One Shot Deal ✅ ($15k cap > $3,350), CityFHEPS ✅ (index number). Asthma is noted for the attorney (mold, Class A) and **not** used as an eligibility input |
| 5 | *"How bad is this neighborhood compared to the city?"* | `get_tract_context` (MCP Toolbox, fan-out-safe SQL) | 32.8% vs 25.2% severe burden, 414 modeled filings vs 196 median, each labeled `[Modeled]` |
| 6 | *"Landlord's lawyer says the boiler was fixed last week."* | Re-checks the records: still open as of data date | "Public record shows Class C still open as of 2026-11-01 data. Fixed-or-not can't be verified from this data. Request HPD re-inspection and a dated photo or log from the tenant." |
| 7 | *"Draft the brief for the attorney."* | `finalize_brief` → saves the artifact with the **code-rendered** equity audit appended | Full Tenant Stabilization Brief (Section 11) |

**Recording tip:** in turn 1, keep the raw top-5 list visible before the filter is applied. Judges specifically want to see "raw similarity ranked a decoy #1 and the post-filter caught it."

---

## 4. Architecture

```
                ┌────────────────────────────────────────────────────────────┐
 Paralegal ───▶ │  Front end (custom "Intake Desk" page, or adk web)          │
                └──────────────┬─────────────────────────────────────────────┘
                               │  HTTPS (ADK API server: /run_sse)
                ┌──────────────▼─────────────────────────────────────────────┐
                │  Cloud Run: ADK agent  "stabilization_navigator" (Gemini)  │
                │  Session state = CASE FILE (block, hearing, household,     │
                │  hazards, evidence, exclusions, statutes, funds)           │
                │                                                            │
                │  Custom Python tools (our domain judgment)                 │
                │   open_case / update_case                                  │
                │   search_habitability_evidence ──┐  AI.EMBED + VECTOR_     │
                │   match_statutes ────────────────┤  SEARCH, then hard      │
                │   match_relief_funds             │  post-filter + reasons  │
                │   finalize_brief ── equity audit (code-only, never LLM)    │
                │                                                            │
                │  MCPToolset ──────────────┐                                │
                └───────────────────────────┼────────────────────────────────┘
                                            │
                ┌───────────────────────────▼──────────────┐
                │ Cloud Run: MCP Toolbox for Databases      │  (min-instances=1)
                │  get_tract_context, metro_baseline,       │
                │  list_relief_programs (parameterized SQL) │
                └───────────────────────────┬──────────────┘
                                            │
                ┌───────────────────────────▼──────────────────────────────────┐
                │ BigQuery  a4i_housing (US)                                   │
                │  5 starter tables + complaints_embedded + statutes_embedded  │
                │  + bulletins_embedded + v_tract_context (fan-out safe)       │
                │  connection us.a4i-vertex → gemini-embedding-2               │
                └──────────────────────────────────────────────────────────────┘
```

**Principles (repeat these in the deck):**
1. **Vector search generates candidates. It doesn't decide.** Rules decide eligibility, and every exclusion carries a reason.
2. **The LLM reasons and writes. It never computes eligibility.** The Python tools compute pass/fail, and Gemini explains it.
3. **`audit_*` columns never enter retrieval, scoring or any prompt.** The equity audit is rendered by code after the brief is final.
4. **Two evidence layers, kept separate:** block-level public record vs unit-level facts only the tenant or attorney can establish.

---

## 5. Repository layout

```
agent/
  navigator/
    __init__.py              # from . import agent
    agent.py                 # root_agent (ADK)
    prompts.py               # SYSTEM_INSTRUCTION
    config.py                # project, dataset, connection, FPL table, model
    bq.py                    # BigQuery client + run_query helper (parameterized only)
    tools/
      case_file.py           # open_case, update_case
      evidence.py            # search_habitability_evidence (+ exclusion logic)
      statutes.py            # match_statutes
      funds.py               # match_relief_funds (eligibility engine)
      brief.py               # finalize_brief, render_brief_markdown
    equity.py                # equity audit (code-only), used by brief.py + batch script
  requirements.txt
  .env.example
  tests/
    test_decoys.py           # all 9 DECOY-* never reach kept evidence
    test_eligibility.py      # Marisol fixture → expected fund verdicts
    test_fanout.py           # tract context row counts == 168
    golden_conversation.md   # Section 3 table, used for manual QA
mcp/
  tools.yaml                 # MCP Toolbox config
  deploy_toolbox.sh
sql/
  01_connection.sh
  02_embed_complaints.sql
  03_embed_rules.sql
  04_views.sql
  05_equity_audit.sql
frontend/                    # optional custom UI (Section 13.2)
scripts/
  run_equity_audit.py        # batch audit → numbers for the deck
docs/
  IMPLEMENTATION.md          # this file
  rigor/                     # proof outputs from every mission (judges' Rigor score)
.agent/
  rules/navigator-guardrails.md   # mirror of AGENTS.md for Antigravity
  workflows/m00-…m13-*.md         # one slash-command workflow per mission
AGENTS.md                    # guardrails Antigravity must follow
GEMINI.md                    # pointer to AGENTS.md + this doc
```

---

## 6. Phase 0: Load data and build embeddings

**Antigravity missions: M01 (load), M02 (connection), M03 (embeddings). Target: done by 0:45.**

```bash
# From repo root in Cloud Shell
bash scripts/load.sh new-york
```

Then confirm the notebook validation passes. Either run Section 12 of `notebooks/c_housing_01_load_explore.ipynb` with `METRO = "New York"`, or rely on `load.sh`'s verification block. Screenshot the PASS summary for the deck.

### 6.1 Vertex connection (`sql/01_connection.sh`)

```bash
#!/usr/bin/env bash
set -euo pipefail
PROJECT_ID="$(gcloud config get-value project)"
bq mk --connection --location=US --project_id="${PROJECT_ID}" \
  --connection_type=CLOUD_RESOURCE a4i-vertex || echo "connection exists"

SA="$(bq show --format=json --connection "${PROJECT_ID}.us.a4i-vertex" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["cloudResource"]["serviceAccountId"])')"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA}" --role="roles/aiplatform.user" --condition=None
echo "Waiting 60s for IAM propagation..."; sleep 60
```

---

## 7. BigQuery SQL artifacts

### 7.1 Embed complaints (`sql/02_embed_complaints.sql`)

The notebook version drops lat/long and dates. We keep them because we need proximity and "days open".

```sql
CREATE OR REPLACE TABLE `a4i_housing.complaints_embedded` AS
SELECT
  request_id, metro_area, jurisdiction, census_tract_geoid, block_address,
  agency_code, property_type, raw_complaint_type, inspection_status,
  created_date, closed_date, latitude, longitude, data_provenance,
  complaint_narrative,
  embedded.result AS embedding
FROM (
  SELECT *,
    AI.EMBED(complaint_narrative,
             connection_id => 'us.a4i-vertex',
             endpoint => 'gemini-embedding-2') AS embedded
  FROM `a4i_housing.municipal_311_housing_complaints`
)
WHERE embedded.status = '';

-- Sanity: expect 174 (165 real + 9 decoys)
SELECT COUNT(*) AS n, COUNTIF(request_id LIKE 'DECOY-%') AS decoys
FROM `a4i_housing.complaints_embedded`;
```

### 7.2 Embed statutes and bulletins (`sql/03_embed_rules.sql`)

This puts semantic search on the legal side too, and covers trap #4 in notebook Section 13.

```sql
CREATE OR REPLACE TABLE `a4i_housing.statutes_embedded` AS
SELECT s.* EXCEPT(embedded), embedded.result AS embedding
FROM (
  SELECT *, AI.EMBED(CONCAT(ordinance_title, '. ', raw_statute_text),
                     connection_id => 'us.a4i-vertex',
                     endpoint => 'gemini-embedding-2') AS embedded
  FROM `a4i_housing.municipal_housing_ordinance_statutes`
) AS s
WHERE embedded.status = '';

CREATE OR REPLACE TABLE `a4i_housing.bulletins_embedded` AS
SELECT b.* EXCEPT(embedded), embedded.result AS embedding
FROM (
  SELECT *, AI.EMBED(CONCAT(program_name, '. ', raw_bulletin_text),
                     connection_id => 'us.a4i-vertex',
                     endpoint => 'gemini-embedding-2') AS embedded
  FROM `a4i_housing.rental_relief_program_bulletins`
) AS b
WHERE embedded.status = '';
```

### 7.3 Fan-out-safe tract view (`sql/04_views.sql`)

```sql
-- One row per tract. court_eviction_filings is aggregated BEFORE the join (4 quarters/tract).
CREATE OR REPLACE VIEW `a4i_housing.v_tract_context` AS
WITH annual_filings AS (
  SELECT census_tract_geoid,
         SUM(nonpayment_filings_count)              AS annual_nonpayment_filings,
         SUM(holdover_or_no_fault_filings_count)    AS annual_holdover_filings,
         SUM(default_judgments_count)               AS annual_default_judgments,
         ROUND(AVG(median_claimed_arrears_usd), 0)  AS avg_claimed_arrears_usd,
         COUNT(*)                                   AS quarters_aggregated   -- must be 4
  FROM `a4i_housing.court_eviction_filings`
  GROUP BY census_tract_geoid
),
open_res AS (
  SELECT census_tract_geoid, COUNT(*) AS open_residential_311
  FROM `a4i_housing.municipal_311_housing_complaints`
  WHERE property_type = 'Residential' AND closed_date IS NULL
    AND request_id NOT LIKE 'DECOY-%'
  GROUP BY census_tract_geoid
)
SELECT
  a.census_tract_geoid,                        -- STRING, 11 chars. Never cast.
  a.county_name,
  a.renter_occupied_units,
  a.median_household_income,
  a.median_gross_rent,
  ROUND(SAFE_DIVIDE(a.renter_hh_rent_50_pct_plus_count, a.renter_occupied_units) * 100, 1) AS severe_rent_burden_pct,
  ROUND(SAFE_DIVIDE(a.renter_hh_rent_30_to_49_pct_count, a.renter_occupied_units) * 100, 1) AS rent_burden_30_49_pct,
  ROUND(a.poverty_rate * 100, 1)    AS poverty_pct,
  ROUND(a.no_vehicle_rate * 100, 1) AS no_vehicle_pct,
  COALESCE(f.annual_nonpayment_filings, 0) AS annual_nonpayment_filings_modeled,
  COALESCE(f.annual_holdover_filings, 0)   AS annual_holdover_filings_modeled,
  COALESCE(f.annual_default_judgments, 0)  AS annual_default_judgments_modeled,
  f.avg_claimed_arrears_usd                AS avg_claimed_arrears_usd_modeled,
  f.quarters_aggregated,
  COALESCE(o.open_residential_311, 0)      AS open_residential_311
  -- NOTE: audit_* columns intentionally NOT exposed in this view.
FROM `a4i_housing.acs_tract_housing_tenure` a
LEFT JOIN annual_filings f USING (census_tract_geoid)
LEFT JOIN open_res o USING (census_tract_geoid);

CREATE OR REPLACE VIEW `a4i_housing.v_metro_baseline` AS
SELECT
  ROUND(SAFE_DIVIDE(SUM(a.renter_hh_rent_50_pct_plus_count), SUM(a.renter_occupied_units)) * 100, 1) AS metro_severe_rent_burden_pct,
  APPROX_QUANTILES(t.annual_nonpayment_filings_modeled, 2)[OFFSET(1)] AS median_tract_nonpayment_filings_modeled,
  COUNT(*) AS tracts
FROM `a4i_housing.acs_tract_housing_tenure` a
JOIN `a4i_housing.v_tract_context` t USING (census_tract_geoid);
```

### 7.4 The search query used by the evidence tool

Multi-query (one row per hazard), **unfiltered** `top_k => 20`, so the tool can show and explain what it excluded. (`top_k` runs before any `WHERE`, which is notebook trap #3.)

```sql
WITH anchor AS (
  -- Anchor point = centroid of 311 rows on the tenant's block, else tract centroid
  SELECT COALESCE(
    (SELECT ST_GEOGPOINT(AVG(longitude), AVG(latitude))
       FROM `a4i_housing.municipal_311_housing_complaints`
      WHERE LOWER(block_address) LIKE CONCAT('%', LOWER(@block_hint), '%')
        AND @block_hint != ''),
    (SELECT ST_GEOGPOINT(longitude, latitude)
       FROM `a4i_housing.acs_tract_housing_tenure`
      WHERE census_tract_geoid = @tract_hint)
  ) AS pt
),
hits AS (
  SELECT query.query_text, base.*, distance
  FROM VECTOR_SEARCH(
    TABLE `a4i_housing.complaints_embedded`, 'embedding',
    (SELECT q AS query_text,
            AI.EMBED(q, connection_id => 'us.a4i-vertex',
                        endpoint => 'gemini-embedding-2').result AS query_vec
       FROM UNNEST(@queries) AS q),
    query_column_to_search => 'query_vec',
    top_k => 20,
    options => '{"use_brute_force":true}'
  )
)
SELECT
  h.request_id, h.block_address, h.census_tract_geoid, h.property_type,
  h.raw_complaint_type, h.inspection_status, h.created_date, h.closed_date,
  h.complaint_narrative, h.query_text,
  ROUND(1 - h.distance, 4) AS similarity,
  ROUND(ST_DISTANCE(ST_GEOGPOINT(h.longitude, h.latitude), (SELECT pt FROM anchor)), 0) AS meters_from_anchor
FROM hits h
QUALIFY ROW_NUMBER() OVER (PARTITION BY h.request_id ORDER BY h.distance) = 1
ORDER BY h.distance;
```

> If `@block_hint` matches nothing and no tract is given, the anchor is NULL and `meters_from_anchor` is NULL. The tool then asks the user for a block or tract instead of guessing.

---

## 8. Custom tools (Python)

These carry the "a tool you built" points (Technical) and most of Rigor. All BigQuery calls use **parameterized queries**. Never format user text into SQL.

### 8.1 `config.py`

```python
import os

PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
DATASET = os.getenv("A4I_DATASET", "a4i_housing")
BQ_LOCATION = os.getenv("A4I_LOCATION", "US")
METRO = "New York"
MODEL = os.getenv("NAVIGATOR_MODEL", "gemini-2.5-flash")  # use the newest Gemini available in the project

PROXIMITY_METERS = 800          # ~ 8–10 Manhattan blocks
MIN_SIMILARITY = 0.55           # tune once against Section 3 queries; log it in the deck
EMERGENCY_HOURS = 96            # hearing within ~4 days (e.g. Thursday intake → Monday court)

# HHS poverty guidelines (48 states). UPDATE to the current year's figures before demo.
FPL_BASE = 15_650
FPL_PER_EXTRA = 5_500
def fpl(household_size: int) -> int:
    return FPL_BASE + FPL_PER_EXTRA * max(household_size - 1, 0)

# Exclusion reasons — shown verbatim in the UI and brief
EXCLUSION_REASONS = {
    "commercial": "Commercial property — no residential tenants; cannot support a residential habitability defense.",
    "closed_abated": "Closed – Abated — condition was repaired and re-inspected; not an active hazard.",
    "closed_no_violation": "Closed – No Violation — inspector found no defect; this record would undercut, not support, the claim.",
    "closed_other": "Closed — no longer an open enforcement case.",
    "too_far": "Outside the {m} m corroboration radius from the tenant's block.",
    "low_similarity": "Semantic similarity below threshold — different hazard.",
    "planted": "Labeled [Planted Case] teaching decoy.",
}
```

### 8.2 `bq.py`

```python
from google.cloud import bigquery
from .config import PROJECT, BQ_LOCATION

_client = bigquery.Client(project=PROJECT, location=BQ_LOCATION)

def run_query(sql: str, params: list | None = None) -> list[dict]:
    job = _client.query(sql, job_config=bigquery.QueryJobConfig(query_parameters=params or []))
    return [dict(r) for r in job.result()]
```

### 8.3 Case file in session state (`tools/case_file.py`)

The case file is what makes this a *working conversation*: later turns update it, and every tool reads from it.

```python
from datetime import date, datetime
from google.adk.tools import ToolContext

def open_case(block_address: str, hearing_datetime: str, hazards: list[str],
              tenant_narrative: str, tool_context: ToolContext,
              census_tract_geoid: str = "") -> dict:
    """Start a new intake case file.

    Args:
      block_address: Tenant's 100-block, e.g. "1000 Block St Nicholas Avenue". Never a unit number.
      hearing_datetime: ISO datetime of the court hearing, e.g. "2026-11-23T09:30".
      hazards: Short plain-language hazard phrases, e.g. ["no heat", "mold around tub", "water leak through wall"].
      tenant_narrative: The tenant's description, paraphrased, with names/units removed.
      census_tract_geoid: Optional 11-character tract GEOID (string).
    """
    hearing = datetime.fromisoformat(hearing_datetime)
    case = {
        "block_address": block_address,
        "census_tract_geoid": census_tract_geoid,
        "hearing_datetime": hearing_datetime,
        "hours_to_hearing": round((hearing - datetime.now()).total_seconds() / 3600, 1),
        "hazards": hazards,
        "tenant_narrative": tenant_narrative,
        "household": {},          # filled by update_case
        "evidence": [], "exclusions": [], "statutes": [], "funds": [],
        "open_questions": [],     # things the public record cannot prove
        "created": date.today().isoformat(),
    }
    tool_context.state["case"] = case
    from ..config import EMERGENCY_HOURS
    urgency = f"EMERGENCY (<{EMERGENCY_HOURS}h)" if case["hours_to_hearing"] < EMERGENCY_HOURS else "standard"
    return {"status": "opened", "urgency": urgency, "hours_to_hearing": case["hours_to_hearing"]}

def update_case(tool_context: ToolContext, household_size: int | None = None,
                annual_income_usd: float | None = None, arrears_usd: float | None = None,
                has_court_index_number: bool | None = None,
                received_written_rent_demand: bool | None = None,
                notes: str = "") -> dict:
    """Update household facts as the intake conversation reveals them.
    Health details go in `notes` for the attorney and are NEVER eligibility inputs."""
    case = tool_context.state.get("case")
    if not case:
        return {"error": "No open case. Call open_case first."}
    h = case["household"]
    for k, v in dict(household_size=household_size, annual_income_usd=annual_income_usd,
                     arrears_usd=arrears_usd, has_court_index_number=has_court_index_number,
                     received_written_rent_demand=received_written_rent_demand).items():
        if v is not None:
            h[k] = v
    if notes:
        h.setdefault("notes", []).append(notes)
    tool_context.state["case"] = case
    return {"status": "updated", "household": h}
```

### 8.4 Evidence search with explained exclusions (`tools/evidence.py`)

```python
from google.cloud import bigquery
from google.adk.tools import ToolContext
from ..bq import run_query
from ..config import DATASET, PROXIMITY_METERS, MIN_SIMILARITY, EXCLUSION_REASONS

SEARCH_SQL = open(__file__.replace("evidence.py", "search.sql")).read()  # Section 7.4 SQL

# Plain-language → inspector-language query expansion (helps recall; vector search does the matching)
HAZARD_EXPANSIONS = {
    "heat": "no heat in apartment, radiators cold, boiler not working, heating system inaccessible",
    "hot water": "no hot water at fixtures, hot water outage",
    "mold": "visible mold condition on walls and ceiling, black mold around bathtub",
    "leak": "water leak through ceiling or wall, abate evidence of water leak",
    "electric": "defective electrical outlet, exposed wiring, electrical hazard near water",
    "sewage": "sewage backup, clogged waste line, toilet overflowing",
    "pests": "roaches, mice, rodent infestation",
}

def _expand(hazards: list[str]) -> list[str]:
    out = []
    for h in hazards:
        key = next((k for k in HAZARD_EXPANSIONS if k in h.lower()), None)
        out.append(f"{h}. {HAZARD_EXPANSIONS[key]}" if key else h)
    return out[:6]

def _classify(row: dict) -> str | None:
    """Return an exclusion key, or None if the record is admissible corroboration."""
    # DECOY-* rows are classified by the same real rules as everything else, so the
    # explanation is substantive ("Closed – Abated"), not just "it's a decoy".
    if row["property_type"] != "Residential":
        return "commercial"
    if row["closed_date"] is not None:
        status = (row["inspection_status"] or "").lower()
        if "abated" in status:
            return "closed_abated"
        if "no violation" in status:
            return "closed_no_violation"
        return "closed_other"
    if row["meters_from_anchor"] is not None and row["meters_from_anchor"] > PROXIMITY_METERS:
        return "too_far"
    if row["similarity"] < MIN_SIMILARITY:
        return "low_similarity"
    return None

def search_habitability_evidence(tool_context: ToolContext, hazards: list[str] | None = None) -> dict:
    """Semantic search (BigQuery AI.EMBED + VECTOR_SEARCH) over 311 housing complaints for
    the open case, then apply hard eligibility rules: Residential, still open, near the block.
    Returns kept evidence AND every excluded near-match with its reason."""
    case = tool_context.state.get("case")
    if not case:
        return {"error": "No open case. Call open_case first."}
    queries = _expand(hazards or case["hazards"])
    rows = run_query(SEARCH_SQL, [
        bigquery.ArrayQueryParameter("queries", "STRING", queries),
        bigquery.ScalarQueryParameter("block_hint", "STRING", _block_core(case["block_address"])),
        bigquery.ScalarQueryParameter("tract_hint", "STRING", case.get("census_tract_geoid", "")),
    ])
    raw_top = [{"rank": i + 1, "request_id": r["request_id"], "similarity": r["similarity"],
                "status": r["inspection_status"], "property_type": r["property_type"]}
               for i, r in enumerate(rows[:5])]
    kept, excluded = [], []
    for r in rows:
        why = _classify(r)
        item = {k: (str(v) if v is not None and k.endswith("_date") else v) for k, v in r.items()}
        if why:
            item["excluded_because"] = EXCLUSION_REASONS[why].format(m=PROXIMITY_METERS)
            if r["request_id"].startswith("DECOY-"):
                item["excluded_because"] += " " + EXCLUSION_REASONS["planted"]
            # only surface semantically relevant exclusions (the interesting near-misses)
            if r["similarity"] >= MIN_SIMILARITY:
                excluded.append(item)
        else:
            kept.append(item)
    case["evidence"], case["exclusions"] = kept[:8], excluded[:8]
    if not kept:
        case["open_questions"].append(
            "No open residential 311/HPD record corroborates these conditions near this block. "
            "Possible under-reporting: route to an inspection request and to funds that do not "
            "require an open habitability case.")
    tool_context.state["case"] = case
    return {"queries_used": queries, "raw_top5_before_rules": raw_top,
            "kept": case["evidence"], "excluded": case["exclusions"],
            "evidence_scope": "100-block public record — corroborates block conditions, not the tenant's unit."}

def _block_core(block: str) -> str:
    # "1000 Block St Nicholas Avenue, Manhattan" -> "1000 block st nicholas"
    b = block.lower().replace("ave.", "avenue").split(",")[0]
    return " ".join(b.split()[:4])
```

> **Antigravity (M04):** move the Section 7.4 SQL into `tools/search.sql`. Add a unit test asserting **no `DECOY-*` id ever appears in `kept`** across 10 hazard phrasings.

### 8.5 Statutes (`tools/statutes.py`)

```python
STATUTE_SQL = """
SELECT base.statute_section_id, base.jurisdiction, base.code_citation, base.ordinance_title,
       base.raw_statute_text, ROUND(1 - distance, 4) AS similarity
FROM VECTOR_SEARCH(
  TABLE `a4i_housing.statutes_embedded`, 'embedding',
  (SELECT AI.EMBED(@q, connection_id => 'us.a4i-vertex', endpoint => 'gemini-embedding-2').result AS v),
  query_column_to_search => 'v', top_k => 3, options => '{"use_brute_force":true}')
ORDER BY distance
"""

def match_statutes(tool_context: ToolContext) -> dict:
    """Rank this metro's housing statutes against the case's hazards + nonpayment posture
    using vector search. Returns citations plus procedural checks the record can't answer."""
    case = tool_context.state["case"]
    q = (f"Nonpayment eviction defense; tenant has hazardous conditions: {', '.join(case['hazards'])}. "
         f"Rent abatement, repair deadlines, complete defense for uncorrected violations, right to counsel.")
    rows = run_query(STATUTE_SQL, [bigquery.ScalarQueryParameter("q", "STRING", q)])
    case["statutes"] = rows
    # Deterministic procedural checks tied to known NY citations
    checks = []
    if any("711" in r["code_citation"] for r in rows) and \
       case["household"].get("received_written_rent_demand") is None:
        checks.append("Confirm tenant received a 14-day WRITTEN rent demand before filing (RPAPL § 711(2)). "
                      "Not provable from public records.")
    if any("27-2115" in r["code_citation"] for r in rows):
        checks.append("Class C (heat/hot water) must be corrected within 24 hours; Class B within 30 days. "
                      "Compare against violation created_date.")
    case["open_questions"] += checks
    tool_context.state["case"] = case
    return {"statutes": rows, "procedural_checks": checks,
            "disclaimer": "Statutory summaries support internal triage, not legal advice."}
```

### 8.6 Relief fund eligibility engine (`tools/funds.py`)

**Rules are evaluated in code.** Caps are parsed from `raw_bulletin_text` with regex and cross-checked against the structured flags.

```python
import re
from ..config import fpl

FUNDS_SQL = """
SELECT b.bulletin_id, b.program_name, b.administering_agency, b.funding_stream,
       b.requires_open_habitability_case, b.residential_tenants_only,
       b.raw_bulletin_text, b.intake_url, b.effective_date,
       ROUND(1 - vs.distance, 4) AS hazard_fit
FROM `a4i_housing.rental_relief_program_bulletins` b
LEFT JOIN (
  SELECT base.bulletin_id, distance
  FROM VECTOR_SEARCH(TABLE `a4i_housing.bulletins_embedded`, 'embedding',
    (SELECT AI.EMBED(@q, connection_id => 'us.a4i-vertex', endpoint => 'gemini-embedding-2').result AS v),
    query_column_to_search => 'v', top_k => 4, options => '{"use_brute_force":true}')
) vs USING (bulletin_id)
"""

_CAP = re.compile(r"up to \$([\d,]+)", re.I)
_INCOME = re.compile(r"<=\s*(\d+)%\s*(AMI|FPL)", re.I)

def _evaluate(b: dict, case: dict) -> dict:
    h = case["household"]
    checks = []
    def chk(name, ok, detail):
        checks.append({"rule": name, "pass": ok, "detail": detail})

    if b["residential_tenants_only"]:
        chk("Residential tenant", True, "Tenant rents a residential unit (intake confirmed).")

    if b["requires_open_habitability_case"]:
        has_open = len(case["evidence"]) > 0
        chk("Open habitability case", has_open,
            f"{len(case['evidence'])} open residential HPD/311 record(s) on/near block"
            + (" — attorney must confirm at least one is in the tenant's building." if has_open else ""))

    m = _INCOME.search(b["raw_bulletin_text"])
    if m:
        pct, basis = int(m.group(1)), m.group(2).upper()
        if basis == "FPL" and h.get("household_size") and h.get("annual_income_usd") is not None:
            limit = pct / 100 * fpl(h["household_size"])
            chk(f"Income ≤{pct}% FPL", h["annual_income_usd"] <= limit,
                f"${h['annual_income_usd']:,.0f} vs limit ${limit:,.0f} (household of {h['household_size']})")
        elif basis == "AMI":
            chk(f"Income ≤{pct}% AMI", None, "AMI table not loaded — verify manually (BYOD: HUD Income Limits, public domain).")
        else:
            chk(f"Income ≤{pct}% {basis}", None, "Need household size and income.")

    cap = _CAP.search(b["raw_bulletin_text"])
    cap_usd = int(cap.group(1).replace(",", "")) if cap else None
    if cap_usd and h.get("arrears_usd"):
        chk("Award covers arrears", cap_usd >= h["arrears_usd"],
            f"Cap ${cap_usd:,} vs arrears ${h['arrears_usd']:,.0f}")

    text = b["raw_bulletin_text"].lower()
    if "index number" in text or "rent demand" in text:
        ok = bool(h.get("has_court_index_number") or h.get("received_written_rent_demand"))
        chk("Court index number or rent demand", ok, "Tenant holds Housing Court index number." if ok else "Not confirmed.")
    if "heat" in text and "mold" in text:
        hz = " ".join(case["hazards"]).lower()
        chk("Hazard type covered (heat/hot water/lead/mold)", any(w in hz for w in ["heat", "hot water", "mold", "lead"]),
            "Case hazards include heat and mold.")

    verdicts = [c["pass"] for c in checks]
    status = "ELIGIBLE" if all(v is True for v in verdicts) else ("INELIGIBLE" if False in verdicts else "NEEDS INFO")
    return {**{k: b[k] for k in ["bulletin_id", "program_name", "administering_agency",
                                 "requires_open_habitability_case", "intake_url"]},
            "max_award_usd": cap_usd, "hazard_fit": b.get("hazard_fit"),
            "status": status, "checks": checks}

def match_relief_funds(tool_context: ToolContext) -> dict:
    """Evaluate every emergency stabilization fund for this household with explicit rule checks.
    Ranks ELIGIBLE first, then habitability-linked programs when the hearing is imminent."""
    case = tool_context.state["case"]
    q = f"Relief for tenant facing nonpayment eviction with {', '.join(case['hazards'])}"
    rows = run_query(FUNDS_SQL, [bigquery.ScalarQueryParameter("q", "STRING", q)])
    results = [_evaluate(b, case) for b in rows]
    from ..config import EMERGENCY_HOURS
    urgent = case["hours_to_hearing"] < EMERGENCY_HOURS
    order = {"ELIGIBLE": 0, "NEEDS INFO": 1, "INELIGIBLE": 2}
    results.sort(key=lambda r: (order[r["status"]],
                                -(1 if urgent and r["requires_open_habitability_case"] else 0),
                                -(r["hazard_fit"] or 0)))
    case["funds"] = results
    tool_context.state["case"] = case
    return {"funds": results, "deadline_weighting": f"hearing < {EMERGENCY_HOURS}h: defense-linked programs ranked first" if urgent else "standard"}
```

**Expected verdicts for Marisol** (household 3, $31,000, arrears $3,350, index number = yes, 3 open records). These form the `test_eligibility.py` fixture:

| Program | Expected | Key reason |
|---|---|---|
| BUL-NY-02 Right to Counsel & HPD Class C Spiegel Defense | ELIGIBLE | Open HPD violation; ≤200% FPL ($31,000 < ~$53,300) |
| BUL-NY-04 ERP Tenant Stabilization & Escrow Clinic | ELIGIBLE | Open heat + mold violations; up to $5,500 |
| BUL-NY-01 HRA One Shot Deal | ELIGIBLE | $15,000 cap ≥ $3,350 arrears; ≤200% FPL |
| BUL-NY-03 CityFHEPS Prevention | ELIGIBLE | Index number held; ≤200% FPL |

> **Twist to demo:** rerun with `evidence = []` (no open record). BUL-NY-02 and BUL-NY-04 flip to INELIGIBLE, and the agent routes to One Shot Deal and CityFHEPS plus an inspection request. That is the README's under-reporting fallback, and it shows rules doing the work.

### 8.7 Brief (`tools/brief.py`)

```python
from google.genai import types
from ..equity import tract_equity_note   # code-only; never returned to the LLM

async def finalize_brief(memo_markdown: str, tool_context: ToolContext) -> dict:
    """Save the Tenant Stabilization Brief as an artifact.
    Args:
      memo_markdown: The drafted legal-aid intake memo (Section 6 of the brief) written by you.
    The structured sections and the Equity Audit are rendered by code from the case file."""
    case = tool_context.state["case"]
    md = render_brief_markdown(case, memo_markdown)
    md += "\n\n" + tract_equity_note(case)          # appended AFTER; LLM never sees audit_* values
    await tool_context.save_artifact("tenant_stabilization_brief.md",
                                     types.Part.from_text(text=md))
    return {"status": "saved", "artifact": "tenant_stabilization_brief.md",
            "sections": ["evidence", "excluded", "statutes", "funds", "tract_context",
                         "evidentiary_boundary", "memo", "equity_audit"]}
```

`render_brief_markdown` is a pure function that formats the Section 11 template from `case`. Antigravity implements it in M05 with a snapshot test.

---

## 9. Managed MCP: MCP Toolbox for Databases

This satisfies "consume at least one Google-managed MCP server". We use it for **structured context lookups**, and keep domain judgment in our Python tools.

### 9.1 `mcp/tools.yaml`

```yaml
sources:
  a4i-bq:
    kind: bigquery
    project: ${GOOGLE_CLOUD_PROJECT}
    location: US

tools:
  get_tract_context:
    kind: bigquery-sql
    source: a4i-bq
    description: >
      Neighborhood context for one census tract: severe rent burden, MODELED annual eviction
      filings (pre-aggregated across 4 quarters, no fan-out), open residential 311 count,
      poverty and vehicle access. GEOID is an 11-character string.
    parameters:
      - name: census_tract_geoid
        type: string
        description: 11-character census tract GEOID, e.g. "36061024500"
    statement: |
      SELECT t.*, b.metro_severe_rent_burden_pct, b.median_tract_nonpayment_filings_modeled
      FROM `a4i_housing.v_tract_context` t CROSS JOIN `a4i_housing.v_metro_baseline` b
      WHERE t.census_tract_geoid = @census_tract_geoid

  find_tract_for_block:
    kind: bigquery-sql
    source: a4i-bq
    description: Resolve a 100-block address fragment to its census tract GEOID(s).
    parameters:
      - name: block_fragment
        type: string
        description: e.g. "1000 Block St Nicholas"
    statement: |
      SELECT DISTINCT block_address, census_tract_geoid
      FROM `a4i_housing.municipal_311_housing_complaints`
      WHERE LOWER(block_address) LIKE CONCAT('%', LOWER(@block_fragment), '%')
        AND request_id NOT LIKE 'DECOY-%'
      LIMIT 5

  list_relief_programs:
    kind: bigquery-sql
    source: a4i-bq
    description: List this metro's emergency rental relief programs and their structured flags.
    statement: |
      SELECT bulletin_id, program_name, administering_agency, requires_open_habitability_case,
             residential_tenants_only, intake_url, effective_date
      FROM `a4i_housing.rental_relief_program_bulletins`

toolsets:
  navigator:
    - get_tract_context
    - find_tract_for_block
    - list_relief_programs
```

> `audit_*` columns are not reachable through any MCP tool, by design.

### 9.2 `mcp/deploy_toolbox.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
PROJECT_ID="$(gcloud config get-value project)"; REGION=us-central1
gcloud iam service-accounts create sq7-toolbox-sa --display-name "MCP Toolbox" || true
SA="sq7-toolbox-sa@${PROJECT_ID}.iam.gserviceaccount.com"
for ROLE in roles/bigquery.dataViewer roles/bigquery.jobUser; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$SA" --role="$ROLE" --condition=None
done
gcloud secrets create sq7-toolbox-tools --data-file=mcp/tools.yaml 2>/dev/null || \
  gcloud secrets versions add sq7-toolbox-tools --data-file=mcp/tools.yaml
gcloud secrets add-iam-policy-binding sq7-toolbox-tools --member="serviceAccount:$SA" --role=roles/secretmanager.secretAccessor

gcloud run deploy sq7-mcp-toolbox \
  --image=us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest \
  --region="$REGION" --service-account="$SA" \
  --set-secrets="/app/tools.yaml=sq7-toolbox-tools:latest" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --args="--tools-file=/app/tools.yaml,--address=0.0.0.0,--port=8080" \
  --min-instances=1 --no-allow-unauthenticated
```

> `--min-instances=1` avoids a cold start during the recorded demo (README hint). If `${GOOGLE_CLOUD_PROJECT}` substitution isn't supported in your Toolbox version, hardcode the project id.

---

## 10. The ADK agent and system prompt

### 10.1 `agent.py`

```python
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StreamableHTTPConnectionParams
from .config import MODEL
from .prompts import SYSTEM_INSTRUCTION
from .tools.case_file import open_case, update_case
from .tools.evidence import search_habitability_evidence
from .tools.statutes import match_statutes
from .tools.funds import match_relief_funds
from .tools.brief import finalize_brief
import os

toolbox = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=os.environ["TOOLBOX_URL"] + "/mcp",
        headers={"Authorization": f"Bearer {os.environ.get('TOOLBOX_ID_TOKEN', '')}"},
    ),
    tool_filter=["get_tract_context", "find_tract_for_block", "list_relief_programs"],
)

root_agent = Agent(
    name="stabilization_navigator",
    model=MODEL,
    description="Eviction-prevention intake navigator for NYC legal-aid paralegals.",
    instruction=SYSTEM_INSTRUCTION,
    tools=[open_case, update_case, search_habitability_evidence, match_statutes,
           match_relief_funds, finalize_brief, toolbox],
)
```

> **Antigravity (M06):** check the ADK version installed. If `StreamableHTTPConnectionParams` isn't available, use `SseConnectionParams(url=TOOLBOX_URL + "/mcp/sse")`, or `ToolboxToolset` from `google.adk.tools.toolbox_toolset`. For Cloud Run → Cloud Run auth, mint an ID token with `google.oauth2.id_token.fetch_id_token(Request(), TOOLBOX_URL)` per request (wrap it in a small header provider) instead of a static env var.

### 10.2 `prompts.py` (system instruction)

```text
You are the Stabilization Navigator, an intake co-pilot for legal-aid paralegals and housing
counselors in New York City. You help them build a Tenant Stabilization Brief before a housing
court hearing. You are not a lawyer, and your output is reviewed by a supervising attorney.

HOW YOU WORK
- On a new intake, call open_case first (100-block only, never unit numbers or names), then
  search_habitability_evidence. Resolve the tract with find_tract_for_block if needed.
- When the user adds facts (household size, income, arrears, index number, notices), call
  update_case, then re-run whatever those facts affect (usually match_relief_funds).
- Use match_statutes for legal questions and get_tract_context for neighborhood questions.
- Call finalize_brief only when asked for the brief/memo. Write the memo yourself; the tool
  renders the rest.

EVIDENCE RULES (non-negotiable)
- Vector search returns candidates. Only records the tool marks "kept" are corroboration.
  Never cite an excluded record as support. When asked about an exclusion, quote its reason.
- Always show the request_id, block, HPD class/complaint type, status and created date for
  each cited record.
- A 100-block record corroborates conditions on the block or building cluster, NOT inside the
  tenant's unit. Say so every time you summarize evidence.
- Court filing counts are [Modeled] neighborhood baselines, never this tenant's docket.
- If no open record exists, say so plainly, flag possible under-reporting, and route to an
  inspection request and to funds that don't require an open habitability case.

ELIGIBILITY
- Fund and statute eligibility come from the tools' rule checks. Report pass/fail/needs-info
  exactly as returned; never override a check with your own judgment.
- Health conditions, immigration status, race or ethnicity are NEVER eligibility inputs.
  Health details may be noted for the attorney.

DEADLINES
- Always state hours remaining to the hearing. If open_case reports EMERGENCY: lead with
  defenses and same-week actions (counsel, HP action, emergency arrears).

STYLE
- Paralegal-speed: short headings, bullets, record IDs in monospace. No legal advice phrasing
  ("you will win"); use "supports", "may qualify", "attorney to confirm".
- End substantive answers with "What the record can't prove yet:" plus 1–3 bullets.
```

### 10.3 `requirements.txt` and `.env.example`

```text
google-adk>=1.0
google-cloud-bigquery>=3.25
google-auth>=2.30
pytest
```

```bash
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project
GOOGLE_CLOUD_LOCATION=us-central1
A4I_DATASET=a4i_housing
NAVIGATOR_MODEL=gemini-2.5-flash
TOOLBOX_URL=https://sq7-mcp-toolbox-xxxx-uc.a.run.app
```

Run locally: `cd agent && adk web` (pick `navigator`).

---

## 11. Tenant Stabilization Brief: output contract

`render_brief_markdown(case, memo)` must output exactly these sections, in this order:

```markdown
# Tenant Stabilization Brief
**Prepared:** 2026-11-19 16:05 · **Hearing:** Mon 2026-11-23 09:30 (≈ 89 h) · **Urgency:** EMERGENCY (<96h)
**Block:** 1000 Block St Nicholas Avenue · **Tract:** 36061024500 (New York County)
> Internal triage aid prepared by a paralegal with AI assistance. Not legal advice. Attorney review required.

## 1. Corroborating public records (open, residential, ≤800 m)
| Request ID | Block | Type | Status | Opened | Similarity |
|---|---|---|---|---|---|
| `NYC-19346259` | 900 Block St Nicholas Ave | HPD Class C — heating system access (boiler room locked) | Open | 2026-11-01 | 0.71 |
| `NYC-19346354` | 1000 Block St Nicholas Ave | HPD Class A — visible mold around bathtub | Open | 2026-11-01 | 0.78 |
| `NYC-19346353` | 1000 Block St Nicholas Ave | HPD Class B — water leak at bathroom wall | Open | 2026-11-01 | 0.74 |

### Near-matches excluded (and why)
- `DECOY-NEWY-04` (sim 0.80): Closed – Abated — boiler replaced and re-inspected. *[Planted Case]*
- `DECOY-NEWY-01` (sim 0.77): Commercial storefront — zero residential tenants. *[Planted Case]*
- `DECOY-NEWY-07` (sim 0.69): Closed – No Violation — inspector found heat at 71°F. *[Planted Case]*

## 2. Applicable law
- **RPL § 235-b / RPAPL § 711(2):** warranty of habitability → rent abatement; 14-day written demand prerequisite.
- **NYC Admin. Code § 27-2115 / § 26-1302:** Class C correction within 24 h (Class B: 30 days); Right to Counsel ≤200% FPL.
- **SSL § 143-b / MDL § 302-a:** defense where rent-impairing violations remain uncorrected *(applicability: attorney to confirm)*.

## 3. Emergency relief match
| Program | Status | Why | Max | Apply |
|---|---|---|---|---|
| Right to Counsel & HPD Class C Defense (BUL-NY-02) | ✅ Eligible | Open HPD violation; $31,000 ≤ 200% FPL | $4,000 | legalaidnyc.org |
| … | | | | |

## 4. Neighborhood context
Severe rent burden 32.8% (metro 25.2%) · 414 nonpayment filings/yr [Modeled] (median tract 196) · 91.6% no-vehicle households → plan court transit.

## 5. Evidentiary boundary — what the public record cannot prove
- Whether the cited violations are in the tenant's building/unit (100-block redaction).
- Whether the 14-day written rent demand was properly served.
- Current repair status after 2026-11-01 (landlord claims boiler fixed → request HPD re-inspection).

## 6. Intake memo (draft for attorney)
<memo written by the agent>

## 7. Equity audit (auto-generated after output; not used in any ranking)
<rendered by equity.py>
```

---

## 12. Equity Audit (post-output only)

Two levels. Both are computed by **code**. Neither feeds back into retrieval, ranking or prompts.

### 12.1 Per-brief note (`equity.py → tract_equity_note`)

Reads `audit_*` and `no_vehicle_rate` for the case tract and the metro baseline, then renders:

> *Who lives in this corridor:* tract demographic shares vs metro (Black, Hispanic, Asian, Indigenous, White), no-vehicle rate. *Why it matters:* triage rules that require an open 311 ticket may under-serve tenants who fear retaliation. This case **had** corroborating records. Cases without them were routed to the inspection-request pathway.

### 12.2 Batch audit for the deck (`sql/05_equity_audit.sql` + `scripts/run_equity_audit.py`)

The question the README wants answered with numbers: **does requiring an open 311 record penalize high-burden "silent distress" tracts?**

```sql
WITH t AS (SELECT * FROM `a4i_housing.v_tract_context`),
policy AS (
  SELECT census_tract_geoid,
         open_residential_311 > 0 AS prioritized_by_311_rule,
         (open_residential_311 <= 1
          AND severe_rent_burden_pct >= (SELECT metro_severe_rent_burden_pct FROM `a4i_housing.v_metro_baseline`)
          AND annual_nonpayment_filings_modeled >= (SELECT median_tract_nonpayment_filings_modeled FROM `a4i_housing.v_metro_baseline`)
         ) AS silent_distress
  FROM t
)
SELECT
  CASE WHEN p.prioritized_by_311_rule THEN 'A. Prioritized by open-311 rule'
       WHEN p.silent_distress THEN 'B. Silent distress (missed by 311 rule)'
       ELSE 'C. Other tracts' END AS grp,
  COUNT(*) AS tracts,
  SUM(a.renter_hh_rent_50_pct_plus_count) AS severely_burdened_households,
  ROUND(AVG(a.no_vehicle_rate) * 100, 1)        AS no_vehicle_pct,
  ROUND(AVG(a.audit_black_share) * 100, 1)      AS black_pct,
  ROUND(AVG(a.audit_hispanic_share) * 100, 1)   AS hispanic_pct,
  ROUND(AVG(a.audit_asian_share) * 100, 1)      AS asian_pct,
  ROUND(AVG(a.audit_white_share) * 100, 1)      AS white_pct
FROM policy p JOIN `a4i_housing.acs_tract_housing_tenure` a USING (census_tract_geoid)
GROUP BY grp ORDER BY grp;
```

**Deck slide:** a table of groups A/B/C, plus one sentence: *"An open-311-only rule would skip N tracts holding M severely rent-burdened households. Our navigator routes those cases to the inspection-request pathway and to funds without an open-case requirement, and we flag those tracts for mobile intake (X% no-vehicle)."* Fill in N, M and X from the real query output, and don't invent numbers.

---

## 13. Deploy, front end, tests

### 13.1 Deploy the agent (Cloud Run)

```bash
cd agent
adk deploy cloud_run \
  --project "$(gcloud config get-value project)" \
  --region us-central1 \
  --service_name sq7-stabilization-navigator \
  --with_ui \
  ./navigator
# Then grant the agent's service account: bigquery.dataViewer, bigquery.jobUser,
# bigquery.connectionUser (for AI.EMBED via us.a4i-vertex), aiplatform.user, run.invoker on sq7-mcp-toolbox.
# Set env vars on the service: TOOLBOX_URL, NAVIGATOR_MODEL, A4I_DATASET.
```

Deploy by **hour 2**, even if it's rough, so the front-end and story lanes work against a live URL.

### 13.2 Front end: "Intake Desk" (custom, scoped tight)

**Why custom:** the user is a paralegal under a clock, so a brief card beats a chat log. `adk web` stays as the fallback.

Layout (single page, no framework needed; plain HTML + JS calling the ADK API server's `/run_sse`):
- **Left (40%):** chat with the agent. A header strip shows a hearing countdown ("Mon 9:30 · 89 h").
- **Right (60%):** a live **Case File** card that updates from tool results. It has an Evidence tab (kept records in green, excluded records in grey with their reasons), a Funds tab (rule checkmarks), a Law tab and a Brief tab (renders the artifact, with Print / Copy buttons).
- **Footer badges:** `Real: ACS, 311` · `[Modeled]: filings` · `[Planted]: decoys filtered: 9/9`.

Mock the JSON schema of tool outputs from Section 8 on day zero, and swap in the live endpoint at hour 2.5.

### 13.3 Tests (rigor evidence, so screenshot them)

| Test | Assertion |
|---|---|
| `test_decoys.py` | Over 10 phrasings ("no heat", "black mold", "boiler", "sewage", "leak onto breaker"…), `DECOY-*` never appears in `kept`, and each one that appears in raw top-20 has an `excluded_because` reason |
| `test_eligibility.py` | Marisol fixture → 4× ELIGIBLE. Same fixture with no evidence → BUL-NY-02/04 INELIGIBLE |
| `test_fanout.py` | `SELECT COUNT(*) FROM v_tract_context` = 168, and every `quarters_aggregated` = 4 |
| `test_geoid.py` | All GEOIDs in tool outputs are `str` with length 11 |
| `test_no_audit_leak.py` | No `audit_` substring in any tool return payload or in the system prompt |
| Golden conversation | Section 3, run manually on the deployed URL before recording |

---

## 14. Antigravity prompts by lane

Moved to **Part A**. Every prompt is now a mission card (A3) and a workflow file in `.agent/workflows/`.

---

## 15. 4.5-hour timeline

Moved to **A6. Timeline by lane**.

---

## 16. Deck and 3-minute video script

**Deck (10 slides):** (1) Marisol's Monday. (2) The silo problem. (3) Metro choice + our 6-metro data audit. (4) Track: intake + funds. (5) Architecture (Section 4). (6) Vector search vs keywords, with the decoy caught. (7) Eligibility engine. (8) Equity audit numbers. (9) Real vs modeled data, plus limitations. (10) What's next (inspection-request agent, HUD AMI, transit).

**Video (≤3:00):**

| Time | Screen | Voiceover |
|---|---|---|
| 0:00–0:20 | Title card → photo-free text of Marisol's quote | "Thursday, 3:40 pm. Marisol's hearing is Monday. Her radiators have been cold for 18 days. The city knows. Her court file doesn't." |
| 0:20–0:35 | Data audit table | "We're working in New York, the only metro where open 311 records actually describe habitability hazards at scale." |
| 0:35–1:20 | Turns 1–2 live | "Dev types what Marisol said. Vector search finds inspector language like 'provide ready access to heating system.' Look: the #1 raw match is a closed, fixed boiler. Our rules drop it and say why." |
| 1:20–1:55 | Turns 3–4 | "Law, then money. Eligibility is computed by rules, not guessed by the model. Four programs, each check shown." |
| 1:55–2:15 | Turn 6 | "When the landlord's lawyer says it's fixed, the navigator says what the record can and can't prove." |
| 2:15–2:40 | Brief + equity audit | "The brief is ready for the attorney tonight. And we audit our own rule: requiring a 311 ticket would miss N high-burden tracts, so we route those families differently." |
| 2:40–3:00 | Architecture + stack badges | "ADK, Gemini, BigQuery vector search, MCP Toolbox, Cloud Run. Real ACS and 311 data, modeled filings labeled. Built so Marisol walks in Monday with a defense." |

---

## 17. Limitations we state out loud

- **100-block redaction:** records corroborate block conditions, not a specific unit or building. The attorney confirms with an HPD lookup by full address.
- **Modeled filings:** `court_eviction_filings` is modeled from county baselines. It's never a docket.
- **Data snapshot:** violation status is as of the 2026-11-01 data. Real-time HPD status needs the live HPD Open Data API (public domain, a possible BYOD addition).
- **FPL figures:** hardcoded guideline values must be updated yearly. AMI-based programs need HUD Income Limits (not loaded).
- **311 under-reporting:** absence of a record isn't absence of a hazard. The agent says so and routes accordingly.
- **Not legal advice:** statute text is summarized and the outputs are internal triage for attorney review.
- **Single metro:** the pipeline is metro-agnostic, but our thresholds (similarity 0.55, 800 m) were tuned on New York only.
