#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="$(gcloud config get-value project 2>/dev/null || true)"
DATASET="a4i_housing"
LOCATION="US"

echo "--> Generating Gemini embeddings for municipal complaints (all 6 metros)..."
bq --project_id="${PROJECT_ID}" --location="${LOCATION}" query \
  --use_legacy_sql=false \
  "CREATE OR REPLACE TABLE \`${PROJECT_ID}.${DATASET}.complaints_embedded\` AS
   SELECT
     request_id, metro_area, jurisdiction, census_tract_geoid, block_address,
     agency_code, property_type, raw_complaint_type, inspection_status,
     created_date, closed_date, latitude, longitude, data_provenance,
     complaint_narrative,
     embedded.result AS embedding
   FROM (
     SELECT *,
       AI.EMBED(complaint_narrative,
                connection_id => 'us.a4i-vertex',
                endpoint => 'gemini-embedding-2') AS embedded
     FROM \`${PROJECT_ID}.${DATASET}.municipal_311_housing_complaints\`
   )
   WHERE embedded.status = '';"

echo "--> Generating Gemini embeddings for statutes (all 6 metros)..."
bq --project_id="${PROJECT_ID}" --location="${LOCATION}" query \
  --use_legacy_sql=false \
  "CREATE OR REPLACE TABLE \`${PROJECT_ID}.${DATASET}.statutes_embedded\` AS
   SELECT s.* EXCEPT(embedded), embedded.result AS embedding
   FROM (
     SELECT *, AI.EMBED(CONCAT(ordinance_title, '. ', raw_statute_text),
                        connection_id => 'us.a4i-vertex',
                        endpoint => 'gemini-embedding-2') AS embedded
     FROM \`${PROJECT_ID}.${DATASET}.municipal_housing_ordinance_statutes\`
   ) AS s
   WHERE embedded.status = '';"

echo "--> Generating Gemini embeddings for relief bulletins (all 6 metros)..."
bq --project_id="${PROJECT_ID}" --location="${LOCATION}" query \
  --use_legacy_sql=false \
  "CREATE OR REPLACE TABLE \`${PROJECT_ID}.${DATASET}.bulletins_embedded\` AS
   SELECT b.* EXCEPT(embedded), embedded.result AS embedding
   FROM (
     SELECT *, AI.EMBED(CONCAT(program_name, '. ', raw_bulletin_text),
                        connection_id => 'us.a4i-vertex',
                        endpoint => 'gemini-embedding-2') AS embedded
     FROM \`${PROJECT_ID}.${DATASET}.rental_relief_program_bulletins\`
   ) AS b
   WHERE embedded.status = '';"

echo "--> Rebuilding views across all tracts..."
bq --project_id="${PROJECT_ID}" --location="${LOCATION}" query \
  --use_legacy_sql=false \
  "CREATE OR REPLACE VIEW \`${PROJECT_ID}.${DATASET}.v_tract_context\` AS
   WITH annual_filings AS (
     SELECT census_tract_geoid,
            SUM(nonpayment_filings_count)              AS annual_nonpayment_filings,
            SUM(holdover_or_no_fault_filings_count)    AS annual_holdover_filings,
            SUM(default_judgments_count)               AS annual_default_judgments,
            ROUND(AVG(median_claimed_arrears_usd), 0)  AS avg_claimed_arrears_usd,
            COUNT(*)                                   AS quarters_aggregated
     FROM \`${PROJECT_ID}.${DATASET}.court_eviction_filings\`
     GROUP BY census_tract_geoid
   ),
   open_res AS (
     SELECT census_tract_geoid, COUNT(*) AS open_residential_311
     FROM \`${PROJECT_ID}.${DATASET}.municipal_311_housing_complaints\`
     WHERE property_type = 'Residential' AND closed_date IS NULL
       AND request_id NOT LIKE 'DECOY-%'
     GROUP BY census_tract_geoid
   )
   SELECT
     a.census_tract_geoid,
     a.county_name,
     a.metro_area,
     a.renter_occupied_units,
     a.median_household_income,
     a.median_gross_rent,
     ROUND(SAFE_DIVIDE(a.renter_hh_rent_50_pct_plus_count, a.renter_occupied_units) * 100, 1) AS severe_rent_burden_pct,
     ROUND(SAFE_DIVIDE(a.renter_hh_rent_30_to_49_pct_count, a.renter_occupied_units) * 100, 1) AS rent_burden_30_49_pct,
     ROUND(a.poverty_rate * 100, 1)    AS poverty_pct,
     ROUND(a.no_vehicle_rate * 100, 1) AS no_vehicle_pct,
     COALESCE(f.annual_nonpayment_filings, 0) AS annual_nonpayment_filings_modeled,
     COALESCE(f.annual_holdover_filings, 0)   AS annual_holdover_filings_modeled,
     COALESCE(f.annual_default_judgments, 0)  AS annual_default_judgments_modeled,
     f.avg_claimed_arrears_usd                AS avg_claimed_arrears_usd_modeled,
     f.quarters_aggregated,
     COALESCE(o.open_residential_311, 0)      AS open_residential_311
   FROM \`${PROJECT_ID}.${DATASET}.acs_tract_housing_tenure\` a
   LEFT JOIN annual_filings f USING (census_tract_geoid)
   LEFT JOIN open_res o USING (census_tract_geoid);"

bq --project_id="${PROJECT_ID}" --location="${LOCATION}" query \
  --use_legacy_sql=false \
  "CREATE OR REPLACE VIEW \`${PROJECT_ID}.${DATASET}.v_metro_baseline\` AS
   SELECT
     a.metro_area,
     ROUND(SAFE_DIVIDE(SUM(a.renter_hh_rent_50_pct_plus_count), SUM(a.renter_occupied_units)) * 100, 1) AS metro_severe_rent_burden_pct,
     APPROX_QUANTILES(t.annual_nonpayment_filings_modeled, 2)[OFFSET(1)] AS median_tract_nonpayment_filings_modeled,
     COUNT(*) AS tracts
   FROM \`${PROJECT_ID}.${DATASET}.acs_tract_housing_tenure\` a
   JOIN \`${PROJECT_ID}.${DATASET}.v_tract_context\` t USING (census_tract_geoid)
   GROUP BY a.metro_area;"

echo "--> Verifying embedded counts:"
bq --project_id="${PROJECT_ID}" --location="${LOCATION}" query \
  --use_legacy_sql=false --format=csv \
  "SELECT 'complaints_embedded' AS tbl, COUNT(*) AS cnt, COUNT(DISTINCT metro_area) AS metros FROM \`${PROJECT_ID}.${DATASET}.complaints_embedded\`"
bq --project_id="${PROJECT_ID}" --location="${LOCATION}" query \
  --use_legacy_sql=false --format=csv \
  "SELECT 'bulletins_embedded' AS tbl, COUNT(*) AS cnt, COUNT(DISTINCT metro_area) AS metros FROM \`${PROJECT_ID}.${DATASET}.bulletins_embedded\`"
bq --project_id="${PROJECT_ID}" --location="${LOCATION}" query \
  --use_legacy_sql=false --format=csv \
  "SELECT 'statutes_embedded' AS tbl, COUNT(*) AS cnt, COUNT(DISTINCT metro_area) AS metros FROM \`${PROJECT_ID}.${DATASET}.statutes_embedded\`"
