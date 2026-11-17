# Hackathon Demo Runbook & Preparation Guide

**Project:** Affordable Housing Stability & Eviction Prevention Navigator (`a4i_housing`)  
**Hackathon:** Agents for Impact 2026  
**Target Scenario:** Marisol's Monday (Northern Manhattan / Washington Heights Intake)  
**Target Runtime:** ≤ 3:00 minute live demonstration  

---

## 1. Demo Overview & Narrative Arc

### The Persona
* **Tenant:** Marisol (34, home health aide, 2 children: Leo 9, Daniela 6)
* **Location:** 1000 block of St. Nicholas Ave, Washington Heights, Manhattan (Tract `36061024500`)
* **Crisis:** Hours cut; owes **$3,350** in rent arrears. Nonpayment hearing is **Monday 9:30 AM** in Manhattan Housing Court.
* **Conditions:** Radiators cold for 18 days (running oven for heat); black mold around bathtub; water leaking through bathroom wall. Daughter's asthma worsening.
* **The Silo:** The city already has open code violations on record (`NYC-19346259`, `NYC-19346354`, `NYC-19346353`), but none of this is in her housing court file.

### Key Architectural Takeaways for Judges
1. **Vector Search is a Candidate Generator, Not the Judge:** Semantic search finds inspector phrasing, but strict post-filtering drops commercial and closed cases (catching planted traps / decoys).
2. **Rules Decide Eligibility, LLM Explains:** Python tools evaluate statutory requirements and fund caps deterministically. The LLM communicates without hallucinating eligibility.
3. **Strict Equity Boundaries:** `audit_*` demographic columns are excluded from all prompts, embeddings, and ranking. Audits run post-output only.
4. **Honest Data Provenance:** Public ACS & 311 data are real; eviction court filings are explicitly labeled `[Modeled]`.

---

## 2. Pre-Flight Checklist (15 Minutes Before Demo)

| Check | Item | Status / Verification Command |
|---|---|---|
| [ ] | **GCP Project & Services** | `gcloud config get-value project` matches configured deployment project. |
| [ ] | **Cloud Run MCP Toolbox** | Service `sq7-mcp-toolbox` is up with `--min-instances=1` (avoids cold start). |
| [ ] | **Cloud Run Agent Endpoint** | ADK Agent service `sq7-stabilization-navigator` responds to `/run_sse` or `adk web` is active. |
| [ ] | **BigQuery Datasets & Views** | `v_tract_context` (168 NY tracts, 4 quarters aggregated) and `v_metro_baseline` exist in `a4i_housing`. |
| [ ] | **Embeddings & Vector Search** | `gemini-embedding-2` endpoint active on connection `us.a4i-vertex`. |
| [ ] | **Decoy Filter Integrity** | Decoy cases (`DECOY-NEWY-01` through `DECOY-NEWY-09`) are detected and rejected with explicit reasons. |

---

## 3. The 7-Turn Live Demo Golden Path

Run these exact turns sequentially. Keep output cards and filter stages clearly visible.

### Turn 1: Case Intake & Public Record Corroboration
* **Paralegal Types:**
  > *"New intake. Tenant on the 1000 block of St. Nicholas Ave, Manhattan. Nonpayment hearing Monday 9:30. Radiators cold since early Nov, black mold around the tub, water coming through the bathroom wall. Anything open on her block?"*
* **Expected Agent Action:** Calls `open_case` → `search_habitability_evidence` (queries 3 hazards, top_k 20) → post-filter.
* **What Must Show on Screen:**
  - 3+ corroborating open residential records (`NYC-19346259` Class C heat, `NYC-19346354` Class A mold, `NYC-19346353` Class B water leak).
  - Explicit count badge: **"Excluded: 4 records"** (with reasons).

### Turn 2: Demonstrating the Decoy Trap
* **Paralegal Types:**
  > *"Why did you drop that boiler record? It looked like an exact match."*
* **Expected Agent Action:** Reads exclusions from case file.
* **What Must Show on Screen:**
  - `DECOY-NEWY-04`: `"Closed – Abated: landlord replaced boiler, inspector verified."`
  - `DECOY-NEWY-01`: `"Commercial storefront, zero residential tenants."`

### Turn 3: Statutory Defenses
* **Paralegal Types:**
  > *"What law covers this?"*
* **Expected Agent Action:** Calls `match_statutes`.
* **What Must Show on Screen:**
  - **RPL § 235-b** (Warranty of Habitability abatement).
  - **NYC Admin Code § 27-2115** (Class C heat hazard required 24h repair).
  - **RPAPL § 711(2)** notice check: *"Ask whether tenant received 14-day written demand (the public record cannot verify this)."*

### Turn 4: Relief Funds Eligibility
* **Paralegal Types:**
  > *"Household of 3, about $31k a year, she has the court index number. Her daughter has asthma that's gotten worse."*
* **Expected Agent Action:** Calls `update_case` → `match_relief_funds`.
* **What Must Show on Screen:**
  - Ranked funds with rule checkmarks:
    - Right to Counsel + Class C defense: ✅ **Eligible** (≤200% FPL)
    - One Shot Deal (HRA Emergency Assistance): ✅ **Eligible** ($3,350 arrears < $15k cap)
    - CityFHEPS: ✅ **Eligible** (has court index number)
  - Clear note that asthma is highlighted for the attorney but **not** used as an algorithmic eligibility metric.

### Turn 5: Neighborhood Context & Eviction Pressure
* **Paralegal Types:**
  > *"How bad is this neighborhood compared to the city?"*
* **Expected Agent Action:** Calls MCP Toolbox `get_tract_context` (Census Tract `36061024500`).
* **What Must Show on Screen:**
  - Severe Rent Burden: **32.8%** (vs. Metro 25.2%)
  - Modeled Annual Filings: **414** `[Modeled]` (vs. Metro tract median 196)
  - Vehicle Access: **91.6%** without a vehicle (access risk for Monday hearing).

### Turn 6: Rebutting Landlord Claims & Evidentiary Boundaries
* **Paralegal Types:**
  > *"Landlord's lawyer says the boiler was fixed last week."*
* **Expected Agent Action:** Checks latest public record snapshot date.
* **What Must Show on Screen:**
  - Points out public record shows Class C violation still open as of 2026-11-01 snapshot.
  - States clearly: *"Fixed-or-not cannot be verified from historical public data alone. Request HPD re-inspection and contemporaneous tenant photo log."*

### Turn 7: Tenant Stabilization Brief & Equity Audit
* **Paralegal Types:**
  > *"Draft the brief for the attorney."*
* **Expected Agent Action:** Calls `finalize_brief`.
* **What Must Show on Screen:**
  - Formatted **Tenant Stabilization Brief** (Corroborating Records, Statutes, Relief Match, Evidentiary Boundaries, Intake Memo).
  - **Equity Audit** block automatically rendered by code at the bottom.

---

## 4. Video Recording Timing Guide (≤ 3:00 Total)

| Timestamp | Screen Display | Narration Talking Points |
|---|---|---|
| **0:00 – 0:20** | Title card + Marisol case quote | "Thursday 3:40 PM. Marisol's eviction hearing is Monday morning. Her radiators have been cold for 18 days. The city knows; her court file doesn't." |
| **0:20 – 0:35** | Data architecture & Metro table | "We built the navigator for New York City, connecting real-time municipal 311 habitability complaints with court baselines." |
| **0:35 – 1:20** | Live turns 1 & 2 (Evidence & Decoys) | "The paralegal enters the tenant's words. Vector search finds technical violations, while our filter catches commercial decoys and closed repairs." |
| **1:20 – 1:55** | Live turns 3 & 4 (Law & Funds) | "Law, then funding. Rules compute eligibility deterministically—four relief funds matched, including NYC Right to Counsel." |
| **1:55 – 2:15** | Live turn 6 (Evidentiary boundaries) | "When the landlord claims it's resolved, the navigator acknowledges the evidentiary boundary: public records cannot prove inside-unit repairs." |
| **2:15 – 2:40** | Live turn 7 (Brief & Equity Audit) | "In 20 minutes, Dev hands the supervising attorney a complete Tenant Stabilization Brief with a code-rendered equity audit." |
| **2:40 – 3:00** | Architecture diagram & closing | "Powered by Google Cloud, BigQuery Vector Search, ADK, and Gemini. Built so tenants walk into court with an actual defense." |

---

## 5. Fallback & Troubleshooting Procedures

1. **If Cloud Run Agent cold-starts or times out:**
   - Fallback to local development runner: `cd agent && adk web` and connect to `http://localhost:8000`.
2. **If BigQuery Vector Search latency exceeds 5s:**
   - Confirm brute-force option is set in the query: `options => '{"use_brute_force":true}'`.
3. **If MCP Toolbox endpoint is unreachable:**
   - Verify IAM permission `run.invoker` on service account `sq7-toolbox-sa` or invoke local direct client.
