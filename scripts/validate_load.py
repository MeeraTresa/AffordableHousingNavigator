#!/usr/bin/env python3
"""Run notebook Section 12 validation checks against loaded BigQuery tables."""

import os
import sys
from google.cloud import bigquery

PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-03-ee26737d3114")
DATASET = os.environ.get("A4I_DATASET", "a4i_housing")
LOCATION = os.environ.get("A4I_LOCATION", "US")
METRO = "New York"
STATE_FIPS = "36"
S = f"{PROJECT}.{DATASET}"

client = bigquery.Client(project=PROJECT, location=LOCATION)
checks = []

def check(name, condition, detail):
    verdict = "PASS" if condition else "FAIL"
    checks.append({"check": name, "verdict": verdict, "detail": detail})
    print(f"[{verdict}] {name}: {detail}")

def note(name, condition, detail):
    verdict = "PASS" if condition else "WARN"
    checks.append({"check": name, "verdict": verdict, "detail": detail})
    print(f"[{verdict}] {name}: {detail}")

print(f"Running validation checks against {S} (METRO={METRO}, STATE_FIPS={STATE_FIPS})\n")

t_stats = list(client.query(f"""
    SELECT
        COUNT(*) AS n,
        COUNT(DISTINCT census_tract_geoid) AS n_distinct,
        COUNTIF(LENGTH(census_tract_geoid) != 11) AS bad_geoid_len,
        COUNTIF(SUBSTR(census_tract_geoid, 1, 2) != '{STATE_FIPS}') AS bad_fips_prefix,
        COUNTIF(metro_area != '{METRO}') AS wrong_metro,
        COUNTIF(renter_occupied_units <= 0) AS nonpos_renters,
        COUNTIF(renter_hh_rent_50_pct_plus_count > renter_occupied_units) AS impossible_burden,
        COUNTIF(
            audit_black_share < 0 OR audit_black_share > 1
            OR audit_hispanic_share < 0 OR audit_hispanic_share > 1
            OR audit_asian_share < 0 OR audit_asian_share > 1
            OR audit_indigenous_share < 0 OR audit_indigenous_share > 1
            OR audit_white_share < 0 OR audit_white_share > 1
        ) AS bad_audit_bounds
    FROM `{S}.acs_tract_housing_tenure`
""").result())[0]

check("tenure: >= 40 tracts loaded", t_stats.n >= 40, f"{t_stats.n} tracts")
check("tenure: unique census_tract_geoid", t_stats.n == t_stats.n_distinct, f"{t_stats.n_distinct} distinct")
check("tenure: all tract IDs are 11 chars (leading zero intact)", t_stats.bad_geoid_len == 0, f"{t_stats.bad_geoid_len} bad")
check("tenure: all tracts match metro state FIPS", t_stats.bad_fips_prefix == 0, f"expected prefix {STATE_FIPS}")
check("tenure: all rows belong to selected METRO", t_stats.wrong_metro == 0, f"{t_stats.wrong_metro} wrong")
check("tenure: positive renter_occupied_units", t_stats.nonpos_renters == 0, f"{t_stats.nonpos_renters} <= 0")
check("tenure: 50%+ rent-burden count <= renter units", t_stats.impossible_burden == 0, f"{t_stats.impossible_burden} bad")
check("tenure: audit_* shares within [0, 1]", t_stats.bad_audit_bounds == 0, f"{t_stats.bad_audit_bounds} out of bounds")

f_stats = list(client.query(f"""
    SELECT
        COUNT(*) AS n,
        COUNT(DISTINCT filing_record_id) AS n_distinct,
        COUNT(DISTINCT reporting_quarter) AS n_quarters,
        COUNTIF(metro_area != '{METRO}') AS wrong_metro,
        COUNTIF(nonpayment_filings_count < 0 OR holdover_or_no_fault_filings_count < 0) AS neg_counts,
        COUNTIF(census_tract_geoid NOT IN (
            SELECT census_tract_geoid FROM `{S}.acs_tract_housing_tenure`
        )) AS orphan_tracts
    FROM `{S}.court_eviction_filings`
""").result())[0]

check("filings: exact 4 quarters per tract", f_stats.n == 4 * t_stats.n and f_stats.n_quarters == 4, f"{f_stats.n} rows across {f_stats.n_quarters} quarters")
check("filings: unique filing_record_id", f_stats.n == f_stats.n_distinct, f"{f_stats.n_distinct} distinct")
check("filings: all rows match METRO", f_stats.wrong_metro == 0, f"{f_stats.wrong_metro} wrong")
check("filings: non-negative filing counts", f_stats.neg_counts == 0, f"{f_stats.neg_counts} negative")
check("filings: 100% FK match to acs_tract_housing_tenure", f_stats.orphan_tracts == 0, f"{f_stats.orphan_tracts} orphans")

c_stats = list(client.query(rf"""
    SELECT
        COUNT(*) AS n,
        COUNT(DISTINCT request_id) AS n_distinct,
        COUNTIF(metro_area != '{METRO}') AS wrong_metro,
        COUNTIF(LENGTH(census_tract_geoid) != 11) AS bad_geoid_len,
        COUNTIF(census_tract_geoid NOT IN (
            SELECT census_tract_geoid FROM `{S}.acs_tract_housing_tenure`
        )) AS orphan_tracts,
        COUNTIF(request_id LIKE 'DECOY-%') AS n_decoys,
        COUNTIF(request_id LIKE 'DECOY-%' AND property_type = 'Commercial' AND closed_date IS NULL) AS decoy_comm_open,
        COUNTIF(request_id LIKE 'DECOY-%' AND property_type = 'Residential' AND inspection_status = 'Closed - Abated') AS decoy_res_abated,
        COUNTIF(request_id LIKE 'DECOY-%' AND property_type = 'Residential' AND inspection_status = 'Closed - No Violation') AS decoy_res_noviol,
        COUNTIF(property_type = 'Residential' AND closed_date IS NULL AND request_id NOT LIKE 'DECOY-%') AS open_real_res,
        COUNTIF(REGEXP_CONTAINS(complaint_narrative, r'(?i)\bmy\s+name\s+is\s+[A-Z][a-z]+')) AS pii_names_left,
        COUNTIF(REGEXP_CONTAINS(complaint_narrative, r'(?i)license\s+plate\s*#?\s*[A-Z0-9]{4,}')) AS pii_plates_left,
        COUNTIF(REGEXP_CONTAINS(complaint_narrative, r'(?i)\b(dwelling\s+unit|apt\.?|apartment|room)\s*[:#]?\s*\d+')) AS pii_units_left
    FROM `{S}.municipal_311_housing_complaints`
""").result())[0]

check("311: expected 174 rows (165 real + 9 decoys)", c_stats.n == 174, f"{c_stats.n} rows")
check("311: unique request_id", c_stats.n == c_stats.n_distinct, f"{c_stats.n_distinct} distinct")
check("311: all rows match METRO", c_stats.wrong_metro == 0, f"{c_stats.wrong_metro} wrong")
check("311: all tract IDs are 11 chars", c_stats.bad_geoid_len == 0, f"{c_stats.bad_geoid_len} bad")
check("311: 100% FK match to acs_tract_housing_tenure", c_stats.orphan_tracts == 0, f"{c_stats.orphan_tracts} orphans")
check("311: all 9 [Planted Case] decoys present (3+3+3)", c_stats.n_decoys == 9 and c_stats.decoy_comm_open == 3 and c_stats.decoy_res_abated == 3 and c_stats.decoy_res_noviol == 3, f"decoys={c_stats.n_decoys} ({c_stats.decoy_comm_open}/{c_stats.decoy_res_abated}/{c_stats.decoy_res_noviol})")
check("311: at least 5 open real residential complaints", c_stats.open_real_res >= 5, f"{c_stats.open_real_res} open residential cases")
check("311 PII scrub: zero self-disclosed caller names remain", c_stats.pii_names_left == 0, f"{c_stats.pii_names_left} remaining")
check("311 PII scrub: zero license plates remain", c_stats.pii_plates_left == 0, f"{c_stats.pii_plates_left} remaining")
check("311 PII scrub: zero apartment/room numbers remain", c_stats.pii_units_left == 0, f"{c_stats.pii_units_left} remaining")

b_stats = list(client.query(f"""
    SELECT
        COUNT(*) AS n_bul,
        COUNTIF(requires_open_habitability_case) AS n_hab_req,
        COUNTIF(NOT requires_open_habitability_case) AS n_general,
        (SELECT COUNT(*) FROM `{S}.municipal_housing_ordinance_statutes` WHERE metro_area = '{METRO}') AS n_stat
    FROM `{S}.rental_relief_program_bulletins`
    WHERE metro_area = '{METRO}'
""").result())[0]

check("bulletins: 4 metro programs (2 general + 2 habitability-contingent)", b_stats.n_bul == 4 and b_stats.n_hab_req == 2 and b_stats.n_general == 2, f"total={b_stats.n_bul} (hab={b_stats.n_hab_req}, gen={b_stats.n_general})")
check("statutes: 3 metro housing ordinance summaries loaded", b_stats.n_stat == 3, f"{b_stats.n_stat} statutes")

geo_cols = list(client.query(f"""
    SELECT table_name, column_name, data_type
    FROM `{S}.INFORMATION_SCHEMA.COLUMNS`
    WHERE (table_name = 'acs_tract_housing_tenure' AND column_name = 'tract_geom')
       OR (table_name = 'municipal_311_housing_complaints' AND column_name = 'property_geom')
""").result())
n_geog = sum(1 for col in geo_cols if col.data_type == "GEOGRAPHY")
check("spatial: tract_geom and property_geom landed as native GEOGRAPHY", n_geog == 2, f"{n_geog}/2 GEOGRAPHY columns")

failed = [c for c in checks if c["verdict"] == "FAIL"]
warned = [c for c in checks if c["verdict"] == "WARN"]
passed = [c for c in checks if c["verdict"] == "PASS"]

print(f"\n==================================================")
print(f"Validation summary: {len(checks)} checks — {len(passed)} PASS, {len(warned)} WARN, {len(failed)} FAIL")
print(f"Metrics: {c_stats.n} complaints, {t_stats.n} tracts, {f_stats.n} filing rows, {c_stats.n_decoys} decoys, {len(failed)} FAIL")
print(f"==================================================")

if failed:
    sys.exit(1)
