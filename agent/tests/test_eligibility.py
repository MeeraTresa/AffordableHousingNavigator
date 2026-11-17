from unittest.mock import MagicMock
from agent.navigator.tools.case_file import open_case, update_case
from agent.navigator.tools.funds import match_relief_funds

def test_marisol_eligibility():
    # Marisol fixture: Household 3, income $31,000, arrears $3,350, has court index number, 3 open evidence records
    ctx = MagicMock()
    ctx.state = {}
    open_case(
        block_address="1000 Block St Nicholas Avenue",
        hearing_datetime="2026-11-23T09:30",
        hazards=["no heat", "mold around tub", "water leak through wall"],
        tenant_narrative="Radiators cold since November, visible mold around tub, leak in bathroom wall",
        tool_context=ctx,
        census_tract_geoid="36061024500"
    )
    update_case(
        tool_context=ctx,
        household_size=3,
        annual_income_usd=31000.0,
        arrears_usd=3350.0,
        has_court_index_number=True,
        received_written_rent_demand=True
    )
    # Mock kept evidence
    ctx.state["case"]["evidence"] = [
        {"request_id": "NYC-19346259"},
        {"request_id": "NYC-19346354"},
        {"request_id": "NYC-19346353"}
    ]

    res = match_relief_funds(ctx)
    funds = {f["bulletin_id"]: f["status"] for f in res["funds"]}
    print("Marisol fund verdicts with evidence:", funds)

    assert funds["BUL-NY-01"] == "ELIGIBLE"  # One Shot Deal
    assert funds["BUL-NY-02"] == "ELIGIBLE"  # Right to Counsel & Class C
    assert funds["BUL-NY-03"] == "ELIGIBLE"  # CityFHEPS
    assert funds["BUL-NY-04"] == "ELIGIBLE"  # ERP clinic

    # Under-reporting fallback: no open evidence records
    ctx.state["case"]["evidence"] = []
    res_no_ev = match_relief_funds(ctx)
    funds_no_ev = {f["bulletin_id"]: f["status"] for f in res_no_ev["funds"]}
    print("Verdicts with 0 evidence:", funds_no_ev)

    assert funds_no_ev["BUL-NY-01"] == "ELIGIBLE"
    assert funds_no_ev["BUL-NY-02"] == "INELIGIBLE"  # requires open habitability case
    assert funds_no_ev["BUL-NY-03"] == "ELIGIBLE"
    assert funds_no_ev["BUL-NY-04"] == "INELIGIBLE"  # requires open habitability case

    print("test_marisol_eligibility PASSED!")

if __name__ == "__main__":
    test_marisol_eligibility()
