from .bq import run_query
from google.cloud import bigquery

# Hard rule 4: audit_* columns may only be read here and sql/05_equity_audit.sql
_EQUITY_SQL = """
SELECT
  a.census_tract_geoid,
  ROUND(a.audit_black_share * 100, 1)    AS black_pct,
  ROUND(a.audit_hispanic_share * 100, 1) AS hispanic_pct,
  ROUND(a.audit_asian_share * 100, 1)    AS asian_pct,
  ROUND(a.audit_white_share * 100, 1)    AS white_pct,
  ROUND(a.no_vehicle_rate * 100, 1)      AS no_vehicle_pct
FROM `a4i_housing.acs_tract_housing_tenure` a
WHERE a.census_tract_geoid = @geoid
"""

def tract_equity_note(case: dict) -> str:
    """Post-output equity note rendered purely by code.
    NEVER feeds back into retrieval, ranking or prompts."""
    geoid = case.get("census_tract_geoid")
    if not geoid:
        return ""
    rows = run_query(_EQUITY_SQL, [bigquery.ScalarQueryParameter("geoid", "STRING", geoid)])
    if not rows:
        return ""
    r = rows[0]
    had_corroboration = len(case.get("evidence", [])) > 0
    triage_route = (
        "This case **had** corroborating records."
        if had_corroboration
        else "No open 311 records were found; this case was routed to the inspection-request pathway."
    )
    return (
        f"## 7. Equity audit (auto-generated after output; not used in any ranking)\n\n"
        f"**Who lives in this corridor (Tract `{geoid}`):**\n"
        f"- Demographics: Hispanic {r['hispanic_pct']}%, Black {r['black_pct']}%, Asian {r['asian_pct']}%, White {r['white_pct']}%\n"
        f"- Transit reliance: {r['no_vehicle_pct']}% of households have no vehicle available\n\n"
        f"**Why it matters:** Triage rules requiring open 311 complaints may under-serve communities with fear of landlord retaliation or language barriers. "
        f"{triage_route}"
    )
