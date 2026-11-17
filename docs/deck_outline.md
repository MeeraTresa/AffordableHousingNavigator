# Stabilization Navigator: 10-Slide Pitch Deck Outline
**Challenge 02 · Affordable Housing Stability & Eviction Prevention Navigator**

---

### Slide 1: Title & Hook
- **Title:** Stabilization Navigator: An AI Co-Pilot for Housing Intake
- **Subtitle:** Turning 100-Block Municipal Code Violations into Imminent Eviction Defenses
- **Hook:** "Thursday, 3:40 pm. Marisol owes $3,350 and faces a Monday morning eviction hearing. Her radiators have been cold for 18 days. The city has it on record. Her court docket doesn't."

---

### Slide 2: The Administrative Silo Problem
- Housing court nonpayment cases move in days; code enforcement operates in weeks.
- Families with documented uninhabitable living conditions (no heat, toxic mold, raw sewage) face eviction without their habitability rights because courts and code-enforcement databases never talk.
- Paralegals have ~20 minutes per intake and 11 families waiting.

---

### Slide 3: Rigor & Judgment — Why New York?
- **6-Metro Data Audit:** Before writing code, we analyzed open habitability complaints across all 6 challenge metros:
  - *Austin & Cincinnati:* 0 open habitability narratives (mostly trash / tall grass).
  - *New York:* 165 open complaints with 63 serious HPD Class A/B/C habitability violations and 25.2% metro severe rent burden.
- We chose New York because its municipal records actually contain the facts needed to corroborate legal defenses.

---

### Slide 4: Track & Solution Scope
- **Track:** ⚖️ *Today at intake* combined with *🛟 emergency relief fund matching*.
- **Role:** An active intake co-pilot for paralegals and housing counselors (not a passive dashboard or basic query box).
- Generates a **Tenant Stabilization Brief** under 5 minutes before Monday court.

---

### Slide 5: System Architecture
- **Agent Framework:** Google ADK with Gemini (`gemini-2.5-flash`).
- **Semantic Candidate Generator:** BigQuery `VECTOR_SEARCH` with `AI.EMBED` (`gemini-embedding-2`) using brute force cosine similarity.
- **Domain Layer:** Deterministic Python tools for decoy filtering, statutory analysis, and fund qualification.
- **Enterprise Integration:** Google-managed MCP Toolbox for Databases on Cloud Run for parameterized neighborhood SQL lookups.

---

### Slide 6: Vector Search vs. Fragile Keywords (Decoy Defense)
- **The Gap:** Tenants say *"radiators are freezing"*; inspectors write *"§ 27-2031 PROVIDE READY ACCESS TO HEATING SYSTEM"*. Semantic search bridges this vocabulary gap.
- **The Differentiator:** Vector search is only a candidate generator, not the verdict.
- **Planted Decoy Defense:** All 9 planted decoys (`DECOY-*`) are rejected by deterministic post-filters with clear explanations:
  - Dropping commercial storefronts (`DECOY-NEWY-01`).
  - Dropping closed/abated repairs (`DECOY-NEWY-04`).
  - Dropping "no violation found" decoys (`DECOY-NEWY-07`).

---

### Slide 7: Deterministic Eligibility Engine
- **LLM explains, Python decides:** No hallucinated approvals.
- Evaluates income against HHS Federal Poverty Levels (FPL) and program caps.
- Matches requirements for NYC programs:
  - *Right to Counsel (Local Law 136)*: ≤200% FPL + open HPD habitability violation.
  - *HRA One Shot Deal*: Emergency arrears clearance up to $15,000.
  - *Emergency Repair Program (ERP) Clinic*: Open heat/mold violations up to $5,500.
  - *CityFHEPS Prevention*: Court index number + rent arrears.

---

### Slide 8: Post-Output Equity Audit
- **Auditing Our Own Rules:** Does requiring an open 311 record penalize high-burden communities?
- **Empirical Findings across 168 NYC Tracts:**
  - Group A (Prioritized by 311 rule): 38 tracts, 29,117 severely rent-burdened households.
  - Group B ("Silent Distress"): **37 tracts holding 33,980 severely rent-burdened households** that would be completely missed by an open-311 requirement.
- **Our Policy Adaptation:** Cases in silent distress tracts without 311 records are automatically routed to the proactive inspection-request pathway and to funds that do not require an open code violation. We flag these tracts for mobile intake (74.9% no-vehicle rate).

---

### Slide 9: Honest Data & The Evidentiary Boundary
- **Clear Data Labeling:**
  - `Real`: ACS housing tenure and 311 complaint narratives.
  - `[Modeled]`: Court eviction filings (aggregated 4 quarters/tract to avoid 4× fan-out).
  - `[Planted Case]`: Decoy records labeled transparently.
- **The Evidentiary Boundary:** The public record is 100-block redacted; it proves neighborhood/building cluster conditions, not the tenant's individual apartment. The brief tells the attorney exactly what must still be proven.

---

### Slide 10: Immediate Impact & Next Steps
- **In Dev's Hand:** A comprehensive Tenant Stabilization Brief with corroborating evidence, statutory citations (RPL § 235-b, Admin Code § 27-2115), eligible relief funds, and an intake memo.
- **Next Steps:**
  - Real-time integration with live NYC HPD Open Data API.
  - Mobile proactive intake routing for high-burden silent distress corridors.
  - Automated tenant inspection-request agent.
