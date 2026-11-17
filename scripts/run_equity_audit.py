#!/usr/bin/env python3
import os
from google.cloud import bigquery

PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-03-ee26737d3114")
client = bigquery.Client(project=PROJECT, location="US")

with open("sql/05_equity_audit.sql") as f:
    sql = f.read()

rows = [dict(r) for r in client.query(sql).result()]
print(f"{'Group':<38} | {'Tracts':<6} | {'Severe Burden HH':<16} | {'No Car %':<8} | {'Black %':<7} | {'Hisp %':<7}")
print("-" * 95)
b_tracts = 0
b_hh = 0
b_nocar = 0.0

for r in rows:
    print(f"{r['grp']:<38} | {r['tracts']:<6} | {r['severely_burdened_households']:<16} | {r['no_vehicle_pct']:<8} | {r['black_pct']:<7} | {r['hispanic_pct']:<7}")
    if "Silent distress" in r["grp"]:
        b_tracts = r["tracts"]
        b_hh = r["severely_burdened_households"]
        b_nocar = r["no_vehicle_pct"]

deck_sentence = (
    f"An open-311-only rule would skip {b_tracts} tracts holding {b_hh:,} severely rent-burdened households. "
    f"Our navigator routes those cases to the inspection-request pathway and to funds without an open-case requirement, "
    f"and we flag those tracts for mobile intake ({b_nocar}% no-vehicle)."
)
print("\nDeck takeaway sentence:")
print(deck_sentence)

os.makedirs("docs", exist_ok=True)
with open("docs/equity_audit_results.md", "w") as f:
    f.write("# Equity Audit Findings\n\n")
    f.write("| Group | Tracts | Severely Burdened Households | No Vehicle % | Black % | Hispanic % | Asian % | White % |\n")
    f.write("|---|---:|---:|---:|---:|---:|---:|---:|\n")
    for r in rows:
        f.write(f"| {r['grp']} | {r['tracts']} | {r['severely_burdened_households']} | {r['no_vehicle_pct']}% | {r['black_pct']}% | {r['hispanic_pct']}% | {r['asian_pct']}% | {r['white_pct']}% |\n")
    f.write(f"\n> **Takeaway:** *\"{deck_sentence}\"*\n")
