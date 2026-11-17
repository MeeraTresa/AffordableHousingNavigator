from google.cloud import bigquery
from google.adk.tools import ToolContext
from ..bq import run_query

_TRACT_SQL = """
SELECT t.*, b.metro_severe_rent_burden_pct, b.median_tract_nonpayment_filings_modeled
FROM `a4i_housing.v_tract_context` t CROSS JOIN `a4i_housing.v_metro_baseline` b
WHERE t.census_tract_geoid = @census_tract_geoid
"""

_FIND_TRACT_SQL = """
SELECT DISTINCT block_address, census_tract_geoid
FROM `a4i_housing.municipal_311_housing_complaints`
WHERE LOWER(block_address) LIKE CONCAT('%', LOWER(@block_fragment), '%')
  AND request_id NOT LIKE 'DECOY-%'
LIMIT 5
"""

def get_tract_context(census_tract_geoid: str) -> dict:
    """Neighborhood context for one census tract: severe rent burden, MODELED annual eviction
    filings (pre-aggregated across 4 quarters, no fan-out), open residential 311 count,
    poverty and vehicle access. GEOID is an 11-character string."""
    rows = run_query(_TRACT_SQL, [bigquery.ScalarQueryParameter("census_tract_geoid", "STRING", census_tract_geoid)])
    return rows[0] if rows else {"error": f"Tract {census_tract_geoid} not found"}

def find_tract_for_block(block_fragment: str) -> list[dict]:
    """Resolve a 100-block address fragment to its census tract GEOID(s)."""
    return run_query(_FIND_TRACT_SQL, [bigquery.ScalarQueryParameter("block_fragment", "STRING", block_fragment)])
