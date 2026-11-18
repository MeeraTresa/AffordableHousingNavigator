import pytest
from agent.navigator.tools.case_file import open_case
from agent.navigator.tools.evidence import search_habitability_evidence

class MockToolContext:
    def __init__(self):
        self.state = {}

HAZARD_TEST_CASES = [
    ["no heat", "radiators cold"],
    ["black mold around bathtub"],
    ["water leak through bathroom wall"],
    ["broken boiler no hot water"],
    ["sewage backup in toilet"],
    ["defective electrical outlet exposed wiring"],
    ["roaches and mice rodent infestation"],
    ["ceiling collapse water damage"],
    ["freezing apartment heating system broken"],
    ["leaking pipe mold growth"],
]

@pytest.mark.parametrize("hazards", HAZARD_TEST_CASES)
def test_no_decoys_kept_and_all_excluded_explained(hazards):
    tc = MockToolContext()
    open_case(
        block_address="1000 Block St Nicholas Avenue, Manhattan",
        hearing_datetime="2026-11-23T09:30",
        hazards=hazards,
        tenant_narrative="Tenant reports severe conditions.",
        tool_context=tc,
    )
    result = search_habitability_evidence(tool_context=tc)
    
    kept = result["kept"]
    excluded = result["excluded"]
    
    # 1. Assert no DECOY-* id is ever in kept
    for item in kept:
        assert not item["request_id"].startswith("DECOY-"), (
            f"Planted decoy {item['request_id']} was admitted into kept evidence for hazards {hazards}!"
        )
    
    # 2. Assert every DECOY-* in excluded has an excluded_because reason explaining why
    for item in excluded:
        if item["request_id"].startswith("DECOY-"):
            assert "excluded_because" in item, f"Decoy {item['request_id']} missing excluded_because"
            assert len(item["excluded_because"]) > 0, f"Decoy {item['request_id']} has empty excluded_because"
            assert "[Planted Case]" in item["excluded_because"], f"Decoy {item['request_id']} missing [Planted Case] tag"
