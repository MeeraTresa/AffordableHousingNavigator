# Affordable Housing Navigator: AI Eviction Defense Command Centre
## Presentation Brief & Technical Architecture Guide

---

## 1. Executive Summary & Problem Context

In urban housing courts across the United States, residential tenants facing nonpayment and eviction proceedings experience a severe structural disadvantage. In cities like New York, Chicago, and San Francisco, over **80% of landlords have legal representation**, while the vast majority of low-income tenants arrive at court without an attorney. 

Legal-aid clinics, tenant defense organizations, and housing counselors are overwhelmed:
- A caseworker or paralegal typically has **only 20 to 30 minutes per family** during a walk-in intake session.
- Tenants frequently arrive on Friday afternoon with an eviction hearing scheduled for **Monday morning at 9:30 AM**.
- Tenants bring fragmented information: a notice taped to their door, handwritten rent receipts, emotional distress, and apartments plagued by cold radiators, leaking ceilings, or toxic mold.
- The evidence required to mount a winning defense (affirmative defense of breach of the implied warranty of habitability, notice defect motions, and emergency rental assistance funds) is scattered across municipal 311 housing violation databases, state housing statutes, emergency relief program bulletins, and census tract displacement data.

**The Affordable Housing Navigator** is an **AI Eviction Defense Command Centre**. It is **not a conversational chatbot**; it is an integrated, multi-agent operations desk that coordinates six specialized AI subagents to corroborate tenant claims against public records, construct court-ready legal defense memos, and unlock financial aid before calendar call.

---

## 2. Why an AI Command Centre (Not Just a Chatbot)?

A generic chatbot provides generic advice: *"You should talk to a lawyer or tell the judge your heat is broken."* In housing court, generic advice leads directly to eviction.

A **Command Centre** provides an operational, coordinated investigative pipeline:
1. **Parallel Execution:** While the caseworker conducts a trauma-informed multilingual intake, forensic subagents run background vector searches against municipal code databases.
2. **Strict Guardrails & Deterministic Gating:** Vector search is treated solely as a candidate generator. High-stakes eligibility (e.g. income thresholds and whether rent relief funds can be legally released) is evaluated deterministically in Python rather than hallucinated by an LLM.
3. **Decoy Resilience:** Distinguishes active residential building violations from commercial storefront complaints and closed historical repairs.
4. **Evidentiary Honesty:** Clearly marks modeled data as `[Modeled]`, isolates audit columns, and explicitly defines what the public record *cannot* prove so attorneys know what physical evidence to gather.

---

## 3. System Architecture

```
                          ┌────────────────────────────────────────────────────────┐
                          │         COMMAND CENTRE COORDINATOR AGENT               │
                          │   (Orchestrates workflow, session state & triage)      │
                          └───────────────────────────┬────────────────────────────┘
                                                      │
         ┌──────────────────┬─────────────────────────┼─────────────────────────┬──────────────────┐
         │                  │                         │                         │                  │
         ▼                  ▼                         ▼                         ▼                  ▼
┌─────────────────┐ ┌─────────────────┐     ┌───────────────────┐     ┌──────────────────┐ ┌────────────────┐
│  SUBAGENT 1:    │ │  SUBAGENT 2:    │     │   SUBAGENT 3:     │     │   SUBAGENT 4:    │ │  SUBAGENT 5:   │
│  Intake &       │ │  Evidence       │     │   Statutory       │     │   Relief Fund    │ │  Tract Risk &  │
│  Multilingual   │ │  Corroborator   │     │   Defense         │     │   Allocator      │ │  Equity Audit  │
│  Interviewer    │ │  & Decoy Filter │     │   Strategist      │     │   (Eligibility)  │ │  (Neighborhood)│
└────────┬────────┘ └────────┬────────┘     └─────────┬─────────┘     └────────┬─────────┘ └───────┬────────┘
         │                   │                        │                        │                   │
         │ Structured Facts  │ Corroborated 311s      │ Affirmative Defenses   │ Qualified Funds   │ Risk & Transit
         │ (Arrears, Hazards)│ & Excluded Decoys      │ & Cure Deadlines       │ & Grant Caps      │ Barriers
         └───────────────────┴────────────────────────┼────────────────────────┴───────────────────┘
                                                      │
                                                      ▼
                                       ┌──────────────────────────────┐
                                       │         SUBAGENT 6:          │
                                       │    Brief & Action Plan       │
                                       │         Synthesizer          │
                                       │   (Attorney Brief + Packets) │
                                       └──────────────────────────────┘
```

---

## 4. Detailed Component Breakdown

### Component A: Core Data Foundations & Traps Resolved
The Command Centre operates directly on the initial commit datasets (`data/*.parquet` or Google BigQuery `a4i_housing`):
- **11-Character String GEOID Rule:** Census tract FIPS codes (e.g. `36061024500` in New York or `06075012300` in San Francisco) are strictly stored and queried as 11-character strings. Leading zeros are never truncated.
- **The 4× Fan-Out Join Trap:** `court_eviction_filings` contains four quarters of modeled court data per tract. Joining directly against `acs_tract_housing_tenure` would quadruple eviction counts. The loader (`data_loader.py`) pre-aggregates annual filings by `census_tract_geoid` before merging, producing exactly 168 rows for NYC and 42 rows for other metros.
- **Privacy & PII Protection:** Addresses are strictly coarsened to 100-block intervals (e.g., *"1000 Block of St. Nicholas Ave"*). No tenant names, unit numbers, or phone numbers enter prompts or logs.
- **Audit Demographic Isolation:** Demographic columns (`audit_*`) are strictly sequestered from retrieval, ranking, and prompts.

---

### Component B: Command Centre Coordinator (`CommandCentreCoordinator`)
- **Location:** `affordable_housing_navigator/core/agents/coordinator.py`
- **Purpose:** Acts as the central dispatcher. It initializes all six subagents, manages the shared state machine, and streams live telemetry events (`AgentEvent`) to the counselor's desk interface.
- **Execution Pipeline:**
  1. Calls `IntakeAgent` to parse raw intake facts into a validated `TenantCase`.
  2. Passes crisis narratives to `EvidenceCorroboratorAgent` for 311 vector search and decoy post-filtering.
  3. Hands corroborated records to `StatutoryDefenseAgent` and `ReliefFundMatcherAgent`.
  4. Queries `TractContextAgent` for neighborhood displacement indicators and courthouse transit barriers.
  5. Passes all validated state to `BriefCompilerAgent` to build the final court brief.

---

### Component C: Subagent 1 — Intake & Multilingual Interviewer (`IntakeAgent`)
- **Location:** `affordable_housing_navigator/core/agents/intake_agent.py`
- **Role:** Frontline client engagement & trauma-informed intake.
- **Capabilities:**
  - Real-time dual-language intake support (Spanish, Chinese, Bengali, Haitian Creole, English).
  - Uses Google GenAI (Gemini) for legal-aid contextual translations with built-in offline phrasebook fallbacks.
  - Distills emotional narrative into structured intake variables: 100-block, hearing date, claimed arrears, notice type, court index number, household size, and income.
  - Features Phase 2 voice interface hooks (`VoiceIntakeController`) for Speech-to-Text and Text-to-Speech audio streaming.

---

### Component D: Subagent 2 — Municipal Code Corroborator & Decoy Filter (`EvidenceCorroboratorAgent`)
- **Location:** `affordable_housing_navigator/core/agents/evidence_agent.py`
- **Role:** Municipal open-data forensic investigator.
- **Capabilities:**
  - Executes semantic vector search against 311 housing complaint narratives (`AI.EMBED` + `VECTOR_SEARCH` with brute force `top_k >= 20` or local TF-IDF semantic matcher).
  - **The Decoy Resilience Gate:** Applies the mandatory relational filter: `property_type = 'Residential' AND closed_date IS NULL`.
  - Rejects commercial storefront complaints and closed historical repairs (all 9 planted `DECOY-*` per metro).
  - Every rejected record receives an explicit human-readable rejection reason (e.g., *"Commercial property: Zero residential tenants protected under housing code"* or *"Closed – Abated on 2026-06-18: Violation cleared"*).
  - Classifies open residential violations by urgency (e.g. NYC HPD Class C Immediately Hazardous heat violations vs. Class B hazardous leaks).

---

### Component E: Subagent 3 — Statutory Defense & Counterclaim Strategist (`StatutoryDefenseAgent`)
- **Location:** `affordable_housing_navigator/core/agents/defense_agent.py`
- **Role:** Housing court defense analyst.
- **Capabilities:**
  - Maps corroborated hazards to municipal and state housing statutes across all 6 metros:
    - **New York:** Implied Warranty of Habitability (RPL § 235-b) rent abatement counterclaim; NYC Housing Maintenance Code (Admin Code § 27-2115) 24-hour Class C repair mandate; 14-day written rent demand condition precedent (RPAPL § 711(2)); Spiegel Law rent suspension defense (SSL § 143-b).
    - **San Francisco:** Cal. Civ. Code § 1941.1 & § 1942.4 rent demand bar; Cal. Civ. Code § 1942.5 180-day anti-retaliation defense; Proposition F Universal Right to Counsel.
    - **Chicago:** Municipal Code § 5-12-110 RLTO habitability remedies (rent withholding / repair-and-deduct); § 5-12-150 12-month retaliation presumption; Illinois 5-day notice and Cook County Early Resolution Program mediation.

---

### Component F: Subagent 4 — Emergency Relief Fund Allocator (`ReliefFundMatcherAgent`)
- **Location:** `affordable_housing_navigator/core/agents/relief_agent.py`
- **Role:** Financial triage & program eligibility coordinator.
- **Capabilities:**
  - Evaluates household size and income against 2026 Federal Poverty Guidelines (<=200% FPL) and Area Median Income (AMI) thresholds.
  - **The Habitability Gating Engine:** Evaluates the 4 relief bulletins per metro. Crucially, 2 of the 4 funds require `requires_open_habitability_case = True`.
  - When Subagent 2 corroborates open 311 habitability violations, Subagent 4 unlocks high-value habitability grants (e.g., Emergency Repair Program $5,500 grant and Local Law 136 Spiegel defense legal representation) that general applicants cannot access.
  - Automatically recommends fast-track pathways for NYC One Shot Deal ($15,000 cap) and CityFHEPS ($18,000 cap).

---

### Component G: Subagent 5 — Neighborhood Displacement & Equity Auditor (`TractContextAgent`)
- **Location:** `affordable_housing_navigator/core/agents/tract_agent.py`
- **Role:** Spatial intelligence & access barrier monitor.
- **Capabilities:**
  - Executes fan-out-safe tract joins against ACS tenure and aggregated court filings.
  - Contextualizes eviction pressure: identifies if tenant's census tract suffers severe rent burden above the metro median (e.g., 32.8% vs. 24.4% metro median in Washington Heights).
  - **Courthouse Transit Barrier Alert:** Detects when `no_vehicle_rate > 70%` (91.6% in Washington Heights tract `36061024500`). Warns the caseworker to provide transit route instructions and urge arrival 45 minutes early to avoid default judgment at calendar call.
  - Labeled honestly as `[Modeled]` data.

---

### Component H: Subagent 6 — Attorney Brief & Action Plan Synthesizer (`BriefCompilerAgent`)
- **Location:** `affordable_housing_navigator/core/agents/brief_agent.py`
- **Role:** Executive packet compiler.
- **Capabilities:**
  - Compiles the court-ready **Tenant Stabilization Brief & Legal Defense Memo**.
  - Generates the actionable **Tenant Checklist** (photos of radiators, thermometer logs, rent receipts).
  - **Evidentiary Boundary Definition:** Articulates the boundary between what the municipal public record proves (city code violations on block) and what the tenant and attorney must document for trial (unit-specific photos, notices to super).

---

### Component I: Interactive Command Centre Dashboard
- **Location:** `affordable_housing_navigator/app/main.py`
- **Role:** Single-page operations desk for paralegals and caseworkers.
- **Features:**
  - **Top Nav:** Metro corridor switcher (New York, San Francisco, Chicago, Austin, Baton Rouge, Cincinnati) and 1-click Demo Case loader.
  - **Telemetry Strip:** Real-time indicator displaying the status of all 6 active subagents.
  - **Column 1:** Live multilingual interview chat, translation toggle, structured intake form, and live telemetry log.
  - **Column 2:** Corroborated 311 evidence table and Decoy Rejection audit trail.
  - **Column 3:** Statutory defense matrix, emergency relief funds pipeline with eligibility badges, and neighborhood displacement stat box.
  - **Modal:** Printable, exportable Markdown Tenant Stabilization Brief.

---

## 5. Walkthrough of the Golden Demo Case (Marisol)

### Case Background
- **Tenant:** Marisol (Spanish-speaking mother of two, daughter Daniela has asthma).
- **Address:** 1000 Block of St. Nicholas Ave, Washington Heights, New York (Tract `36061024500`).
- **Hearing:** Monday at 09:30 AM in Manhattan Housing Court (Index `LT-029481/26`).
- **Claimed Arrears:** $3,350.00.
- **Household:** 3 persons, $31,000 annual income (<=200% FPL threshold is $53,300).
- **Physical Hazards:** Radiators freezing cold since early November; runs gas oven for warmth; black mold around tub; water leaking through bathroom wall from upstairs neighbor.

### Multi-Agent Execution Results
1. **`IntakeAgent`:** Extracted facts, translated welcome greeting into Spanish, validated arrears and household income.
2. **`EvidenceCorroboratorAgent`:**
   - Vector search returned 20 candidates.
   - **Kept 13 open residential complaints** on block: Class C heat/hot water violations (`NYC-19346259`, `NYC-19346349`) and Class B water intrusion/mold.
   - **Excluded 7 candidates**, including planted decoys `DECOY-NEWY-01` (Commercial storefront) and `DECOY-NEWY-04` (Closed abated repair).
3. **`StatutoryDefenseAgent`:** Mapped 3 defenses:
   - NY RPL § 235-b: Breach of Implied Warranty of Habitability (rent abatement).
   - NYC Admin Code § 27-2115: Class C heat violations must be cured within 24 hours.
   - NY RPAPL § 711(2): 14-day written rent demand condition precedent.
4. **`ReliefFundMatcherAgent`:** Evaluated 4 funds:
   - **QUALIFIED:** Emergency Repair Program ($5,500 grant) — *Unlocked by corroborated 311 evidence!*
   - **QUALIFIED:** NYC Local Law 136 Right to Counsel ($4,000 grant + assigned attorney) — *Unlocked by corroborated 311 evidence!*
   - **QUALIFIED:** HRA One Shot Deal (Clears arrears up to $15,000).
   - **QUALIFIED:** CityFHEPS Prevention Pathway (Up to $18,000 arrears).
5. **`TractContextAgent`:**
   - Census Tract `36061024500`: 32.8% severe rent burden (Metro median: 24.4%).
   - Modeled filings: 414 / yr (Metro median: 196).
   - **Courthouse Transit Barrier Alert:** 91.6% of households lack a private car. Advised early subway transit departure to prevent calendar call default judgment.
6. **`BriefCompilerAgent`:** Produced a 102-line court-ready legal defense packet and tenant evidentiary checklist.

---

## 6. Verification and Test Suite

The Command Centre includes an automated pytest suite covering all domain logic and guardrails:

```bash
# Run the complete test suite
PYTHONPATH=. /config/.venv/bin/pytest affordable_housing_navigator/tests/ -v
```

### Verified Test Cases:
1. `test_command_centre_pipeline_execution`: Validates coordinator executes all 6 subagents and aggregates telemetry.
2. `test_all_planted_decoys_are_filtered_out`: Validates that all 54 planted decoys across all 6 metros are filtered out with explicit reasons.
3. `test_vector_search_rejects_decoys_on_heat_query`: Verifies vector search rejects commercial/closed records on heat queries.
4. `test_tract_counts_match_expected`: Validates fan-out safety (168 NY tracts, 42 for other metros).
5. `test_geoid_is_always_11_char_string`: Validates 11-char string format and zero-preservation.
6. `test_habitability_gate_locks_and_unlocks_funds`: Validates deterministic unlocking of habitability-contingent relief funds.
7. `test_full_marisol_intake_flow`: End-to-end integration test of intake, evidence retrieval, defenses, and brief compilation.

---

## 7. Running the Command Centre Web Application

To launch the interactive Command Centre desk:

```bash
# Start FastAPI application with Uvicorn
PYTHONPATH=. /config/.venv/bin/uvicorn affordable_housing_navigator.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Then open `http://127.0.0.1:8000` in the browser:
- Click **"Load Marisol Monday Case"** to watch the multi-agent pipeline execute in real time.
- View live subagent telemetry logs in the terminal ticker.
- Inspect the Corroborated Evidence radar, Decoy Audit trail, and Relief Funds pipeline.
- Click **"Attorney Brief"** to export or print the generated defense packet.

---

## 8. Google Maps Building Identification & Privacy Architecture

The Navigator includes a dedicated spatial resolution module ([`building_mapper.py`](file:///config/Desktop/AgentsForImpact/AffordableHousingNavigator/affordable_housing_navigator/core/building_mapper.py)):

### Privacy-Preserving Address Normalization
- **Strict Anti-PII Filter:** In legal aid clinics, tenants often inadvertently include apartment, unit, or floor numbers (e.g. `1000 St. Nicholas Ave Apt 4B`). 
- The normalizer automatically parses and removes unit designations (`Apt`, `Unit`, `#`, `Fl`, `Suite`), preserving tenant anonymity while retaining the exact building and 100-block footprint.

### Spatial Identification & Google Maps Integration
- **Automated Centroid Lookup:** Queries the municipal 311 parcel dataset and Census ACS tract boundaries to identify the building's exact latitude and longitude (`40.836626, -73.942098` for Washington Heights).
- **Interactive Embed:** Embeds a zero-API-key Google Maps view directly into the counselor's intake desk.
- **One-Click Street View Verification:** Generates direct links for Google Maps navigation and Google Street View so caseworkers and attorneys can inspect the building exterior and verify physical conditions.

---

## 9. Conversational Caseworker Co-Pilot & Dynamic Defense UI Generator

In response to caseworker needs in high-volume legal clinics, the Navigator introduces an **AI Conversational Co-Pilot** paired with a **Dynamic UI Generator**:

### 1. Conversational Co-Pilot Architecture (`copilot.py`)
- **Natural Language Dialogue:** Caseworkers can converse naturally with the co-pilot (e.g. *"Marisol is here. Hearing next Monday, rent arrears $3,350, radiators freezing and mold. What defenses and relief can we get?"*).
- **Automated Intake & Entity Extraction:** Parses building street address, hearing dates, claimed arrears, and habitability conditions in real-time.
- **Procedural Coaching:** Supplies instant statutory analysis (RPL § 235-b, Class C heat violation 24-hr cure rules, Spiegel Law).
- **Proactive Suggestions:** Recommends next steps via clickable golden-path prompt pills.

### 2. Dynamic UI Generation
- **On-Demand Defense Workspace:** When the caseworker speaks with the agent or clicks **"Generate Defense UI"**, the workspace dynamically synthesizes and renders:
  1. **Ticking Hearing Countdown Clock:** Live countdown to the calendar call (e.g., `5d 11h 38m remaining`).
  2. **Interactive Map with 800m Statutory Buffer:** Centered on the building centroid (stripping apartment numbers for privacy) with an 800m search radius, verified green 311 markers, and transparent red decoy markers.
  3. **Affirmative Defense Answer Checklist:** Interactive checkboxes ready for drafting court pleadings.
  4. **Emergency Relief Fund Pipeline:** Live qualification badges for One Shot Deal ($15k), CityFHEPS ($18k), Emergency Repair ($5.5k), and Right to Counsel ($4k).
  5. **Displacement Pressure & Transit Warning:** Severe rent burden radar (32.8% vs 24.4% metro) and courthouse transit warning (91.6% transit reliance).

### 3. Multimodal Action Drawer (`+` Button)
- **📸 Inspect Hazard Photo:** Forensic severity analysis (Class A/B/C) with mandatory Evidentiary Boundary disclaimer.
- **📄 Extract Notice of Petition (OCR):** Auto-extracts court index numbers, arrears amounts, and hearing dates from photos of court papers.
- **🎙️ Voice Audio Intake:** Speech-to-facts intake transcription.

---

## 10. Hearth · Senior Housing-Court Intake Partner & Living Brief Workspace

Inspired by the civic design and paralegal persona from the `a4i` repository, the Navigator integrates the **Hearth & Living Brief UI**:

### Civic Identity & Public Sector Theme
- **Typographic System:** USWDS Public Sans for UI elements, IBM Plex Mono for municipal IDs, and Source Serif 4 for formal court paper documents.
- **HearthMark:** Civic house-with-doorway mark SVG in civic blue (`#1d4ed8`), replacing generic chatbots with a dignified institutional symbol.
- **Top Bar Case Line:** Real-time urgency monitor (`1000 Block St. Nicholas Ave · Mon 9:30 AM · $3,350 · 5d 11h left`), turning into an urgent red badge if the hearing is approaching.

### Hearth Persona Invariants (`copilot.py`)
- **Senior Housing-Court Paralegal:** Colleague partnering with intake caseworkers at 111 Centre St (Manhattan Housing Court).
- **Findings-First & Shorthand:** Leads with conclusions, fluent in RPAPL § 711(2), RPL § 235-b, Spiegel law, and Class C 24h repair windows. Zero filler.
- **Mandatory Closing Invariant:** Concludes substantive replies with:
  `**What the record can't prove yet:** [One specific fact needed]`

### Two-Column Architecture
- **Left 58% (Conversation with Hearth):**
  - Interactive chat stream with inline kept evidence chips (`[✓ Kept · Class C · Heat]`), struck-through decoys (`[~~DECOY-NEWY-05~~ Closed]`), and fund checklist lines.
  - Dynamically updating suggested next question chips (`⚡ Marisol Intake`, `🔍 Why set aside look-alike?`, `⚖️ What law covers this?`).
  - Multimodal composer with `+` drawer (📸 Photo Vision, 📄 Notice OCR, 🎙️ Voice Intake).
- **Right 42% (Living Tenant Stabilization Brief):**
  - Styled as formal New York City Civil Court Housing Part legal paper (`CIVIL COURT OF THE CITY OF NEW YORK · HOUSING PART`).
  - Progressively drafts and populates live as the caseworker and Hearth converse.
  - Embedded Leaflet 800m habitability search map with Google Maps and Google Street View links.
  - One-click print/PDF clean stylesheet (`@media print` prints only the formal brief).

---

## 11. Database Persistence, Living Brief Editing & Caseworker Dashboard

To support enterprise legal-aid operations, the platform integrates **Case Persistence**, **In-Place Brief Editing**, and a dedicated **Caseworker Case Management Dashboard**:

### 1. Database Storage & Firebase Firestore Schema Mapping
- **Firestore Document Model:** Documented in `affordable_housing_navigator/schema/firestore_schema.json` matching the Firestore `tenant_cases` collection:
  - `case_id`: Unique identifier (e.g. `case-lt-029481-26`).
  - `court_index_number`: e.g. `LT-029481/26/NY`.
  - `tenant_name`: Masked for privacy (e.g. `Marisol V.`).
  - `block_address`: Strict 100-block privacy (Rule 7: No apartment or unit numbers).
  - `hearing_date` & `hearing_time`: Hearing schedule (e.g. `2026-11-23 09:30 AM`).
  - `claimed_arrears`: Landlord claimed amount (`$3,350.00`).
  - `brief_markdown`: The complete living defense brief document.
  - `brief_edits_count`: Incremental version counter tracking caseworker modifications.
  - `caseworker_notes`: Internal attorney/paralegal notes.
- **Embedded Document Store:** High-performance local SQLite datastore (`data/cases.db`) with zero-configuration setup and SQL indexing, ready to sync with Google Cloud Firestore.

### 2. In-Place Living Brief Editing & Version Control
- Caseworkers can toggle between **"View Clean Court Brief"** and **"Edit Brief"**.
- In edit mode, the brief transforms into an interactive legal worksheet with syntax-friendly editing and caseworker notes.
- Clicking **"Save Changes to DB"** triggers `POST /api/cases/{case_id}/brief`, writing changes to the database and incrementing the version badge (`v1`, `v2`, etc.).

### 3. Caseworker Case Management Dashboard ("The Next App")
- Accessible via the **[ 📋 Cases Dashboard ]** navigation tab or `/dashboard`.
- **KPI Metrics:**
  - Active Tenant Cases count.
  - Critical Hearings This Week (imminent calendar calls).
  - Total Claimed Arrears Managed.
  - Emergency Relief Funds Matched.
- **Search & Filtering:**
  - Real-time search across tenant names, court index numbers, and 100-block addresses.
  - Status filters: `All`, `Hearing Ready`, `Active Intake`, `Brief Finalized`.
- **Actions:**
  - **"Open Brief"**: Loads the case into Hearth's conversational desk and living brief pane.
  - **"Create New Intake"**: Launches a modal to input a new tenant and immediately start the defense analysis.
