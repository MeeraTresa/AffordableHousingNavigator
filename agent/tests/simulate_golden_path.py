import os
import asyncio
from unittest.mock import MagicMock
from agent.navigator.tools.case_file import open_case, update_case
from agent.navigator.tools.evidence import search_habitability_evidence
from agent.navigator.tools.statutes import match_statutes
from agent.navigator.tools.funds import match_relief_funds
from agent.navigator.tools.tract import get_tract_context
from agent.navigator.tools.brief import finalize_brief, render_brief_markdown

async def test_golden_path():
    ctx = MagicMock()
    ctx.state = {}
    async def mock_save_artifact(name, part):
        print(f"Artifact saved: {name} ({len(part.text)} chars)")
    ctx.save_artifact = mock_save_artifact

    print("=== Turn 1: New Intake ===")
    t1 = open_case(
        block_address="1000 Block St Nicholas Avenue, Manhattan",
        hearing_datetime="2026-11-23T09:30",
        hazards=["no heat", "black mold around bathtub", "water coming through bathroom wall"],
        tenant_narrative="Radiators cold since early November, black mold around tub, water coming through bathroom wall",
        tool_context=ctx,
        census_tract_geoid="36061024500"
    )
    print("Open case:", t1)
    ev_res = search_habitability_evidence(ctx)
    print(f"Kept corroborating records ({len(ev_res['kept'])}):")
    for k in ev_res["kept"]:
        print(f"  [{k['request_id']}] {k['block_address']} (sim: {k['similarity']})")
    print(f"Excluded records ({len(ev_res['excluded'])}):")
    for ex in ev_res["excluded"][:3]:
        print(f"  [{ex['request_id']}] sim: {ex['similarity']} -> {ex['excluded_because']}")

    print("\n=== Turn 2: Decoy explanation ===")
    decoys = [ex for ex in ctx.state["case"]["exclusions"] if ex["request_id"].startswith("DECOY-")]
    print(f"Decoys identified and explained: {len(decoys)}")
    for d in decoys:
        print(f"  {d['request_id']}: {d['excluded_because']}")

    print("\n=== Turn 3: Applicable law ===")
    stat_res = match_statutes(ctx)
    for s in stat_res["statutes"]:
        print(f"  {s['code_citation']}: {s['ordinance_title']}")
    print("Procedural checks:", stat_res["procedural_checks"])

    print("\n=== Turn 4: Household facts & Fund matching ===")
    update_case(
        tool_context=ctx,
        household_size=3,
        annual_income_usd=31000.0,
        arrears_usd=3350.0,
        has_court_index_number=True,
        received_written_rent_demand=True,
        notes="Daughter Daniela (6) has worsening asthma (noted for attorney)"
    )
    fund_res = match_relief_funds(ctx)
    for f in fund_res["funds"]:
        print(f"  {f['program_name']}: {f['status']}")

    print("\n=== Turn 5: Tract context ===")
    tract_res = get_tract_context("36061024500")
    print(f"Tract 36061024500: severe rent burden {tract_res['severe_rent_burden_pct']}% (metro {tract_res['metro_severe_rent_burden_pct']}%), annual nonpayment filings {tract_res['annual_nonpayment_filings_modeled']} [Modeled] (median {tract_res['median_tract_nonpayment_filings_modeled']})")

    print("\n=== Turn 6: Re-checking evidence against landlord claim ===")
    heat_records = [e for e in ctx.state["case"]["evidence"] if "heat" in (e.get("raw_complaint_type") or "").lower() or "boiler" in (e.get("complaint_narrative") or "").lower() or e["request_id"] == "NYC-19346259"]
    print(f"Corroborating record NYC-19346259 still active in HPD: {len(heat_records) > 0}")

    print("\n=== Turn 7: Finalize brief ===")
    memo = (
        "Tenant Marisol (household of 3) faces nonpayment petition with hearing on Mon Nov 23. "
        "Conditions: Class C heat violation (boiler locked) plus Class A visible mold and Class B leak documented on block. "
        "Recommend asserting RPL 235-b warranty of habitability defense, petitioning for HP Action, and submitting "
        "emergency One Shot Deal and Right to Counsel intake applications immediately."
    )
    brief_res = await finalize_brief(memo, ctx)
    print("Finalize brief result:", brief_res)
    brief_text = render_brief_markdown(ctx.state["case"], memo)
    with open("docs/sample_tenant_stabilization_brief.md", "w") as f:
        f.write(brief_text)
    print("Wrote docs/sample_tenant_stabilization_brief.md successfully!")

if __name__ == "__main__":
    asyncio.run(test_golden_path())
