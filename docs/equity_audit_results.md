# Post-Output Batch Equity Audit Results

**Corridor:** New York City Metro (168 Census Tracts, `a4i_housing`)  
**Source Query:** `sql/05_equity_audit.sql`  
**Execution Script:** `scripts/run_equity_audit.py`  
**Guardrail Status:** `audit_*` demographic variables are isolated strictly to post-output evaluation. They never enter embeddings, prompts, retrieval, or ranking.

---

## 1. Demographic & Distress Distribution Across Triage Policies

| Triage Policy Group | Tracts | Severely Rent-Burdened Households | No-Vehicle Rate (%) | Black Share (%) | Hispanic Share (%) | Asian Share (%) | White Share (%) |
|---|---:|---:|---:|---:|---:|---:|---:|
| **A. Prioritized by open-311 rule** | 38 | 29,117 | 71.7% | 28.6% | 55.4% | 5.1% | 8.5% |
| **B. Silent distress (missed by 311 rule)** | 37 | 33,980 | 74.9% | 25.0% | 43.2% | 14.6% | 15.1% |
| **C. Other tracts** | 93 | 47,271 | 69.3% | 18.4% | 27.7% | 14.8% | 35.4% |

---

## 2. Key Metric Sentence for Pitch Deck & Presentation

> *"An open-311-only rule would skip **37** tracts holding **33,980** severely rent-burdened households. Our navigator routes those cases to the inspection-request pathway and to funds without an open-case requirement, and we flag those tracts for mobile intake (**74.9%** no-vehicle)."*

---

## 3. Equity Analysis & Interpretation

Public municipal 311 habitability logs are powerful corroborating evidence in housing court, but they suffer from documented reporting bias: low-income, immigrant, and rent-burdened tenants frequently fear landlord retaliation, harassment, or lease non-renewal if they file city inspection complaints. 

The audit reveals that **Group B ("Silent Distress")** encompasses **37** census tracts with **33,980** households spending over 50% of their income on rent and facing above-median eviction filings, despite having $\le 1$ open residential 311 complaint. These communities exhibit an extraordinary **74.9%** zero-vehicle rate. A naive triage system that conditions assistance exclusively on prior 311 filings would systematically deny stabilization aid to these vulnerable households.

**System Mitigation in Stabilization Navigator:**
1. **Fallback Inspection Intake Pathway:** When a tenant reports active habitability hazards on a block without prior 311 violations, the navigator drafts a formal HPD emergency inspection request and structures photo-evidence checklists.
2. **Flexible Fund Routing:** The navigator matches households to emergency programs where `requires_open_habitability_case = FALSE` (such as the HRA One Shot Deal, up to $15,000, and CityFHEPS arrears pathway, up to $18,000) while inspection requests are pending.
3. **Transit Barrier Flag:** The high no-vehicle rate (74.9%) triggers automated court transit advisories (subway/bus routing to 111 Centre St) to prevent non-appearance default judgments.
