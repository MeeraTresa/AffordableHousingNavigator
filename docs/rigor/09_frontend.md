# Mission M09: Intake Desk UI Implementation & Verification

**Status:** Completed & Verified  
**Resolution:** 1280×720 (optimized for video walkthrough)  
**Modes:** Mock Replay (`?mock=1`) and Live Cloud Run ADK (`https://sq7-stabilization-navigator-530357188502.us-central1.run.app`)  

---

## 1. Components Delivered

- `frontend/index.html`: Responsive, single-page application layout with 40% Chat / 60% Live Case File division.
- `frontend/styles.css`: Dark modern civic-tech design system with provenance badges and hearing countdown timer.
- `frontend/app.js`: Replays turns 1–7 with dynamic Case File updates (kept/excluded evidence, relief funds pass/fail checks, applicable law, and brief rendering) and live Cloud Run API integration.
- `frontend/mock/turns.json`: Pre-staged golden path replaying turns 1–7 with all tool payloads.
- `scripts/test_ui.py`: Playwright browser automation verifying all turns at 1280×720.

---

## 2. Browser Verification Screenshots (1280×720)

| Turn / State | Description | Screenshot Artifact |
|---|---|---|
| **Initial State** | Intake Desk with Marisol V. case loaded & countdown | `docs/rigor/09_ui/01_mock_initial.png` |
| **Turn 1: Evidence** | Kept corroborating 311s (green) & 4 excluded decoys (grey) | `docs/rigor/09_ui/02_turn1_evidence.png` |
| **Turn 2: Exclusions** | Deep explanation of `DECOY-NEWY-04` (Abated) & `DECOY-NEWY-01` (Commercial) | `docs/rigor/09_ui/03_turn2_exclusion.png` |
| **Turn 3: Law** | Statutes tab populated with NY RPL § 235-b, Admin Code § 27-2115, Spiegel Law | `docs/rigor/09_ui/04_turn3_statutes.png` |
| **Turn 4: Funds** | Relief funds tab with pass/fail rule checkmarks (4× ELIGIBLE) | `docs/rigor/09_ui/05_turn4_funds.png` |
| **Turn 5: Neighborhood** | Pre-aggregated 4-quarter modeled filings (414) & severe burden (32.8%) | `docs/rigor/09_ui/06_turn5_neighborhood.png` |
| **Turn 6: Boundary** | Evidentiary limits regarding landlord counsel's oral repair claim | `docs/rigor/09_ui/07_turn6_boundary.png` |
| **Turn 7: Brief** | Full Tenant Stabilization Brief rendered with copy & print buttons | `docs/rigor/09_ui/08_turn7_brief.png` |
| **Live Mode Ready** | Live mode toggle connected to deployed Cloud Run ADK agent | `docs/rigor/09_ui/09_live_mode_ready.png` |

---

## 3. Provenance & Guardrail Verification

- **Real Data:** ACS 5-Year housing tenure counts and municipal 311 complaint narratives are labeled `Real: ACS 5-Yr, 311 Narratives`.
- **Modeled Data:** Quarterly court filings are labeled `[Modeled]: Eviction Filings (4-Qtr Agg)`.
- **Planted Decoys:** All 9 decoy cases per metro are strictly filtered by relational post-search predicates; badge reflects `[Planted]: Decoys Filtered 9/9`.
- **Equity Isolation:** Demographic variables (`audit_*`) remain completely isolated from retrieval and ranking, rendering only in post-output brief notes.
