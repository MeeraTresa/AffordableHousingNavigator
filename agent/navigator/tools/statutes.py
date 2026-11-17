from google.cloud import bigquery
from google.adk.tools import ToolContext
from ..bq import run_query


STATUTE_URLS = {
    "STAT-NY-01": "https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCadmin/0-0-0-48227",
    "STAT-NY-02": "https://www.nysenate.gov/legislation/laws/RPP/235-B",
    "STAT-NY-03": "https://www.nysenate.gov/legislation/laws/SOS/143-B",
}

STATUTE_SQL = """
SELECT base.statute_section_id, base.jurisdiction, base.code_citation, base.ordinance_title,
       base.raw_statute_text, ROUND(1 - distance, 4) AS similarity
FROM VECTOR_SEARCH(
  TABLE `a4i_housing.statutes_embedded`, 'embedding',
  (SELECT AI.EMBED(@q, connection_id => 'us.a4i-vertex', endpoint => 'gemini-embedding-2').result AS v),
  query_column_to_search => 'v', top_k => 3, distance_type => 'COSINE', options => '{"use_brute_force":true}')
ORDER BY distance
"""

def match_statutes(tool_context: ToolContext) -> dict:
    """Rank this metro's housing statutes against the case's hazards + nonpayment posture
    using vector search. Returns citations plus procedural checks the record can't answer."""
    case = tool_context.state["case"]
    q = (f"Nonpayment eviction defense; tenant has hazardous conditions: {', '.join(case['hazards'])}. "
         f"Rent abatement, repair deadlines, complete defense for uncorrected violations, right to counsel.")
    rows = run_query(STATUTE_SQL, [bigquery.ScalarQueryParameter("q", "STRING", q)])
    for r in rows:
        sid = r.get("statute_section_id")
        r["statute_url"] = STATUTE_URLS.get(sid, "https://www.nysenate.gov/legislation/laws")
    case["statutes"] = rows
    # Deterministic procedural checks tied to known NY citations
    checks = []
    if any("711" in r["code_citation"] for r in rows) and \
       case["household"].get("received_written_rent_demand") is None:
        checks.append("Confirm tenant received a 14-day WRITTEN rent demand before filing (RPAPL § 711(2)). "
                      "Not provable from public records.")
    if any("27-2115" in r["code_citation"] for r in rows):
        checks.append("Class C (heat/hot water) must be corrected within 24 hours; Class B within 30 days. "
                      "Compare against violation created_date.")
    case["open_questions"] += checks
    tool_context.state["case"] = case
    return {"statutes": rows, "procedural_checks": checks,
            "disclaimer": "Statutory summaries support internal triage, not legal advice."}
