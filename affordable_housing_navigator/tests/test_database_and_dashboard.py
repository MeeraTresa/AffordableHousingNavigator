"""Test Database persistence, Living Brief editing, and Caseworker Dashboard."""

from fastapi.testclient import TestClient
from affordable_housing_navigator.core.database import case_repo, CaseDocument
from affordable_housing_navigator.app.main import app

client = TestClient(app)


def test_list_cases_api():
    res = client.get("/api/cases")
    assert res.status_code == 200
    cases = res.json()
    assert len(cases) >= 4
    marisol = next(c for c in cases if c["case_id"] == "case-lt-029481-26")
    assert marisol["tenant_name"] == "Marisol V."
    assert marisol["claimed_arrears"] == 3350.0


def test_get_single_case_api():
    res = client.get("/api/cases/case-lt-018274-26")
    assert res.status_code == 200
    case = res.json()
    assert case["court_index_number"] == "LT-018274/26/BX"
    assert "Case Brief: Hector M." in case["brief_markdown"]


def test_update_brief_api():
    # Save an edit to the living brief
    new_text = "# Edited Brief\n\nCaseworker added supplemental inspection notes for Monday."
    res = client.post("/api/cases/case-lt-029481-26/brief", json={
        "brief_markdown": new_text,
        "caseworker_notes": "Added tenant witness testimony."
    })
    assert res.status_code == 200
    updated = res.json()
    assert updated["brief_markdown"] == new_text
    assert updated["brief_edits_count"] >= 1
    assert updated["caseworker_notes"] == "Added tenant witness testimony."

    # Verify retrieval from DB confirms updated text
    check = client.get("/api/cases/case-lt-029481-26").json()
    assert check["brief_markdown"] == new_text


def test_create_and_delete_case_api():
    # Create new case
    new_case_payload = {
        "case_id": "case-test-9999",
        "court_index_number": "LT-999999/26/NY",
        "tenant_name": "Carlos R.",
        "block_address": "400 Block of W 145th St",
        "metro_area": "New York",
        "census_tract_geoid": "36061023700",
        "hearing_date": "2026-11-28",
        "hearing_time": "09:30 AM",
        "claimed_arrears": 2900.0,
        "hazard_narrative": "Radiators banging and leaking water onto floor.",
        "status": "Active Intake",
        "urgency_level": "High"
    }
    res_create = client.post("/api/cases", json=new_case_payload)
    assert res_create.status_code == 200
    created = res_create.json()
    assert created["case_id"] == "case-test-9999"

    # Verify listed
    res_list = client.get("/api/cases?search=Carlos")
    assert any(c["case_id"] == "case-test-9999" for c in res_list.json())

    # Delete case
    res_del = client.delete("/api/cases/case-test-9999")
    assert res_del.status_code == 200
    assert res_del.json()["success"] is True

    # Verify not found
    res_get = client.get("/api/cases/case-test-9999")
    assert res_get.status_code == 404


def test_dashboard_stats_api():
    res = client.get("/api/dashboard/stats")
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_cases"] >= 4
    assert stats["total_arrears"] > 0
    assert "hearings_this_week" in stats
