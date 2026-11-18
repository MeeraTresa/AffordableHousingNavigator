"""Test emergency rental relief program eligibility rules."""

import pytest
from affordable_housing_navigator.core.case_intake import TenantCase, CorroboratedEvidence
from affordable_housing_navigator.core.relief_funds import evaluate_relief_programs


def test_habitability_gate_locks_and_unlocks_funds():
    """Verify that requires_open_habitability_case locks funds without evidence and unlocks with evidence."""
    tc = TenantCase(
        block_address="1000 Block of St. Nicholas Ave",
        hazard_narrative="Radiators cold",
        claimed_arrears=3000,
        household_size=3,
        annual_income=30000,
    )

    # 1. No corroborated evidence -> habitability funds should not qualify
    funds_no_ev = evaluate_relief_programs(tc, [])
    for f in funds_no_ev:
        if f.requires_open_habitability_case:
            assert f.verdict == "UNQUALIFIED"
            assert "FAILS habitability requirement" in f.rationale

    # 2. Corroborated evidence supplied -> habitability funds unlock
    ev = [
        CorroboratedEvidence(
            request_id="NYC-19346259",
            block_address="900 Block of St. Nicholas Ave",
            property_type="Residential",
            raw_complaint_type="HEAT",
            inspection_status="Open",
            complaint_narrative="Boiler locked, no heat",
            similarity_score=0.92,
            hazard_category="Heat / Boiler",
        )
    ]
    funds_with_ev = evaluate_relief_programs(tc, ev)
    habitability_funds = [f for f in funds_with_ev if f.requires_open_habitability_case]
    assert len(habitability_funds) > 0
    for f in habitability_funds:
        assert f.habitability_satisfied is True
        assert f.verdict == "QUALIFIED"
