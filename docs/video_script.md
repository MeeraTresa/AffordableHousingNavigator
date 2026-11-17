# Stabilization Navigator: 3-Minute Video Walkthrough Script

**Run Time:** 2 minutes 55 seconds (Strictly $\le$ 3:00)  
**Presenter:** Developer / Civic Tech Lead  
**UI Surface:** Custom Intake Desk (`http://localhost:8088` or Cloud Run Dev UI) at 1280×720  

---

### [0:00 – 0:20] Hook: Marisol's Monday
- **Screen:** Title card fades into the Intake Desk with Case Marisol V. loaded; hearing countdown timer pulsing: "⏳ Mon 9:30 AM · 89h remaining".
- **Voiceover:**
  > "Thursday afternoon, 3:40 PM. Marisol walks into a Harlem legal-aid clinic with a 3-day eviction notice for $3,350. Her radiators have been ice cold for eighteen days, toxic mold covers her bathroom, and water is dripping near the fuse box. Her hearing is Monday at 9:30 AM. The city's housing agency already inspected and knows about these hazards. Her court file doesn't."

---

### [0:20 – 0:35] The Data: Why New York
- **Screen:** Quick cut to the 6-metro data audit table showing New York's 168 tracts and 165 open residential 311 complaints.
- **Voiceover:**
  > "We engineered our navigator for New York—the only metro in our 6-city audit where open municipal 311 records describe active habitability violations at real urban scale. But connecting citizen complaints to housing court under a clock is an urgent triage challenge."

---

### [0:35 – 1:20] Live Demo: Turns 1 & 2 — Vector Candidate Generation & Decoy Traps
- **Screen:** Dev clicks Turn 1 on the Intake Desk. The agent opens the case file and executes vector search. The Evidence tab lights up with 3 green kept records and 4 grey excluded records.
- **Voiceover:**
  > "Dev enters what Marisol said in plain language. Vector search using Gemini-Embedding-2 instantly bridges citizen phrasing to municipal inspector codes, finding HPD Class A mold and Class C heating access violations on St. Nicholas Avenue.
  > 
  > But look closely: raw semantic similarity ranked a closed boiler repair number one! A keyword search would have dragged that into court and destroyed her defense. Our relational post-filter catches all nine planted decoys—marking them 'Closed – Abated' or 'Commercial Property' with explicit explanations."

---

### [0:55 – 1:20] Turn 2: Explaining Exclusions
- **Screen:** Dev clicks Turn 2: *"Why did you drop that boiler record?"* The agent immediately references `DECOY-NEWY-04` and `DECOY-NEWY-01`.
- **Voiceover:**
  > "When asked why the boiler match was dropped, the navigator explains: 'DECOY-NEWY-04 was replaced and closed by the inspector, while DECOY-01 was a commercial storefront.' Total transparency for the supervising attorney."

---

### [1:20 – 1:55] Live Demo: Turns 3 & 4 — Law and Deterministic Relief Matching
- **Screen:** Dev triggers Turn 3 (*"What law covers this?"*), switching to Law tab showing NY RPL § 235-b and Admin Code § 27-2115. Then Dev triggers Turn 4 (household details), switching to Funds tab with 4 green ELIGIBLE cards.
- **Voiceover:**
  > "Next, statutory defense: the agent cites New York's mandatory 24-hour repair window for Class C heat hazards and flags the critical procedural check—did the landlord serve a valid 14-day written rent demand?
  > 
  > Then, emergency money. We never let the LLM guess income or funding eligibility. Our deterministic Python rules engine evaluates Marisol's household against four NYC programs. Result: four green passes—unlocking $42,500 in potential relief capacity, including the HRA One Shot Deal and Right to Counsel defense clinic."

---

### [1:55 – 2:15] Turn 6: Testing Evidentiary Boundaries
- **Screen:** Dev clicks Turn 6: *"Landlord's lawyer says the boiler was fixed last week."*
- **Voiceover:**
  > "Intake attorneys face oral landlord pushback constantly. When the landlord claims the boiler was fixed last week, the navigator doesn't hallucinate. It states what the public record can and cannot prove: the violation remains open as of the official municipal snapshot, oral claims are unverified, and an emergency HPD re-inspection must be requested."

---

### [2:15 – 2:40] Turn 7: The Brief & Post-Output Equity Audit
- **Screen:** Dev clicks Turn 7 (*"Draft the brief"*). Brief tab displays the full Tenant Stabilization Brief with Copy and Print buttons, highlighting the Equity Audit note at the bottom.
- **Voiceover:**
  > "With one click, the full Tenant Stabilization Brief is compiled for the attorney tonight.
  > 
  > And we audited our own triage rules. Our batch query across all 168 New York tracts revealed 37 'silent distress' tracts—holding 33,980 severely rent-burdened families with a 75% zero-vehicle rate who rarely call 311. Our navigator safeguards them by providing an automated inspection-request pathway and routing them to non-contingent relief funds."

---

### [2:40 – 3:00] Architecture & Closing
- **Screen:** Full architecture diagram with technology badges: ADK, Gemini 2.5 Flash, BigQuery Vector Search, Cloud Run MCP Toolbox, and live service links.
- **Voiceover:**
  > "Built with ADK, Gemini 2.5 Flash, BigQuery Vector Search, and MCP Toolbox on Cloud Run. Real Census and 311 records, modeled filings labeled honestly, zero data leakage. Engineered so Marisol walks into court Monday morning with a defensible case and an eviction defense."
