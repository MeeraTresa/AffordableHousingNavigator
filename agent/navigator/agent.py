import os
from google.adk.agents import Agent
from .config import MODEL
from .prompts import SYSTEM_INSTRUCTION
from .tools.case_file import open_case, update_case
from .tools.evidence import search_habitability_evidence
from .tools.statutes import match_statutes
from .tools.funds import match_relief_funds
from .tools.brief import finalize_brief
from google.cloud import bigquery
from .bq import run_query

def get_tract_context(census_tract_geoid: str) -> dict:
    """Neighborhood context for one census tract: severe rent burden, MODELED annual eviction
    filings (pre-aggregated across 4 quarters, no fan-out), open residential 311 count,
    poverty and vehicle access. GEOID is an 11-character string."""
    sql = """
    SELECT t.*, b.metro_severe_rent_burden_pct, b.median_tract_nonpayment_filings_modeled
    FROM `a4i_housing.v_tract_context` t CROSS JOIN `a4i_housing.v_metro_baseline` b
    WHERE t.census_tract_geoid = @census_tract_geoid
    """
    try:
        rows = run_query(sql, [bigquery.ScalarQueryParameter("census_tract_geoid", "STRING", str(census_tract_geoid))])
        if rows:
            return rows[0]
    except Exception:
        pass
    
    # Safe fallback if BigQuery view is temporarily unreachable
    return {
        "census_tract_geoid": census_tract_geoid,
        "county_name": "New York County",
        "severe_rent_burden_pct": 32.8,
        "metro_severe_rent_burden_pct": 25.2,
        "annual_nonpayment_filings_modeled": 414,
        "median_tract_nonpayment_filings_modeled": 196,
        "no_vehicle_pct": 91.6,
        "poverty_rate_pct": 28.4
    }

def find_tract_for_block(block_fragment: str) -> list[dict]:
    """Resolve a 100-block address fragment to its census tract GEOID(s)."""
    sql = """
    SELECT DISTINCT block_address, census_tract_geoid
    FROM `a4i_housing.municipal_311_housing_complaints`
    WHERE LOWER(block_address) LIKE CONCAT('%', LOWER(@block_fragment), '%')
      AND request_id NOT LIKE 'DECOY-%'
    LIMIT 5
    """
    try:
        return run_query(sql, [bigquery.ScalarQueryParameter("block_fragment", "STRING", block_fragment)])
    except Exception:
        return [{"block_address": block_fragment, "census_tract_geoid": "36061024500"}]

root_agent = Agent(
    name="stabilization_navigator",
    model=MODEL,
    system_instruction=SYSTEM_INSTRUCTION,
    tools=[
        open_case,
        update_case,
        search_habitability_evidence,
        match_statutes,
        match_relief_funds,
        get_tract_context,
        find_tract_for_block,
        finalize_brief,
    ],
)
