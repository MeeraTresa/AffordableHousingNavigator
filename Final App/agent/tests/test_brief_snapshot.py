import pytest
from agent.navigator.tools.brief import render_brief_markdown
from agent.navigator.equity import tract_equity_note

def test_brief_markdown_structure():
    """Verify render_brief_markdown produces exactly the Part B §11 structure."""
    case = {
        "block_address": "1000 Block St Nicholas Avenue",
        "census_tract_geoid": "36061024500",
        "hearing_datetime": "2026-11-23T09:30",
        "hours_to_hearing": 89.0,
        "hazards": ["no heat", "black mold around bathtub", "water leak at bathroom wall"],
        "tenant_narrative": "Radiators cold, mold behind bathroom tile, leak into ceiling.",
        "household": {
            "household_size": 3,
            "annual_income_usd": 31000.0,
            "arrears_usd": 3350.0,
            "has_court_index_number": True,
            "received_written_rent_demand": True,
        },
        "evidence": [
            {
                "request_id": "NYC-19346259",
                "block_address": "900 Block St Nicholas Ave",
                "raw_complaint_type": "HPD Class C — heating system access (boiler room locked)",
                "inspection_status": "Open",
                "created_date": "2026-11-01",
                "similarity": 0.71,
            },
            {
                "request_id": "NYC-19346354",
                "block_address": "1000 Block St Nicholas Ave",
                "raw_complaint_type": "HPD Class A — visible mold around bathtub",
                "inspection_status": "Open",
                "created_date": "2026-11-01",
                "similarity": 0.78,
            },
            {
                "request_id": "NYC-19346353",
                "block_address": "1000 Block St Nicholas Ave",
                "raw_complaint_type": "HPD Class B — water leak at bathroom wall",
                "inspection_status": "Open",
                "created_date": "2026-11-01",
                "similarity": 0.74,
            },
        ],
        "exclusions": [
            {
                "request_id": "DECOY-NEWY-04",
                "similarity": 0.80,
                "excluded_because": "Closed – Abated — condition was repaired and re-inspected; not an active hazard. Labeled [Planted Case] teaching decoy.",
            },
            {
                "request_id": "DECOY-NEWY-01",
                "similarity": 0.77,
                "excluded_because": "Commercial property — no residential tenants; cannot support a residential habitability defense. Labeled [Planted Case] teaching decoy.",
            },
            {
                "request_id": "DECOY-NEWY-07",
                "similarity": 0.69,
                "excluded_because": "Closed – No Violation — inspector found no defect; this record would undercut, not support, the claim. Labeled [Planted Case] teaching decoy.",
            },
        ],
        "statutes": [
            {
                "code_citation": "RPL § 235-b / RPAPL § 711(2)",
                "ordinance_title": "Warranty of Habitability",
                "raw_statute_text": "warranty of habitability → rent abatement; 14-day written demand prerequisite.",
            },
            {
                "code_citation": "NYC Admin. Code § 27-2115 / § 26-1302",
                "ordinance_title": "Housing Maintenance Code Violation Remedy",
                "raw_statute_text": "Class C correction within 24 h (Class B: 30 days); Right to Counsel ≤200% FPL.",
            },
        ],
        "funds": [
            {
                "bulletin_id": "BUL-NY-02",
                "program_name": "Right to Counsel & HPD Class C Defense",
                "status": "ELIGIBLE",
                "checks": [{"rule": "Open habitability case", "pass": True, "detail": "Open HPD violation; $31,000 ≤ 200% FPL"}],
                "max_award_usd": 4000,
                "intake_url": "legalaidnyc.org",
            }
        ],
        "open_questions": [],
    }

    memo = "Tenant Marisol Rodriguez faces imminent eviction hearing Monday 9:30 AM."
    md = render_brief_markdown(case, memo)
    equity = tract_equity_note(case)
    full_doc = md + "\n\n" + equity

    # Assert exact required sections in order
    assert "# Tenant Stabilization Brief" in full_doc
    assert "## 1. Corroborating public records" in full_doc
    assert "### Near-matches excluded (and why)" in full_doc
    assert "## 2. Applicable law" in full_doc
    assert "## 3. Emergency relief match" in full_doc
    assert "## 4. Neighborhood context" in full_doc
    assert "## 5. Evidentiary boundary" in full_doc
    assert "## 6. Intake memo (draft for attorney)" in full_doc
    assert "## 7. Equity audit" in full_doc

    # Check key content elements
    assert "NYC-19346259" in full_doc
    assert "DECOY-NEWY-04" in full_doc
    assert "[Planted Case]" in full_doc
    assert "[Modeled]" in full_doc
