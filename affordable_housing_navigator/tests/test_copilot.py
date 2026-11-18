"""Test Conversational Co-Pilot and UI generation."""

from fastapi.testclient import TestClient
from affordable_housing_navigator.core.copilot import ConversationalCoPilot
from affordable_housing_navigator.app.main import app


def test_copilot_direct_message_processing():
    copilot = ConversationalCoPilot()
    resp = copilot.process_message("I am working with Marisol on 1000 Block of St. Nicholas Ave. Generate UI")
    assert resp.ui_generated is True
    assert resp.ui_data is not None
    assert "Building Identified" in resp.reply
    assert len(resp.suggestions) > 0
    assert "LT-029481/26" in resp.ui_data["tenant_case"]["court_index_number"]


def test_copilot_statutes_query():
    copilot = ConversationalCoPilot()
    resp = copilot.process_message("What legal defenses and statutes apply to freezing radiators and mold?")
    assert "235-b" in resp.reply or "Warranty of Habitability" in resp.reply
    assert "27-2115" in resp.reply or "Class C" in resp.reply


def test_copilot_relief_funds_query():
    copilot = ConversationalCoPilot()
    resp = copilot.process_message("What relief grants and emergency funds can help with $3350 arrears?")
    assert "One Shot Deal" in resp.reply
    assert "Emergency Repair" in resp.reply


def test_api_chat_endpoint_generates_ui():
    client = TestClient(app)
    res = client.post("/api/chat", json={
        "session_id": "test-sess-1",
        "message": "Generate UI for Marisol Monday case"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["ui_generated"] is True
    assert "ui_data" in data
    assert data["ui_data"]["tenant_case"]["block_address"] == "1000 Block of St. Nicholas Ave"
    assert len(data["ui_data"]["corroborated_evidence"]) > 0


def test_multimodal_inspection_endpoints():
    client = TestClient(app)
    
    # Vision inspect photo
    res_photo = client.post("/api/vision/inspect", json={"image_base64": "dummy", "mime_type": "image/jpeg"})
    assert res_photo.status_code == 200
    pdata = res_photo.json()
    assert "severity_class" in pdata
    assert "evidentiary_boundary" in pdata

    # Notice OCR
    res_notice = client.post("/api/vision/notice", json={"image_base64": "dummy", "mime_type": "image/jpeg"})
    assert res_notice.status_code == 200
    ndata = res_notice.json()
    assert ndata["court_index_number"] == "LT-029481/26"
    assert ndata["claimed_arrears"] == 3350.0

    # Audio transcription
    res_audio = client.post("/api/audio/process", json={"audio_base64": "dummy", "mime_type": "audio/webm"})
    assert res_audio.status_code == 200
    adata = res_audio.json()
    assert "radiators have been cold" in adata["transcript"]
