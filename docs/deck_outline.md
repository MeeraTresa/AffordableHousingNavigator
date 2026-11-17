# Stabilization Navigator: Pitch Deck Outline (10 Slides)

**Team:** Squad 7 · Agents for Impact 2026  
**Corridor:** New York City Metro (`a4i_housing`)  
**Track:** Intake Triage & Emergency Relief Matching  

---

### Slide 1: Marisol's Monday
- **Headline:** Thursday, 3:40 PM: Court is Monday at 9:30 AM.
- **Bullets:**
  - Marisol arrives at a legal-aid clinic with a 3-day nonpayment eviction notice for $3,350 in arrears.
  - Her radiators have been stone-cold since early November; toxic black mold surrounds the bathtub and water leaks near the fuse box.
  - The city's housing agency *already inspected and knows* about these hazards, but her court file contains zero evidence.
- **Visual:** Simple split intake card showing Marisol's emergency notice next to a countdown clock ("89 hours to hearing").

---

### Slide 2: The Silo Problem
- **Headline:** A Corroboration & Triage Crisis Under a Running Clock
- **Bullets:**
  - Tenants routinely forfeit non-waivable statutory defenses and $15,000+ stabilization grants in 5-minute hallway settlements.
  - Right-to-counsel clinics have waiting rooms full of families and minutes per intake to find corroborating public records.
  - Municipal 311/HPD records, court dockets, and emergency funding guidelines sit in disconnected operational silos.
- **Visual:** Diagram of three disconnected silos (Courthouse Docket, 311 Municipal Database, Emergency Relief Guidelines) failing to talk before Monday morning.

---

### Slide 3: Metro Choice & 6-Metro Data Audit
- **Headline:** Selecting New York: The Only Metro with Scale in Open 311 Habitability
- **Bullets:**
  - Audited all 6 challenge metros: Baton Rouge carries 27.2% severe rent burden but only 10 open residential 311s; SF has 140 open 311s across 42 tracts.
  - New York corridor provides 168 census tracts, 437,111 renter households (25.2% severe burden), and 165 open residential 311 complaints.
  - Demonstrates why open-311 triage rules alone risk penalizing "silent distress" tracts where tenants fear calling city inspectors.
- **Visual:** Data audit comparison table highlighting New York, San Francisco, Chicago, Austin, Baton Rouge, and Cincinnati metrics.

---

### Slide 4: Track Selection: Intake Triage & Relief Matching
- **Headline:** Connecting Public Building-Code Files to Emergency Defense Before Trial
- **Bullets:**
  - **Input:** Tenant's everyday natural-language crisis narrative and 100-block location.
  - **Engine:** Semantic vector candidate generation, hard relational filtering (rejecting commercial and abated decoys), and deterministic rules engine.
  - **Output:** Actionable Tenant Stabilization Brief pairing corroborating 311 evidence, statutory defenses, and $42,500 in matched relief capacity.
- **Visual:** Input-to-Output pipeline card: Citizen Intake &rarr; Stabilization Navigator &rarr; Attorney Brief.

---

### Slide 5: System Architecture
- **Headline:** Enterprise-Grade Civic AI on Google Cloud
- **Bullets:**
  - **ADK & Gemini 2.5 Flash:** Agent runtime managing multi-turn case state and structured reasoning.
  - **BigQuery Vector Search:** `gemini-embedding-2` generating 768-dim embeddings with brute-force cosine distance (`ML.DISTANCE`).
  - **Cloud Run MCP Toolbox:** Parameterized, fan-out-safe SQL tools deployed with `--min-instances=1` to eliminate cold starts.
- **Visual:** Complete architectural flow diagram (Frontend &rarr; ADK Cloud Run &rarr; MCP Toolbox &rarr; BigQuery `a4i_housing`).

---

### Slide 6: Vector Search vs. Keywords: Catching the Decoys
- **Headline:** Semantic Retrieval Generates Candidates; Hard Relational Rules Decide
- **Bullets:**
  - Citizen phrasing ("radiators stone cold") never matches statutory codes ("HPD Class C heating system access").
  - Keyword search retrieves dangerous traps; raw vector similarity ranked a closed boiler repair (`DECOY-NEWY-04`, sim 0.80) #1.
  - Our relational post-filter (`property_type = 'Residential' AND closed_date IS NULL`) caught 9/9 planted decoys with human-readable rationale.
- **Visual:** Side-by-side screenshot showing Raw Top-5 candidates with Decoys highlighted vs. Kept Evidence cards in green and Excluded Decoys in grey.

---

### Slide 7: Deterministic Eligibility Engine
- **Headline:** Code Computes Eligibility; Gemini Explains the Verdicts
- **Bullets:**
  - LLMs hallucinate income limits and guideline thresholds; Python rules (`tools/funds.py`) evaluate pass/fail with absolute precision.
  - Marisol's household (3 people, $31,000 income, court index number, 3 open HPD violations) evaluated against 4 NYC stabilization programs.
  - 4× ELIGIBLE verdicts produced: Right to Counsel ($4k), ERP Clinic ($5.5k), HRA One Shot Deal ($15k), and CityFHEPS Arrears ($18k).
- **Visual:** Relief Funds UI tab displaying pass/fail checkmarks (✅/❌) and max award amounts.

---

### Slide 8: Post-Output Equity Audit
- **Headline:** Uncovering Silent Distress: Auditing Our Own Triage Policy
- **Bullets:**
  - Isolated `audit_*` demographic columns completely from retrieval and ranking; audited across all 168 New York tracts.
  - **Finding:** An open-311-only rule would skip **37** tracts holding **33,980** severely rent-burdened households with **74.9%** zero-vehicle rates.
  - **Policy Mitigation:** Navigator routes uncorroborated cases to emergency inspection intake and general relief funds (One Shot Deal) rather than denying aid.
- **Visual:** Table of Groups A, B (Silent Distress), and C with tract counts, severely burdened households, and vehicle access rates from `docs/equity_audit_results.md`.

---

### Slide 9: Honest Data Provenance & Real-World Boundaries
- **Headline:** Knowing What the City Record Cannot Prove
- **Bullets:**
  - **Data Provenance:** ACS housing tenure and 311 complaints are real public records; court eviction filings are explicitly labeled `[Modeled]`.
  - **Evidentiary Limits:** 100-block records corroborate block/cluster conditions, not interior apartment leases or unit inspections.
  - **Live Controversy:** When landlord counsel claims the boiler was repaired last week, the navigator flags that snapshot data cannot verify recent repairs and petitions for an HPD re-inspection.
- **Visual:** Evidentiary boundary card illustrating the boundary between public municipal records and tenant unit leasehold facts.

---

### Slide 10: Future Roadmap & Impact
- **Headline:** From Thursday Intake to Sustainable Housing Stability
- **Bullets:**
  - **Automated 311 Inspection Drafter:** Secondary agent to interview tenants and auto-submit structured municipal code complaints with photo checklists.
  - **Dynamic Transit Routing:** Integration with GTFS subway/bus schedules to guarantee tenants reach 111 Centre Street before 9:30 AM default call.
  - **Multi-Jurisdiction Expansion:** Portable architecture ready for Chicago, San Francisco, Austin, and Cincinnati corridor data.
- **Visual:** Product vision mockup showing mobile intake checklist and Google Maps transit routing card.
