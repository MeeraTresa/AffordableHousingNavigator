"""End-to-end integration test of tenant case intake and brief generation."""

import pytest
from affordable_housing_navigator.core.case_intake import TenantCase, CaseIntakeSession
from affordable_housing_navigator.core import vector_search, statutes, relief_funds, tract_context, brief_builder


def test_full_marisol_intake_flow():
    """Test full intake workflow for composite case: Marisol on St. Nicholas Ave."""
    tc = TenantCase(
        metro_area="New York",
        block_address="1000 Block of St. Nicholas Ave",
        census_tract_geoid="36061024500",
        hearing_date="2026-11-23",
        hearing_time="09:30 AM",
        claimed_arrears=3350.0,
        notice_type="Nonpayment Petition",
        court_index_number="LT-029481/26",
        household_size=3,
        annual_income=31000.0,
        hazard_narrative="Radiators cold since early Nov. Black mold around tub. Water coming through bathroom wall from upstairs.",
        landlord_notified_date="2026-11-05",
        tenant_language="Spanish",
    )

    # 1. Search habitability evidence
    kept_ev, excluded = vector_search.search_habitability_evidence(
        query=tc.hazard_narrative,
        metro_area=tc.metro_area,
        tenant_block=tc.block_address,
        top_k=20,
    )
    assert len(kept_ev) > 0
    assert len(excluded) > 0

    # 2. Match statutes
    statute_matches = statutes.match_statutory_defenses(tc, kept_ev)
    assert len(statute_matches) == 3

    # 3. Evaluate relief funds
    funds = relief_funds.evaluate_relief_programs(tc, kept_ev)
    assert len(funds) == 4
    qualified_funds = [f for f in funds if f.verdict == "QUALIFIED"]
    assert len(qualified_funds) >= 3

    # 4. Get tract context
    tract_prof = tract_context.get_tract_risk_profile(tc.metro_area, census_tract_geoid=tc.census_tract_geoid)
    assert tract_prof.census_tract_geoid == "36061024500"
    assert tract_prof.severe_rent_burden_rate > 0.30
    assert tract_prof.transit_barrier_warning is True  # 91.6% no car

    # 5. Build session & brief
    session = CaseIntakeSession(
        session_id="INTAKE-MARISOL-01",
        tenant_case=tc,
        corroborated_evidence=kept_ev,
        excluded_matches=excluded,
        applicable_statutes=statute_matches,
        eligible_funds=funds,
        tract_profile=tract_prof,
    )
    brief = brief_builder.build_tenant_stabilization_brief(session)

    assert "TENANT STABILIZATION BRIEF" in brief
    assert "3,350.00" in brief
    assert "Warranty of Habitability" in brief
    assert "Class C" in brief
    assert "Evidentiary Boundaries" in brief
    assert "Courthouse Transit Barrier Alert" in brief
