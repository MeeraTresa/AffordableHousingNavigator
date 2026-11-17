#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PROJECT_ID="$(gcloud config get-value project 2>/dev/null || true)"
DATASET="a4i_housing"
LOCATION="US"

echo "=========================================================="
echo "Loading ALL 6 Metros into BigQuery: ${PROJECT_ID}:${DATASET}"
echo "=========================================================="

TABLES=(
  acs_tract_housing_tenure
  court_eviction_filings
  municipal_311_housing_complaints
  rental_relief_program_bulletins
  municipal_housing_ordinance_statutes
)

for table in "${TABLES[@]}"; do
  echo "--> Ingesting raw ${table}..."
  bq --project_id="${PROJECT_ID}" --location="${LOCATION}" load \
    --source_format=PARQUET --replace \
    "${DATASET}._raw_${table}" "${REPO_ROOT}/data/${table}.parquet"

  echo "--> Transforming & scrubbing ${table} across ALL metros..."
  case "${table}" in
    acs_tract_housing_tenure)
      bq --project_id="${PROJECT_ID}" --location="${LOCATION}" query \
        --use_legacy_sql=false \
        "CREATE OR REPLACE TABLE \`${PROJECT_ID}.${DATASET}.${table}\` AS
         SELECT * REPLACE (
           LPAD(census_tract_geoid, 11, '0') AS census_tract_geoid,
           LPAD(county_fips, 5, '0') AS county_fips
         ) FROM \`${PROJECT_ID}.${DATASET}._raw_${table}\`"
      ;;
    court_eviction_filings)
      bq --project_id="${PROJECT_ID}" --location="${LOCATION}" query \
        --use_legacy_sql=false \
        "CREATE OR REPLACE TABLE \`${PROJECT_ID}.${DATASET}.${table}\` AS
         SELECT * REPLACE (
           LPAD(census_tract_geoid, 11, '0') AS census_tract_geoid
         ) FROM \`${PROJECT_ID}.${DATASET}._raw_${table}\`"
      ;;
    municipal_311_housing_complaints)
      bq --project_id="${PROJECT_ID}" --location="${LOCATION}" query \
        --use_legacy_sql=false \
        "CREATE OR REPLACE TABLE \`${PROJECT_ID}.${DATASET}.${table}\` AS
         SELECT * REPLACE (
           LPAD(census_tract_geoid, 11, '0') AS census_tract_geoid,
           REGEXP_REPLACE(
             REPLACE(
               REGEXP_REPLACE(
                 REGEXP_REPLACE(
                   REGEXP_REPLACE(
                     REGEXP_REPLACE(
                       REGEXP_REPLACE(
                         REPLACE(complaint_narrative, CHR(65533), CHR(39)),
                         r'(?i)\b(my\s+name\s+is\s+|property\s+manager,?\s+)[A-Z][A-Za-z\x27\-]+(?:\s+[A-Z][A-Za-z\x27\-]+){0,2}',
                         '\\\\1[REDACTED NAME]'
                       ),
                       r'(?i)(license\s+plate\s*#?\s*)[A-Z0-9\-]+',
                       '\\\\1[REDACTED PLATE]'
                     ),
                     r'(?i)\b(dwelling\s+unit|apt\.?|apartment|room|rm\.?|suite|ste\.?)\s*[:#]?\s*\d+[A-Za-z]?(?:\s*(?:,|and)\s*\d+[A-Za-z]?)*',
                     '\\\\1 [REDACTED UNIT]'
                   ),
                   r'(?i)\b(\d{2,5})\s+Block\b',
                   '\\\\1__A4I_BLOCK__'
                 ),
                 r'(?i)\b(\d{2,5})(?:\s*[/\-]\s*\d{2,5})?\s+([A-Za-z0-9.\-]+(?:\s+[A-Za-z0-9.\-]+){0,2}\s+(?:St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Dr|Drive|Ln|Lane|Ct|Court|Way|Pl|Place)\b)',
                 '[REDACTED STREET NUMBER] \\\\2'
               ),
               '__A4I_BLOCK__',
               ' Block'
             ),
             r'(?i)(service\s+address:\s*)\d{2,5}\b',
             '\\\\1[REDACTED STREET NUMBER]'
           ) AS complaint_narrative
         )
         FROM \`${PROJECT_ID}.${DATASET}._raw_${table}\`"
      ;;
    *)
      bq --project_id="${PROJECT_ID}" --location="${LOCATION}" query \
        --use_legacy_sql=false \
        "CREATE OR REPLACE TABLE \`${PROJECT_ID}.${DATASET}.${table}\` AS
         SELECT * FROM \`${PROJECT_ID}.${DATASET}._raw_${table}\`"
      ;;
  esac

  bq --project_id="${PROJECT_ID}" rm -f -t "${PROJECT_ID}:${DATASET}._raw_${table}"
done

echo "=========================================================="
echo "Verifying row counts per table across ALL metros:"
echo "=========================================================="
for table in "${TABLES[@]}"; do
  bq --project_id="${PROJECT_ID}" --location="${LOCATION}" query \
    --use_legacy_sql=false --format=csv \
    "SELECT '${table}' AS tbl, COUNT(*) AS cnt, COUNT(DISTINCT metro_area) AS metros FROM \`${PROJECT_ID}.${DATASET}.${table}\`"
done
