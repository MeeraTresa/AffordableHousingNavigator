import pytest
from unittest.mock import MagicMock
from agent.navigator.tools.case_file import open_case
from agent.navigator.tools.evidence import search_habitability_evidence

PHRASINGS = [
    ["no heat", "radiators cold"],
    ["black mold around bathtub", "mold"],
    ["water leak through bathroom wall"],
    ["boiler not working"],
    ["raw sewage backup in bathroom"],
    ["electrical hazard, sparking outlet near water"],
    ["freezing cold apartment, no heat"],
    ["ceiling leak and peeling paint"],
    ["toxic mold and dampness"],
    ["no hot water, boiler locked"],
]

@pytest.mark.parametrize("hazards", PHRASINGS)
def test_decoys_never_kept(hazards):
    context = MagicMock()
    context.state = {}
    open_case(
        block_address="1000 Block St Nicholas Avenue",
        hearing_datetime="2026-11-23T09:30",
        hazards=hazards,
        tenant_narrative="Tenant experiencing severe habitability issues",
        tool_context=context,
        census_tract_geoid="36061024500"
    )
    result = search_habitability_evidence(context, hazards=hazards)
    kept = result["kept"]
    excluded = result["excluded"]

    # Assert no DECOY-* appears in kept
    for item in kept:
        assert not item["request_id"].startswith("DECOY-"), f"Decoy leaked into kept: {item['request_id']}"

    # Assert every DECOY in excluded has an excluded_because reason
    for item in excluded:
        if item["request_id"].startswith("DECOY-"):
            assert "excluded_because" in item
            assert len(item["excluded_because"]) > 0
            assert "[Planted Case]" in item["excluded_because"]
