#!/usr/bin/env python3
import os
import sys
from google.cloud import bigquery

def main():
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-03-ee26737d3114")
    client = bigquery.Client(project=project)

    with open("sql/05_equity_audit.sql") as f:
        query = f.read()

    print(f"Running Equity Audit against project {project}...")
    query_job = client.query(query)
    rows = list(query_job.result())

    print("\n--- Equity Audit Results ---")
    headers = ["Group", "Tracts", "Severely Burdened HH", "No Vehicle %", "Black %", "Hispanic %", "Asian %", "White %"]
    print(f"{headers[0]:<38} | {headers[1]:<6} | {headers[2]:<20} | {headers[3]:<12} | {headers[4]:<7} | {headers[5]:<10} | {headers[6]:<7} | {headers[7]:<7}")
    print("-" * 125)

    data = []
    group_b_data = None

    for r in rows:
        grp = r["grp"]
        tracts = r["tracts"]
        hh = r["severely_burdened_households"]
        no_veh = r["no_vehicle_pct"]
        blk = r["black_pct"]
        hsp = r["hispanic_pct"]
        asn = r["asian_pct"]
        wht = r["white_pct"]

        data.append({
            "grp": grp,
            "tracts": tracts,
            "hh": hh,
            "no_veh": no_veh,
            "blk": blk,
            "hsp": hsp,
            "asn": asn,
            "wht": wht
        })

        if "Silent distress" in grp:
            group_b_data = data[-1]

        print(f"{grp:<38} | {tracts:<6} | {hh:<20} | {no_veh:<12} | {blk:<7} | {hsp:<10} | {asn:<7} | {wht:<7}")

    # Generate docs/equity_audit_results.md
    n_tracts = group_b_data["tracts"] if group_b_data else 0
    m_households = group_b_data["hh"] if group_b_data else 0
    x_no_vehicle = group_b_data["no_veh"] if group_b_data else 0.0

    markdown = f"""# Post-Output Batch Equity Audit Results

**Corridor:** New York City Metro (168 Census Tracts, `a4i_housing`)  
**Source Query:** `sql/05_equity_audit.sql`  
**Execution Script:** `scripts/run_equity_audit.py`  
**Guardrail Status:** `audit_*` demographic variables are isolated strictly to post-output evaluation. They never enter embeddings, prompts, retrieval, or ranking.

---

## 1. Demographic & Distress Distribution Across Triage Policies

| Triage Policy Group | Tracts | Severely Rent-Burdened Households | No-Vehicle Rate (%) | Black Share (%) | Hispanic Share (%) | Asian Share (%) | White Share (%) |
|---|---:|---:|---:|---:|---:|---:|---:|
"""
    for d in data:
        markdown += f"| **{d['grp']}** | {d['tracts']:,} | {d['hh']:,} | {d['no_veh']}% | {d['blk']}% | {d['hsp']}% | {d['asn']}% | {d['wht']}% |\n"

    markdown += f"""
---

## 2. Key Metric Sentence for Pitch Deck & Presentation

> *"An open-311-only rule would skip **{n_tracts}** tracts holding **{m_households:,}** severely rent-burdened households. Our navigator routes those cases to the inspection-request pathway and to funds without an open-case requirement, and we flag those tracts for mobile intake (**{x_no_vehicle}%** no-vehicle)."*

---

## 3. Equity Analysis & Interpretation

Public municipal 311 habitability logs are powerful corroborating evidence in housing court, but they suffer from documented reporting bias: low-income, immigrant, and rent-burdened tenants frequently fear landlord retaliation, harassment, or lease non-renewal if they file city inspection complaints. 

The audit reveals that **Group B ("Silent Distress")** encompasses **{n_tracts}** census tracts with **{m_households:,}** households spending over 50% of their income on rent and facing above-median eviction filings, despite having $\\le 1$ open residential 311 complaint. These communities exhibit an extraordinary **{x_no_vehicle}%** zero-vehicle rate. A naive triage system that conditions assistance exclusively on prior 311 filings would systematically deny stabilization aid to these vulnerable households.

**System Mitigation in Stabilization Navigator:**
1. **Fallback Inspection Intake Pathway:** When a tenant reports active habitability hazards on a block without prior 311 violations, the navigator drafts a formal HPD emergency inspection request and structures photo-evidence checklists.
2. **Flexible Fund Routing:** The navigator matches households to emergency programs where `requires_open_habitability_case = FALSE` (such as the HRA One Shot Deal, up to $15,000, and CityFHEPS arrears pathway, up to $18,000) while inspection requests are pending.
3. **Transit Barrier Flag:** The high no-vehicle rate ({x_no_vehicle}%) triggers automated court transit advisories (subway/bus routing to 111 Centre St) to prevent non-appearance default judgments.
"""

    with open("docs/equity_audit_results.md", "w") as f:
        f.write(markdown)

    print("\nWrote docs/equity_audit_results.md with real BigQuery numbers successfully!")

if __name__ == "__main__":
    main()
