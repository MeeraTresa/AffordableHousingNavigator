import pytest
from google.cloud import bigquery
from agent.navigator.config import PROJECT, DATASET

def test_census_tract_geoid_string_invariant_in_bigquery():
    """Rule 1: census_tract_geoid must be STRING and 11 characters across all tables and views."""
    client = bigquery.Client(project=PROJECT)
    tables = [
        "acs_tract_housing_tenure",
        "court_eviction_filings",
        "municipal_311_housing_complaints",
        "v_tract_context",
    ]
    for table in tables:
        cols = list(client.query(f"""
            SELECT data_type
            FROM `{PROJECT}.{DATASET}.INFORMATION_SCHEMA.COLUMNS`
            WHERE table_name = '{table}' AND column_name = 'census_tract_geoid'
        """).result())
        assert len(cols) == 1, f"census_tract_geoid not found in {table}"
        assert cols[0]["data_type"] == "STRING", f"census_tract_geoid in {table} is {cols[0]['data_type']}, expected STRING"

        # Check lengths and leading zero
        stats = list(client.query(f"""
            SELECT
              COUNT(*) AS total,
              COUNTIF(LENGTH(census_tract_geoid) != 11) AS bad_len,
              COUNTIF(SUBSTR(census_tract_geoid, 1, 2) != '36') AS bad_fips
            FROM `{PROJECT}.{DATASET}.{table}`
        """).result())[0]
        assert stats.bad_len == 0, f"Found non-11 char census_tract_geoid in {table}"
        assert stats.bad_fips == 0, f"Found non-36 FIPS prefix census_tract_geoid in {table}"
