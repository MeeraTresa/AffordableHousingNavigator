#!/usr/bin/env python3
"""Run M03 sanity checks and generate docs/rigor/03_embeddings.txt."""

import os
from google.cloud import bigquery

PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-03-ee26737d3114")
client = bigquery.Client(project=PROJECT, location="US")

output = []
def log(msg=""):
    print(msg)
    output.append(msg)

log("=== M03 Embeddings & Fan-Out-Safe Views Sanity Verification ===\n")

# 1. Check complaints_embedded
c_res = list(client.query("""
    SELECT COUNT(*) AS total_rows, COUNTIF(request_id LIKE 'DECOY-%') AS decoys
    FROM `a4i_housing.complaints_embedded`
""").result())[0]
log(f"1. complaints_embedded:")
log(f"   total_rows: {c_res.total_rows} (expected 174)")
log(f"   decoys: {c_res.decoys} (expected 9)")

# 2. Check statutes_embedded
s_res = list(client.query("SELECT COUNT(*) AS n FROM `a4i_housing.statutes_embedded`").result())[0]
log(f"\n2. statutes_embedded:")
log(f"   statutes_count: {s_res.n} (expected 3)")

# 3. Check bulletins_embedded
b_res = list(client.query("SELECT COUNT(*) AS n FROM `a4i_housing.bulletins_embedded`").result())[0]
log(f"\n3. bulletins_embedded:")
log(f"   bulletins_count: {b_res.n} (expected 4)")

# 4. Check v_tract_context & v_metro_baseline
t_res = list(client.query("""
    SELECT COUNT(*) AS n, COUNTIF(quarters_aggregated != 4) AS bad_quarters
    FROM `a4i_housing.v_tract_context`
""").result())[0]
log(f"\n4. v_tract_context:")
log(f"   tracts_count: {t_res.n} (expected 168)")
log(f"   bad_quarters_aggregated: {t_res.bad_quarters} (expected 0)")

mb_res = list(client.query("SELECT * FROM `a4i_housing.v_metro_baseline`").result())[0]
log(f"\n5. v_metro_baseline:")
log(f"   metro_severe_rent_burden_pct: {mb_res.metro_severe_rent_burden_pct}%")
log(f"   median_tract_nonpayment_filings_modeled: {mb_res.median_tract_nonpayment_filings_modeled}")
log(f"   tracts: {mb_res.tracts}")

# 5. Raw vector search test
with open("agent/navigator/tools/search.sql") as f:
    sql = f.read()

queries = ["no heat radiators cold", "black mold around tub", "water leak through bathroom wall"]
block_hint = "1000 block st nicholas"
tract_hint = ""

job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ArrayQueryParameter("queries", "STRING", queries),
        bigquery.ScalarQueryParameter("block_hint", "STRING", block_hint),
        bigquery.ScalarQueryParameter("tract_hint", "STRING", tract_hint),
    ]
)

rows = list(client.query(sql, job_config=job_config).result())
log(f"\n6. Raw VECTOR_SEARCH results (queries: {queries}, block: '{block_hint}'):")
log(f"   Total matches returned: {len(rows)}")
log("   Top 10 RAW matches:")

has_decoy = False
for i, r in enumerate(rows[:10]):
    is_decoy = r.request_id.startswith("DECOY-")
    if is_decoy:
        has_decoy = True
    decoy_mark = " [DECOY]" if is_decoy else ""
    log(f"   #{i+1}: request_id={r.request_id}{decoy_mark} | sim={r.similarity:.4f} | status={r.inspection_status} | prop={r.property_type} | dist={r.meters_from_anchor}m")
    log(f"       narrative: {r.complaint_narrative[:80]}...")

log(f"\nAt least one DECOY-* in top 10 RAW results: {has_decoy}")

with open("docs/rigor/03_embeddings.txt", "w") as f:
    f.write("\n".join(output) + "\n")
log("\nOutputs successfully saved to docs/rigor/03_embeddings.txt")
