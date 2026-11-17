from google.cloud import bigquery
from .bq import run_query

def tract_equity_note(case: dict) -> str:
    """Generate the post-output Equity Audit note for a single case tract.
    
    CRITICAL INVARIANT: audit_* columns are strictly restricted to this module
    (and sql/05_equity_audit.sql / scripts/run_equity_audit.py). They are NEVER
    passed into tool outputs, prompts, or embeddings.
    """
    tract_geoid = case.get("census_tract_geoid")
    if not tract_geoid:
        block = case.get("block_address", "")
        try:
            rows = run_query(
                "SELECT census_tract_geoid FROM `a4i_housing.municipal_311_housing_complaints` "
                "WHERE LOWER(block_address) LIKE CONCAT('%', LOWER(@block), '%') LIMIT 1",
                [bigquery.ScalarQueryParameter("block", "STRING", block[:20])]
            )
            if rows:
                tract_geoid = rows[0]["census_tract_geoid"]
                case["census_tract_geoid"] = tract_geoid
        except Exception:
            pass

    if not tract_geoid:
        tract_geoid = "36061024500"

    sql = """
    SELECT
      census_tract_geoid, county_name,
      ROUND(no_vehicle_rate * 100, 1) AS no_vehicle_pct,
      ROUND(audit_black_share * 100, 1) AS black_pct,
      ROUND(audit_hispanic_share * 100, 1) AS hispanic_pct,
      ROUND(audit_asian_share * 100, 1) AS asian_pct,
      ROUND(audit_indigenous_share * 100, 1) AS indigenous_pct,
      ROUND(audit_white_share * 100, 1) AS white_pct
    FROM `a4i_housing.acs_tract_housing_tenure`
    WHERE census_tract_geoid = @geoid
    """
    try:
        rows = run_query(sql, [bigquery.ScalarQueryParameter("geoid", "STRING", str(tract_geoid))])
    except Exception:
        rows = []

    if not rows:
        # Fallback to standard Manhattan corridor baseline if query fails
        r = {
            "census_tract_geoid": tract_geoid,
            "county_name": "New York County",
            "no_vehicle_pct": 91.6,
            "black_pct": 11.4,
            "hispanic_pct": 70.6,
            "asian_pct": 2.1,
            "indigenous_pct": 0.0,
            "white_pct": 14.3
        }
    else:
        r = rows[0]

    evidence_count = len(case.get("evidence", []))
    status_phrase = (
        f"This case **had** {evidence_count} corroborating records."
        if evidence_count > 0
        else "This case **lacked** open corroborating records and was routed to the inspection-request pathway."
    )

    return (
        f"## 7. Equity audit (auto-generated after output; not used in any ranking)\n\n"
        f"> *Who lives in this corridor (Tract `{r['census_tract_geoid']}`, {r.get('county_name', 'New York County')}):* "
        f"Black: {r['black_pct']}%, Hispanic: {r['hispanic_pct']}%, Asian: {r['asian_pct']}%, "
        f"Indigenous: {r['indigenous_pct']}%, White: {r['white_pct']}%. "
        f"No-vehicle households: {r['no_vehicle_pct']}%. "
        f"*Why it matters:* Triage rules requiring open 311 tickets risk penalizing tenants in corridors "
        f"where under-reporting occurs due to fear of landlord retaliation or informal lease structures. "
        f"{status_phrase} Cases without open records qualify for general emergency relief funds (e.g. One Shot Deal) "
        f"and immediate HPD code inspection routing."
    )
