"""FastAPI web server for Hearth · Housing-Court Intake Partner, Living Brief Workspace,
and Caseworker Case Management Dashboard.

Features:
- Full CRUD database persistence (SQLite with Firebase Firestore collection schema)
- In-place editable Living Tenant Stabilization Brief
- Caseworker Dashboard with KPI cards, multi-case table, urgency trackers, and search
- Seamless switching between Caseworker Dashboard and Hearth Workspace
"""

import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from .. import config
from ..core.agents import CommandCentreCoordinator
from ..core.building_mapper import resolve_building_location, clean_address_strip_units
from ..core.copilot import ConversationalCoPilot, ChatTurnRequest
from ..core.database import case_repo, CaseDocument
from ..translation import translator

app = FastAPI(
    title="Hearth · Housing-Court Intake Partner & Case Management System",
    description="Conversational Intake, Editable Living Briefs, and Caseworker Dashboard",
    version="4.5.0",
)

copilot = ConversationalCoPilot()


# ---------------------------------------------------------------------------
# Pydantic Request Models
# ---------------------------------------------------------------------------

class BriefUpdateRequest(BaseModel):
    brief_markdown: str
    caseworker_notes: Optional[str] = None


class BuildingResolveRequest(BaseModel):
    address: str
    metro_area: str = "New York"
    census_tract_geoid: Optional[str] = None


class MultimodalInspectRequest(BaseModel):
    image_base64: str = ""
    mime_type: str = "image/jpeg"
    hazard_hint: Optional[str] = "mold and leak"


class AudioProcessRequest(BaseModel):
    audio_base64: str = ""
    mime_type: str = "audio/webm"


# ---------------------------------------------------------------------------
# Case Management & Database API Endpoints (Firestore Schema)
# ---------------------------------------------------------------------------

@app.get("/api/cases")
async def list_cases(status: Optional[str] = None, search: Optional[str] = None):
    """Retrieve all tenant cases from database with optional status/search filters."""
    return case_repo.list_cases(status=status, search_query=search)


@app.get("/api/cases/{case_id}")
async def get_single_case(case_id: str):
    """Retrieve a single case by ID with full living brief, evidence, and notes."""
    case = case_repo.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case.model_dump()


@app.post("/api/cases")
async def create_case(case_doc: CaseDocument):
    """Create or import a new tenant case into database."""
    saved = case_repo.save_case(case_doc)
    return saved.model_dump()


@app.put("/api/cases/{case_id}")
async def update_case(case_id: str, case_doc: CaseDocument):
    """Update case metadata, hearing date, or intake state."""
    case_doc.case_id = case_id
    saved = case_repo.save_case(case_doc)
    return saved.model_dump()


@app.post("/api/cases/{case_id}/brief")
async def update_case_brief(case_id: str, req: BriefUpdateRequest):
    """Save edits made by caseworker to the Living Tenant Stabilization Brief."""
    updated = case_repo.update_brief(
        case_id=case_id,
        new_brief_markdown=req.brief_markdown,
        notes=req.caseworker_notes
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Case not found")
    return updated.model_dump()


@app.delete("/api/cases/{case_id}")
async def delete_case(case_id: str):
    """Archive or delete a case from database."""
    success = case_repo.delete_case(case_id)
    if not success:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"success": True, "case_id": case_id}


@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Compute KPI metrics across all cases in the database."""
    cases = case_repo.list_cases()
    total_cases = len(cases)
    total_arrears = sum(c.get("claimed_arrears", 0.0) for c in cases)
    critical_count = sum(1 for c in cases if c.get("urgency_level") == "Critical" or "Ready" in c.get("status", ""))
    
    # Calculate relief matched estimate ($15k max per qualified case)
    total_relief = sum(15000.0 for c in cases if c.get("claimed_arrears", 0) > 0)

    return {
        "total_cases": total_cases,
        "hearings_this_week": critical_count,
        "total_arrears": total_arrears,
        "total_relief_matched": total_relief,
    }


# ---------------------------------------------------------------------------
# Conversational Co-Pilot & Multimodal Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/chat")
async def chat_endpoint(req: ChatTurnRequest):
    """Conversational turn with Hearth; extracts facts and updates the living brief."""
    resp = copilot.process_message(
        message=req.message,
        session_id=req.session_id,
        current_case=req.current_case
    )
    return resp.model_dump()


@app.post("/api/generate_ui")
async def generate_ui_endpoint(req: Dict[str, Any]):
    """Explicitly trigger multi-agent pipeline and generate full living brief workspace."""
    resp = copilot.process_message(
        message="Generate UI",
        session_id=req.get("session_id", "default"),
        current_case=req.get("case_state")
    )
    return resp.model_dump()


@app.post("/api/vision/inspect")
async def vision_inspect_endpoint(req: MultimodalInspectRequest):
    """Inspect tenant condition photo with forensic severity classification and evidentiary boundary."""
    return copilot.inspect_photo(image_base64=req.image_base64, mime_type=req.mime_type)


@app.post("/api/vision/notice")
async def vision_notice_endpoint(req: MultimodalInspectRequest):
    """Extract court hearing details from rent demand or Notice of Petition."""
    return copilot.extract_court_notice(image_base64=req.image_base64, mime_type=req.mime_type)


@app.post("/api/audio/process")
async def audio_process_endpoint(req: AudioProcessRequest):
    """Transcribe tenant audio intake statement into structured facts."""
    return copilot.process_audio(audio_base64=req.audio_base64, mime_type=req.mime_type)


@app.post("/api/resolve_building")
async def resolve_building_endpoint(req: BuildingResolveRequest):
    """Resolve building address to coordinates and Google Maps URLs while stripping apartment numbers."""
    return resolve_building_location(
        raw_address=req.address,
        metro_area=req.metro_area,
        census_tract_geoid=req.census_tract_geoid,
    )


@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
async def serve_app():
    """Render unified Hearth Workspace and Caseworker Case Management Dashboard."""
    return HTML_CONTENT


# ---------------------------------------------------------------------------
# Web UI Template
# ---------------------------------------------------------------------------

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Hearth · Housing-Court Intake Partner & Case Dashboard</title>
  
  <!-- USWDS Public Sans, Source Serif 4 & IBM Plex Mono -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&display=swap" rel="stylesheet">
  
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
  
  <!-- Leaflet for Interactive Map -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

  <style>
    :root {
      --brand: #1d4ed8;
      --brand-ink: #1e3a8a;
      --brand-soft: #eef3ff;
      --ok: #047857;
      --bad: #b91c1c;
      --warn: #b45309;
      --mono: 'IBM Plex Mono', ui-monospace, monospace;
      --serif: 'Source Serif 4', Georgia, serif;
      --sans: 'Public Sans', system-ui, -apple-system, sans-serif;
      
      --color-background-body: #ffffff;
      --color-background-surface: #ffffff;
      --color-background-muted: #f4f6f9;
      --color-border: #e2e7ee;
      --color-text-primary: #0f1b2d;
      --color-text-secondary: #5b6b80;
      
      --paper-bg: #fbf8f1;
    }

    * { box-sizing: border-box; }
    html, body { height: 100%; margin: 0; padding: 0; }
    body {
      background: var(--color-background-body);
      color: var(--color-text-primary);
      font-family: var(--sans);
      font-size: 14px;
      line-height: 1.5;
      display: flex;
      flex-direction: column;
    }

    /* Civic Topbar */
    .topbar {
      height: 56px;
      flex: none;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 0 20px;
      border-bottom: 1px solid var(--color-border);
      background: var(--color-background-surface);
      z-index: 100;
    }

    .brand { display: flex; align-items: center; gap: 10px; min-width: 0; }
    
    .hearth-mark {
      display: inline-grid;
      place-items: center;
      flex: none;
      width: 28px;
      height: 28px;
      border-radius: 8px;
      background: var(--brand);
      color: #fff;
    }

    .brand-name {
      font-weight: 700;
      font-size: 16px;
      letter-spacing: -0.01em;
      color: var(--brand-ink);
    }

    /* Top Nav Mode Switcher */
    .nav-switcher {
      display: flex;
      background: var(--color-background-muted);
      border-radius: 8px;
      padding: 3px;
      border: 1px solid var(--color-border);
    }

    .nav-btn {
      all: unset;
      padding: 5px 14px;
      font-size: 13px;
      font-weight: 600;
      color: var(--color-text-secondary);
      cursor: pointer;
      border-radius: 6px;
      transition: all 0.15s;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .nav-btn.active {
      background: #ffffff;
      color: var(--brand-ink);
      box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }

    .case-line {
      font-size: 13px;
      color: var(--color-text-secondary);
      white-space: nowrap;
      font-variant-numeric: tabular-nums;
    }

    .case-line.is-urgent {
      color: var(--bad);
      font-weight: 600;
      background: #fef2f2;
      padding: 3px 8px;
      border-radius: 6px;
      border: 1px solid #fecaca;
    }

    /* VIEW CONTAINERS */
    .view-pane {
      flex: 1;
      min-height: 0;
      display: none;
    }

    .view-pane.active {
      display: flex;
    }

    /* =====================================================================
       CASEWORKER DASHBOARD VIEW ("THE NEXT APP")
       ===================================================================== */
    .dashboard-view {
      flex-direction: column;
      overflow-y: auto;
      padding: 24px 28px 40px;
      background: var(--color-background-muted);
      width: 100%;
    }

    .dash-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }

    /* Metric KPI Cards */
    .kpi-row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }

    .kpi-card {
      background: #ffffff;
      border: 1px solid var(--color-border);
      border-radius: 10px;
      padding: 16px 20px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }

    .kpi-title { font-size: 12px; font-weight: 600; color: var(--color-text-secondary); text-transform: uppercase; letter-spacing: 0.04em; }
    .kpi-val { font-size: 24px; font-weight: 700; color: var(--color-text-primary); margin: 4px 0; }
    .kpi-sub { font-size: 12px; color: var(--brand-ink); font-weight: 500; }

    /* Search & Filter Bar */
    .filter-card {
      background: #ffffff;
      border: 1px solid var(--color-border);
      border-radius: 10px;
      padding: 14px 20px;
      margin-bottom: 20px;
      display: flex;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
    }

    /* Cases Table */
    .cases-table-wrap {
      background: #ffffff;
      border: 1px solid var(--color-border);
      border-radius: 10px;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }

    .table-cases {
      width: 100%;
      border-collapse: collapse;
      font-size: 13.5px;
    }

    .table-cases th {
      background: #f8fafc;
      padding: 12px 16px;
      font-weight: 600;
      color: var(--color-text-secondary);
      border-bottom: 1px solid var(--color-border);
      text-align: left;
    }

    .table-cases td {
      padding: 14px 16px;
      border-bottom: 1px solid var(--color-border);
      vertical-align: middle;
    }

    .table-cases tr:hover td {
      background: #f8fafc;
    }

    .badge-critical { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
    .badge-high { background: #ffedd5; color: #9a3412; border: 1px solid #fed7aa; }
    .badge-ready { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
    .badge-draft { background: #e0e7ff; color: #3730a3; border: 1px solid #c7d2fe; }

    /* =====================================================================
       HEARTH INTAKE & LIVING BRIEF WORKSPACE
       ===================================================================== */
    .workspace-view {
      overflow: hidden;
    }

    .chat-pane {
      flex: 1;
      min-width: 0;
      min-height: 0;
      display: flex;
      flex-direction: column;
      background: var(--color-background-body);
      border-right: 1px solid var(--color-border);
    }

    .chat-scroll {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .msg-wrap {
      max-width: 760px;
      margin: 0 auto;
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .msg-bubble {
      padding: 14px 18px;
      border-radius: 12px;
      font-size: 14.5px;
      line-height: 1.55;
      word-wrap: break-word;
    }

    .msg-user {
      align-self: flex-end;
      background: var(--brand-soft);
      color: var(--brand-ink);
      border: 1px solid #d4e2ed;
      border-bottom-right-radius: 3px;
      max-width: 85%;
    }

    .msg-hearth {
      align-self: flex-start;
      background: var(--color-background-surface);
      border: 1px solid var(--color-border);
      border-bottom-left-radius: 3px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
      max-width: 92%;
    }

    .msg-hearth-header {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 700;
      font-size: 13.5px;
      color: var(--brand-ink);
      margin-bottom: 6px;
    }

    .suggest-row {
      max-width: 760px;
      margin: 0 auto;
      width: 100%;
      padding: 8px 20px 4px;
      display: flex;
      gap: 8px;
      overflow-x: auto;
    }

    .suggest-chip {
      all: unset;
      cursor: pointer;
      font-size: 12.5px;
      font-weight: 500;
      background: var(--color-background-muted);
      border: 1px solid var(--color-border);
      border-radius: 14px;
      padding: 4px 12px;
      color: var(--color-text-secondary);
      white-space: nowrap;
      transition: all 0.15s;
    }

    .suggest-chip:hover {
      background: var(--brand-soft);
      border-color: #cbd5e1;
      color: var(--brand-ink);
    }

    .composer-wrap {
      padding: 12px 20px 16px;
      border-top: 1px solid var(--color-border);
      background: var(--color-background-surface);
    }

    .composer-inner {
      max-width: 760px;
      margin: 0 auto;
      display: flex;
      gap: 10px;
      position: relative;
    }

    .btn-plus {
      background: var(--color-background-muted);
      border: 1px solid var(--color-border);
      border-radius: 8px;
      width: 40px;
      height: 40px;
      display: grid;
      place-items: center;
      font-size: 1.25rem;
      font-weight: 700;
      color: var(--brand-ink);
      cursor: pointer;
      flex: none;
    }

    .multimodal-popup {
      display: none;
      position: absolute;
      bottom: 52px;
      left: 0;
      background: #ffffff;
      border: 1px solid var(--color-border);
      border-radius: 10px;
      box-shadow: 0 6px 22px rgba(0,0,0,0.1);
      min-width: 260px;
      z-index: 1050;
      overflow: hidden;
    }

    .multimodal-popup.show { display: block; }

    .popup-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 16px;
      font-size: 13px;
      cursor: pointer;
    }

    .popup-item:hover { background-color: var(--brand-soft); color: var(--brand-ink); }

    .composer-input {
      flex: 1;
      background: var(--color-background-muted);
      border: 1px solid var(--color-border);
      border-radius: 8px;
      padding: 9px 14px;
      font-size: 14px;
      outline: none;
    }

    .btn-send {
      background: var(--brand);
      color: #ffffff;
      border: none;
      border-radius: 8px;
      padding: 0 16px;
      font-weight: 600;
      cursor: pointer;
    }

    /* RIGHT COLUMN: LIVING BRIEF WITH EDITING WORKSHEET */
    .brief-pane {
      width: min(45vw, 620px);
      flex: none;
      display: flex;
      flex-direction: column;
      background: var(--color-background-muted);
      min-height: 0;
    }

    .brief-head {
      height: 48px;
      flex: none;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 18px;
      border-bottom: 1px solid var(--color-border);
      background: var(--color-background-surface);
    }

    .brief-scroll {
      flex: 1;
      overflow-y: auto;
      padding: 16px 20px 24px;
    }

    .paper-brief {
      background: var(--paper-bg);
      border: 1px solid #e7e0d3;
      border-top: 3px solid var(--brand);
      border-radius: 8px;
      padding: 24px 28px;
      font-family: var(--serif);
      font-size: 14px;
      line-height: 1.6;
      color: #1e1e1e;
      box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    }

    .court-caption {
      text-align: center;
      font-family: var(--sans);
      font-weight: 700;
      font-size: 12px;
      letter-spacing: 0.05em;
      color: #334155;
      padding-bottom: 12px;
      border-bottom: 2px solid #334155;
      margin-bottom: 16px;
    }

    /* EDITABLE WORKSHEET MODE */
    .editor-container {
      display: none;
      flex-direction: column;
      gap: 10px;
    }

    .editor-container.show {
      display: flex;
    }

    .brief-textarea {
      width: 100%;
      height: 480px;
      font-family: var(--mono);
      font-size: 13px;
      line-height: 1.5;
      padding: 14px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      background: #ffffff;
      outline: none;
      resize: vertical;
    }

    .editor-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #ffffff;
      border: 1px solid var(--color-border);
      border-radius: 6px;
      padding: 8px 12px;
    }

    #briefMiniMap {
      height: 170px;
      width: 100%;
      border-radius: 6px;
      border: 1px solid #cbd5e1;
      margin-top: 8px;
    }

    @media print {
      .topbar, .chat-pane, .brief-head, .suggest-row, .composer-wrap, .editor-toolbar, .nav-switcher { display: none !important; }
      .app-body, .workspace-view { overflow: visible !important; }
      .brief-pane { width: 100% !important; border: none !important; background: transparent !important; }
      .paper-brief { border: none !important; box-shadow: none !important; padding: 0 !important; }
    }
  </style>
</head>
<body>

<!-- TOPBAR WITH MODE SWITCHER -->
<header class="topbar">
  <div class="brand">
    <span class="hearth-mark" aria-hidden="true">
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.2">
        <path d="M3.5 10.5 12 4l8.5 6.5M5.5 9v10.5h13V9M10 19.5v-5h4v5"/>
      </svg>
    </span>
    <div>
      <span class="brand-name">Hearth</span>
      <span class="brand-sub d-none d-md-inline ms-1 text-muted">Housing-Court Intake Partner</span>
    </div>
  </div>

  <!-- NAVIGATION TABS: DASHBOARD VS WORKSPACE -->
  <div class="nav-switcher">
    <button class="nav-btn" id="btnNavDash" onclick="switchView('dashboard')">
      <i class="bi bi-grid-fill"></i> Cases Dashboard
    </button>
    <button class="nav-btn active" id="btnNavWork" onclick="switchView('workspace')">
      <i class="bi bi-chat-square-text-fill"></i> Living Brief & Intake
    </button>
  </div>

  <div class="d-flex align-items-center gap-2">
    <div id="topCaseLine" class="case-line is-urgent d-none d-lg-block">
      1000 Block St. Nicholas Ave · Mon 9:30 AM · $3,350 · 5d 11h left
    </div>
    <button class="btn btn-sm btn-outline-primary" onclick="openNewCaseModal()"><i class="bi bi-plus-lg me-1"></i>New Case</button>
    <button class="btn btn-sm btn-primary" onclick="window.print()"><i class="bi bi-printer me-1"></i>Print</button>
  </div>
</header>

<!-- =======================================================================
     APP BODY WITH TWO VIEWS
     ======================================================================= -->
<div class="app-body" style="flex:1; min-height:0; display:flex;">

  <!-- VIEW 1: CASEWORKER CASE MANAGEMENT DASHBOARD ("THE NEXT APP") -->
  <section class="view-pane dashboard-view" id="dashboardView">
    <div class="dash-header">
      <div>
        <h4 class="fw-bold mb-1" style="color:var(--brand-ink);">Caseworker Case Management Dashboard</h4>
        <div class="text-muted small">Monitor active calendar calls, edit living defense briefs, and track arrears relief matches.</div>
      </div>
      <div>
        <button class="btn btn-primary btn-sm" onclick="openNewCaseModal()"><i class="bi bi-plus-circle me-1"></i>Create New Intake</button>
      </div>
    </div>

    <!-- KPI Metric Cards -->
    <div class="kpi-row">
      <div class="kpi-card">
        <div class="kpi-title">Active Tenant Cases</div>
        <div class="kpi-val" id="kpiTotalCases">4</div>
        <div class="kpi-sub">Stored in Firebase/SQLite DB</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Hearings This Week</div>
        <div class="kpi-val text-danger" id="kpiCriticalHearings">2</div>
        <div class="kpi-sub text-danger fw-bold">Critical Calendar Calls</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Total Arrears Managed</div>
        <div class="kpi-val" id="kpiTotalArrears">$15,450</div>
        <div class="kpi-sub">Subject to habitability disputes</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Relief Funds Matched</div>
        <div class="kpi-val text-success" id="kpiTotalRelief">$60,000</div>
        <div class="kpi-sub">HRA One Shot Deal & ERP</div>
      </div>
    </div>

    <!-- Filters & Search -->
    <div class="filter-card">
      <div class="input-group" style="max-width: 320px;">
        <span class="input-group-text bg-light"><i class="bi bi-search"></i></span>
        <input type="text" id="dashSearchInput" class="form-control" placeholder="Search tenant, address, index #..." oninput="filterCasesTable()">
      </div>
      <div class="btn-group btn-group-sm">
        <button class="btn btn-outline-secondary active" onclick="setStatusFilter('All', this)">All Cases</button>
        <button class="btn btn-outline-secondary" onclick="setStatusFilter('Hearing Ready', this)">Hearing Ready</button>
        <button class="btn btn-outline-secondary" onclick="setStatusFilter('Active Intake', this)">Active Intake</button>
        <button class="btn btn-outline-secondary" onclick="setStatusFilter('Brief Finalized', this)">Finalized</button>
      </div>
      <div class="ms-auto small text-muted" id="casesCountLabel">Showing 4 cases</div>
    </div>

    <!-- Cases Table -->
    <div class="cases-table-wrap">
      <table class="table-cases">
        <thead>
          <tr>
            <th>Court Index & ID</th>
            <th>Tenant & Building (100-Block)</th>
            <th>Hearing Schedule</th>
            <th>Claimed Arrears</th>
            <th>Status</th>
            <th>Brief Version</th>
            <th class="text-end">Actions</th>
          </tr>
        </thead>
        <tbody id="casesTableBody">
          <!-- Dynamically populated -->
        </tbody>
      </table>
    </div>
  </section>

  <!-- VIEW 2: HEARTH INTAKE & LIVING BRIEF WORKSPACE -->
  <section class="view-pane workspace-view active" id="workspaceView">
    <!-- LEFT: Conversation with Hearth (58%) -->
    <main class="chat-pane">
      <div class="chat-scroll" id="chatScroll">
        <div class="msg-wrap">
          <div class="msg-bubble msg-hearth">
            <div class="msg-hearth-header">
              <span class="hearth-mark" style="width:20px; height:20px; border-radius:5px;">
                <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <path d="M3.5 10.5 12 4l8.5 6.5M5.5 9v10.5h13V9M10 19.5v-5h4v5"/>
                </svg>
              </span>
              <span>Hearth</span>
            </div>
            <div>
              Hearth active. Ready for Housing Court intake.<br><br>
              I partner with legal-aid intake caseworkers for Housing Part proceedings. 
              Review the living brief on the right, make direct edits to the court brief worksheet, 
              or speak with me to evaluate statutory defenses and relief funds.
            </div>
          </div>
        </div>
      </div>

      <!-- Suggested Next Question Chips -->
      <div class="suggest-row" id="suggestRow">
        <button class="suggest-chip" onclick="sendPrompt('New intake. Tenant on the 1000 block of St. Nicholas Ave, Manhattan. Nonpayment hearing Monday 9:30. Radiators cold since early Nov, black mold around the tub, water coming through the bathroom wall. Anything open on her block?')">⚡ Marisol Intake (Golden Turn 1)</button>
        <button class="suggest-chip" onclick="sendPrompt('Why did you set aside the top look-alike? It looked like a strong match.')">🔍 Why set aside look-alike?</button>
        <button class="suggest-chip" onclick="sendPrompt('What law covers this?')">⚖️ What law covers this?</button>
        <button class="suggest-chip" onclick="sendPrompt('Household of 3, about $31k a year, owes $3,350, has the court index number. Her daughter\'s asthma is worse.')">💰 Relief funds ($31k, 3 people)</button>
        <button class="suggest-chip" onclick="sendPrompt('How bad is this neighborhood compared to the city?')">📊 Neighborhood context</button>
      </div>

      <!-- Composer -->
      <div class="composer-wrap">
        <div class="composer-inner">
          <div class="multimodal-popup" id="multimodalPopup">
            <div class="popup-item" onclick="openVisionInspectModal()">
              <i class="bi bi-camera text-primary fs-5"></i>
              <div>
                <div class="fw-semibold">Inspect Hazard Photo</div>
                <div class="text-muted" style="font-size: 11px;">Class A/B/C violation & evidentiary boundary</div>
              </div>
            </div>
            <div class="popup-item" onclick="openNoticeOCRModal()">
              <i class="bi bi-file-earmark-text text-success fs-5"></i>
              <div>
                <div class="fw-semibold">Extract Notice of Petition (OCR)</div>
                <div class="text-muted" style="font-size: 11px;">Index number, claimed arrears & hearing date</div>
              </div>
            </div>
            <div class="popup-item" onclick="openAudioIntakeModal()">
              <i class="bi bi-mic text-danger fs-5"></i>
              <div>
                <div class="fw-semibold">Voice Audio Intake</div>
                <div class="text-muted" style="font-size: 11px;">Transcribe tenant statement into facts</div>
              </div>
            </div>
          </div>

          <button class="btn-plus" type="button" onclick="togglePlusMenu()" title="Attach photo or document">+</button>
          <input type="text" id="composerInput" class="composer-input" placeholder="Talk with Hearth about case facts, law, or relief..." onkeydown="if(event.key==='Enter') submitMessage()">
          <button class="btn-send" onclick="submitMessage()"><i class="bi bi-arrow-up"></i></button>
        </div>
      </div>
    </main>

    <!-- RIGHT: LIVING BRIEF & IN-PLACE EDITING WORKSHEET (42%) -->
    <aside class="brief-pane">
      <div class="brief-head">
        <div class="d-flex align-items-center gap-2">
          <span class="fw-bold" style="font-size:13.5px;"><i class="bi bi-file-earmark-text me-1 text-primary"></i>Living Brief</span>
          <span class="badge bg-light text-primary border" id="briefStatusBadge">v1 · Saved to DB</span>
        </div>
        <div class="d-flex align-items-center gap-2">
          <button class="btn btn-sm btn-outline-secondary" id="btnToggleEdit" onclick="toggleEditMode()">
            <i class="bi bi-pencil-square me-1"></i><span id="btnToggleEditText">Edit Brief</span>
          </button>
          <button class="btn btn-sm btn-outline-secondary" onclick="copyBrief()"><i class="bi bi-clipboard"></i></button>
        </div>
      </div>

      <div class="brief-scroll">
        <!-- MODE A: Clean Court Document View -->
        <article class="paper-brief" id="paperBrief">
          <div class="court-caption">
            CIVIL COURT OF THE CITY OF NEW YORK · COUNTY OF NEW YORK · HOUSING PART<br>
            NONPAYMENT PROCEEDING · INDEX NO. <span id="captionIndexNumber">LT-029481/26/NY</span>
          </div>

          <div id="briefContent">
            <!-- Living brief markdown renders here -->
          </div>

          <div id="briefMapContainer" style="display:none; margin-top:14px;">
            <div class="small fw-bold text-muted mb-1"><i class="bi bi-geo-alt me-1 text-danger"></i>Building & 800m Habitability Buffer Map</div>
            <div id="briefMiniMap"></div>
            <div class="d-flex justify-content-between align-items-center mt-1 small text-muted" style="font-size: 11.5px;">
              <span id="mapCentroidLabel">Lat 40.8366, Lon -73.9421 (No Unit #)</span>
              <div>
                <a id="btnMapsLink" href="#" target="_blank" class="text-decoration-none me-2">Google Maps</a>
                <a id="btnStreetLink" href="#" target="_blank" class="text-decoration-none">Street View</a>
              </div>
            </div>
          </div>

          <div class="mt-3 pt-2 border-top small text-muted font-monospace" style="font-size:11px;">
            Stored in DB: <span id="briefCaseIdTag">case-lt-029481-26</span> · Rule 7 100-Block Privacy
          </div>
        </article>

        <!-- MODE B: In-Place Editing Worksheet -->
        <div class="editor-container" id="editorContainer">
          <div class="editor-toolbar">
            <span class="small fw-bold text-primary"><i class="bi bi-pencil-fill me-1"></i>Caseworker Document Editor</span>
            <div class="d-flex gap-2">
              <button class="btn btn-sm btn-outline-secondary" onclick="cancelEditMode()">Cancel</button>
              <button class="btn btn-sm btn-success" onclick="saveBriefEdits()"><i class="bi bi-cloud-arrow-up-fill me-1"></i>Save Changes to DB</button>
            </div>
          </div>

          <textarea id="briefTextarea" class="brief-textarea" placeholder="Edit legal brief content here..."></textarea>

          <div class="bg-white p-3 rounded border">
            <label class="form-label small fw-bold text-muted">Caseworker / Supervising Attorney Notes:</label>
            <input type="text" id="caseworkerNotesInput" class="form-control form-control-sm" placeholder="e.g. Verified tenant witness testimony for Monday hearing.">
          </div>
        </div>
      </div>
    </aside>
  </section>

</div>

<!-- NEW CASE MODAL -->
<div class="modal fade" id="newCaseModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h6 class="modal-title fw-bold"><i class="bi bi-folder-plus me-2 text-primary"></i>Create New Tenant Intake Case</h6>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <div class="mb-2">
          <label class="form-label small fw-bold">Tenant Name</label>
          <input type="text" id="modalTenantName" class="form-control form-control-sm" placeholder="e.g. Marisol V.">
        </div>
        <div class="mb-2">
          <label class="form-label small fw-bold">100-Block Building Address (Rule 7: No Unit #)</label>
          <input type="text" id="modalAddress" class="form-control form-control-sm" placeholder="e.g. 1000 Block of St. Nicholas Ave">
        </div>
        <div class="row g-2 mb-2">
          <div class="col">
            <label class="form-label small fw-bold">Court Index #</label>
            <input type="text" id="modalIndex" class="form-control form-control-sm" placeholder="LT-029481/26/NY">
          </div>
          <div class="col">
            <label class="form-label small fw-bold">Claimed Arrears ($)</label>
            <input type="number" id="modalArrears" class="form-control form-control-sm" placeholder="3350">
          </div>
        </div>
        <div class="row g-2 mb-2">
          <div class="col">
            <label class="form-label small fw-bold">Hearing Date</label>
            <input type="date" id="modalHearingDate" class="form-control form-control-sm" value="2026-11-23">
          </div>
          <div class="col">
            <label class="form-label small fw-bold">Hearing Time</label>
            <input type="text" id="modalHearingTime" class="form-control form-control-sm" value="09:30 AM">
          </div>
        </div>
        <div class="mb-2">
          <label class="form-label small fw-bold">Habitability Narrative & Hazards</label>
          <textarea id="modalNarrative" class="form-control form-control-sm" rows="3" placeholder="Describe cold radiators, mold, leaks..."></textarea>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modal">Cancel</button>
        <button type="button" class="btn btn-sm btn-primary" onclick="submitNewCaseModal()">Save & Launch Intake</button>
      </div>
    </div>
  </div>
</div>

<!-- MULTIMODAL PHOTO MODAL -->
<div class="modal fade" id="visionModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h6 class="modal-title fw-bold"><i class="bi bi-camera me-2 text-primary"></i>Inspect Tenant Hazard Photo</h6>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <p class="small text-muted">Forensic inspection for cold radiators, black mold, and water leaks.</p>
        <div class="p-3 text-center border rounded mb-3 bg-light">
          <i class="bi bi-image text-muted" style="font-size: 2.5rem;"></i>
          <div class="small fw-semibold mt-1">Sample Photo: Marisol's Bathroom Tile Mold & Active Leak</div>
        </div>
        <div id="visionResultBox" style="display:none;" class="p-3 rounded border bg-light small"></div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modal">Close</button>
        <button type="button" class="btn btn-sm btn-primary" onclick="runVisionInspection()">Run Forensic Inspection</button>
      </div>
    </div>
  </div>
</div>

<!-- MULTIMODAL NOTICE OCR MODAL -->
<div class="modal fade" id="noticeModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h6 class="modal-title fw-bold"><i class="bi bi-file-earmark-text me-2 text-success"></i>Extract Notice of Petition (OCR)</h6>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <p class="small text-muted">OCR Housing Court Notice of Petition / 14-day Rent Demand.</p>
        <div class="p-3 text-center border rounded mb-3 bg-light">
          <i class="bi bi-file-earmark-pdf text-muted" style="font-size: 2.5rem;"></i>
          <div class="small fw-semibold mt-1">Sample Notice: LT-029481/26/NY (Nonpayment Petition)</div>
        </div>
        <div id="noticeResultBox" style="display:none;" class="p-3 rounded border bg-light small"></div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modal">Close</button>
        <button type="button" class="btn btn-sm btn-primary" onclick="runNoticeOCR()">Extract Court Details</button>
      </div>
    </div>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
<script>
let currentCaseId = "case-lt-029481-26";
let currentBriefMarkdown = "";
let currentCaseState = null;
let isEditMode = false;
let miniMapInstance = null;
let allCasesCache = [];
let currentFilterStatus = "All";

// --- VIEW SWITCHER ---
function switchView(viewName) {
  document.getElementById("btnNavDash").classList.toggle("active", viewName === "dashboard");
  document.getElementById("btnNavWork").classList.toggle("active", viewName === "workspace");
  document.getElementById("dashboardView").classList.toggle("active", viewName === "dashboard");
  document.getElementById("workspaceView").classList.toggle("active", viewName === "workspace");

  if (viewName === "dashboard") {
    loadDashboard();
  }
}

// --- DASHBOARD DATA & TABLE ---
async function loadDashboard() {
  try {
    const [casesRes, statsRes] = await Promise.all([
      fetch("/api/cases"),
      fetch("/api/dashboard/stats")
    ]);
    allCasesCache = await casesRes.json();
    const stats = await statsRes.json();

    document.getElementById("kpiTotalCases").innerText = stats.total_cases;
    document.getElementById("kpiCriticalHearings").innerText = stats.hearings_this_week;
    document.getElementById("kpiTotalArrears").innerText = "$" + stats.total_arrears.toLocaleString();
    document.getElementById("kpiTotalRelief").innerText = "$" + stats.total_relief_matched.toLocaleString();

    renderCasesTable(allCasesCache);
  } catch (err) {
    console.error("Dashboard error:", err);
  }
}

function setStatusFilter(status, btn) {
  currentFilterStatus = status;
  document.querySelectorAll(".filter-card .btn-group .btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  filterCasesTable();
}

function filterCasesTable() {
  const query = document.getElementById("dashSearchInput").value.toLowerCase().trim();
  const filtered = allCasesCache.filter(c => {
    const matchesStatus = (currentFilterStatus === "All") || (c.status === currentFilterStatus);
    const matchesQuery = !query || (
      (c.tenant_name && c.tenant_name.toLowerCase().includes(query)) ||
      (c.court_index_number && c.court_index_number.toLowerCase().includes(query)) ||
      (c.block_address && c.block_address.toLowerCase().includes(query))
    );
    return matchesStatus && matchesQuery;
  });
  renderCasesTable(filtered);
}

function renderCasesTable(cases) {
  const tbody = document.getElementById("casesTableBody");
  tbody.innerHTML = "";
  document.getElementById("casesCountLabel").innerText = `Showing ${cases.length} case${cases.length === 1 ? '' : 's'}`;

  if (cases.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No cases found matching filter criteria.</td></tr>`;
    return;
  }

  cases.forEach(c => {
    const tr = document.createElement("tr");

    let badgeClass = "badge-draft";
    if (c.urgency_level === "Critical" || c.status === "Hearing Ready") badgeClass = "badge-critical";
    else if (c.urgency_level === "High") badgeClass = "badge-high";
    else if (c.status === "Brief Finalized") badgeClass = "badge-ready";

    tr.innerHTML = `
      <td>
        <div class="fw-bold text-primary">${c.court_index_number || 'Pending'}</div>
        <div class="font-monospace text-muted" style="font-size:11px;">${c.case_id}</div>
      </td>
      <td>
        <div class="fw-semibold">${c.tenant_name || 'Anonymous Tenant'}</div>
        <div class="text-muted small">${c.block_address || 'New York, NY'}</div>
      </td>
      <td>
        <div><i class="bi bi-calendar-event me-1 text-muted"></i>${c.hearing_date || 'TBD'} · ${c.hearing_time || '09:30 AM'}</div>
        ${c.urgency_level === 'Critical' ? '<span class="badge bg-danger mt-1">Calendar Call Imminent</span>' : ''}
      </td>
      <td>
        <div class="fw-bold">$${(c.claimed_arrears || 0).toLocaleString()}</div>
        <div class="text-success small" style="font-size:11.5px;"><i class="bi bi-check-circle me-1"></i>Relief Qualified</div>
      </td>
      <td>
        <span class="badge ${badgeClass}">${c.status || 'Active Intake'}</span>
      </td>
      <td>
        <span class="badge bg-light text-dark border">v${c.brief_edits_count || 1}</span>
      </td>
      <td class="text-end">
        <button class="btn btn-sm btn-primary me-1" onclick="openCaseInWorkspace('${c.case_id}')">
          <i class="bi bi-box-arrow-in-right me-1"></i>Open Brief
        </button>
        <button class="btn btn-sm btn-outline-danger" onclick="deleteCase('${c.case_id}')">
          <i class="bi bi-trash"></i>
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function openCaseInWorkspace(caseId) {
  try {
    const res = await fetch(`/api/cases/${caseId}`);
    if (!res.ok) throw new Error("Could not retrieve case");
    const data = await res.json();
    currentCaseId = data.case_id;
    currentCaseState = data;
    currentBriefMarkdown = data.brief_markdown || "";

    // Switch to workspace view
    switchView("workspace");

    // Populate brief
    renderBriefMarkdown(currentBriefMarkdown);
    document.getElementById("captionIndexNumber").innerText = data.court_index_number || "LT-029481/26/NY";
    document.getElementById("briefCaseIdTag").innerText = data.case_id;
    document.getElementById("briefStatusBadge").innerText = `v${data.brief_edits_count || 1} · Saved in DB`;
    document.getElementById("topCaseLine").innerText = `${data.block_address} · ${data.hearing_date} · $${data.claimed_arrears.toLocaleString()}`;

    // If map data present
    if (data.building_location) {
      document.getElementById("briefMapContainer").style.display = "block";
      renderMiniMap(data.building_location, data.corroborated_evidence || []);
    }

    // Add notice in chat
    appendHearthBubble(`Retrieved case **${data.court_index_number}** for **${data.tenant_name}** from the database. The Living Brief on the right is populated and ready for editing.`);
  } catch (err) {
    alert("Error loading case: " + err);
  }
}

async function deleteCase(caseId) {
  if (!confirm(`Are you sure you want to delete case ${caseId}?`)) return;
  try {
    const res = await fetch(`/api/cases/${caseId}`, {method: "DELETE"});
    if (res.ok) {
      loadDashboard();
    }
  } catch (err) {
    alert("Delete failed: " + err);
  }
}

// --- LIVING BRIEF IN-PLACE EDITING ---
function toggleEditMode() {
  isEditMode = !isEditMode;
  const paper = document.getElementById("paperBrief");
  const editor = document.getElementById("editorContainer");
  const btn = document.getElementById("btnToggleEditText");

  if (isEditMode) {
    paper.style.display = "none";
    editor.classList.add("show");
    document.getElementById("briefTextarea").value = currentBriefMarkdown;
    document.getElementById("caseworkerNotesInput").value = (currentCaseState && currentCaseState.caseworker_notes) || "";
    btn.innerText = "View Clean Brief";
  } else {
    paper.style.display = "block";
    editor.classList.remove("show");
    btn.innerText = "Edit Brief";
  }
}

function cancelEditMode() {
  isEditMode = false;
  document.getElementById("paperBrief").style.display = "block";
  document.getElementById("editorContainer").classList.remove("show");
  document.getElementById("btnToggleEditText").innerText = "Edit Brief";
}

async function saveBriefEdits() {
  const newMarkdown = document.getElementById("briefTextarea").value;
  const notes = document.getElementById("caseworkerNotesInput").value;

  try {
    const res = await fetch(`/api/cases/${currentCaseId}/brief`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        brief_markdown: newMarkdown,
        caseworker_notes: notes
      })
    });
    const updated = await res.json();
    currentBriefMarkdown = updated.brief_markdown;
    if (currentCaseState) {
      currentCaseState.brief_markdown = updated.brief_markdown;
      currentCaseState.caseworker_notes = updated.caseworker_notes;
      currentCaseState.brief_edits_count = updated.brief_edits_count;
    }

    renderBriefMarkdown(currentBriefMarkdown);
    document.getElementById("briefStatusBadge").innerText = `v${updated.brief_edits_count} · Saved in DB`;

    cancelEditMode();
    alert("Tenant Stabilization Brief saved successfully to the database!");
  } catch (err) {
    alert("Failed to save brief: " + err);
  }
}

function renderBriefMarkdown(md) {
  document.getElementById("briefContent").innerHTML = marked.parse(md || "*No brief drafted yet.*");
}

function copyBrief() {
  if (!currentBriefMarkdown) {
    alert("Please initiate an intake with Hearth first.");
    return;
  }
  navigator.clipboard.writeText(currentBriefMarkdown).then(() => {
    alert("Tenant Stabilization Brief copied to clipboard!");
  });
}

// --- CONVERSATION WITH HEARTH ---
function togglePlusMenu() {
  document.getElementById("multimodalPopup").classList.toggle("show");
}

document.addEventListener("click", function(e) {
  const plusBtn = document.querySelector(".btn-plus");
  const popup = document.getElementById("multimodalPopup");
  if (plusBtn && popup && !plusBtn.contains(e.target) && !popup.contains(e.target)) {
    popup.classList.remove("show");
  }
});

function sendPrompt(text) {
  document.getElementById("composerInput").value = text;
  submitMessage();
}

async function submitMessage() {
  const input = document.getElementById("composerInput");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";

  appendUserBubble(text);

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        message: text,
        current_case: currentCaseState,
        session_id: currentCaseId
      })
    });
    const data = await res.json();
    appendHearthBubble(data.reply);
    updateSuggestions(data.suggestions);
    currentCaseState = data.case_state;
    if (data.case_state && data.case_state.case_id) {
      currentCaseId = data.case_state.case_id;
    }

    if (data.ui_data && data.ui_data.brief_markdown) {
      currentBriefMarkdown = data.ui_data.brief_markdown;
      renderBriefMarkdown(currentBriefMarkdown);
      document.getElementById("briefStatusBadge").innerText = "Updated & Saved";
      if (data.ui_data.building_location) {
        document.getElementById("briefMapContainer").style.display = "block";
        renderMiniMap(data.ui_data.building_location, data.ui_data.corroborated_evidence || []);
      }
    }
  } catch (err) {
    appendHearthBubble("Connection error: " + err);
  }
}

function appendUserBubble(text) {
  const scroll = document.getElementById("chatScroll");
  const wrap = document.createElement("div");
  wrap.className = "msg-wrap";
  const div = document.createElement("div");
  div.className = "msg-bubble msg-user";
  div.innerText = text;
  wrap.appendChild(div);
  scroll.appendChild(wrap);
  scroll.scrollTop = scroll.scrollHeight;
}

function appendHearthBubble(markdownText) {
  const scroll = document.getElementById("chatScroll");
  const wrap = document.createElement("div");
  wrap.className = "msg-wrap";
  const div = document.createElement("div");
  div.className = "msg-bubble msg-hearth";
  div.innerHTML = `
    <div class="msg-hearth-header">
      <span class="hearth-mark" style="width:20px; height:20px; border-radius:5px;">
        <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2.2">
          <path d="M3.5 10.5 12 4l8.5 6.5M5.5 9v10.5h13V9M10 19.5v-5h4v5"/>
        </svg>
      </span>
      <span>Hearth</span>
    </div>
    <div>${marked.parse(markdownText)}</div>
  `;
  wrap.appendChild(div);
  scroll.appendChild(wrap);
  scroll.scrollTop = scroll.scrollHeight;
}

function updateSuggestions(suggestions) {
  if (!suggestions || suggestions.length === 0) return;
  const row = document.getElementById("suggestRow");
  row.innerHTML = "";
  suggestions.forEach(s => {
    const btn = document.createElement("button");
    btn.className = "suggest-chip";
    btn.innerText = s;
    btn.onclick = () => sendPrompt(s);
    row.appendChild(btn);
  });
}

function renderMiniMap(bld, evidence) {
  const lat = bld.latitude || 40.836626;
  const lon = bld.longitude || -73.942098;

  document.getElementById("mapCentroidLabel").innerText = `Lat ${lat}, Lon ${lon} · Tract ${bld.census_tract_geoid || ''} (No Unit #)`;
  document.getElementById("btnMapsLink").href = bld.google_maps_url;
  document.getElementById("btnStreetLink").href = bld.google_street_view_url;

  setTimeout(() => {
    if (!miniMapInstance) {
      miniMapInstance = L.map('briefMiniMap').setView([lat, lon], 15);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
      }).addTo(miniMapInstance);
    } else {
      miniMapInstance.setView([lat, lon], 15);
      miniMapInstance.eachLayer(l => {
        if (l instanceof L.Marker || l instanceof L.Circle) miniMapInstance.removeLayer(l);
      });
    }

    L.circle([lat, lon], {
      radius: 800,
      color: '#1d4ed8',
      fillColor: '#eef3ff',
      fillOpacity: 0.25,
      weight: 1.5,
      dashArray: '4, 4'
    }).addTo(miniMapInstance).bindPopup("800m Statutory Habitability Buffer");

    L.marker([lat, lon]).addTo(miniMapInstance).bindPopup(`<b>${bld.building_address}</b>`);

    (evidence || []).forEach((ev, i) => {
      const kLat = lat + (0.0008 * (i + 1) * 0.5);
      const kLon = lon + (0.0006 * (i + 1) * (i % 2 === 0 ? 1 : -1));
      L.circleMarker([kLat, kLon], {radius: 6, color: '#16a34a', fillColor: '#22c55e', fillOpacity: 0.9}).addTo(miniMapInstance);
    });

    miniMapInstance.invalidateSize();
  }, 100);
}

// --- NEW CASE MODAL ACTIONS ---
function openNewCaseModal() {
  new bootstrap.Modal(document.getElementById("newCaseModal")).show();
}

async function submitNewCaseModal() {
  const tenantName = document.getElementById("modalTenantName").value.trim() || "New Tenant";
  const address = document.getElementById("modalAddress").value.trim() || "1000 Block of St. Nicholas Ave";
  const indexNum = document.getElementById("modalIndex").value.trim() || "LT-000000/26/NY";
  const arrears = parseFloat(document.getElementById("modalArrears").value) || 2500.0;
  const hearingDate = document.getElementById("modalHearingDate").value || "2026-11-30";
  const hearingTime = document.getElementById("modalHearingTime").value || "09:30 AM";
  const narrative = document.getElementById("modalNarrative").value.trim() || "No heat reported.";

  const newCaseId = "case-lt-" + Math.floor(100000 + Math.random() * 900000) + "-26";

  const casePayload = {
    case_id: newCaseId,
    court_index_number: indexNum,
    tenant_name: tenantName,
    block_address: address,
    metro_area: "New York",
    census_tract_geoid: "36061024500",
    hearing_date: hearingDate,
    hearing_time: hearingTime,
    claimed_arrears: arrears,
    notice_type: "Nonpayment Petition",
    household_size: 2,
    annual_income: 30000.0,
    hazard_narrative: narrative,
    status: "Active Intake",
    urgency_level: "High",
    brief_markdown: `# Case Brief: ${tenantName}\n\n**Court Index:** ${indexNum}\n**Building:** ${address}\n**Arrears:** $${arrears.toLocaleString()}\n\n*Intake launched via Hearth.*`
  };

  try {
    const res = await fetch("/api/cases", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(casePayload)
    });
    const created = await res.json();
    bootstrap.Modal.getInstance(document.getElementById("newCaseModal")).hide();
    
    // Open in workspace immediately
    openCaseInWorkspace(created.case_id);
  } catch (err) {
    alert("Error creating case: " + err);
  }
}

// --- MODAL UTILITIES ---
function openVisionInspectModal() {
  document.getElementById("multimodalPopup").classList.remove("show");
  new bootstrap.Modal(document.getElementById("visionModal")).show();
}

async function runVisionInspection() {
  const box = document.getElementById("visionResultBox");
  box.style.display = "block";
  box.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Inspecting...`;
  const res = await fetch("/api/vision/inspect", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({image_base64: "dummy", mime_type: "image/jpeg"})
  });
  const data = await res.json();
  box.innerHTML = `
    <div class="fw-bold text-success mb-1"><i class="bi bi-check-circle-fill me-1"></i>Analysis Complete</div>
    <div>${data.condition_observed}</div>
    <div class="mt-1"><span class="badge bg-danger">${data.severity_class}</span></div>
  `;
}

function openNoticeOCRModal() {
  document.getElementById("multimodalPopup").classList.remove("show");
  new bootstrap.Modal(document.getElementById("noticeModal")).show();
}

async function runNoticeOCR() {
  const box = document.getElementById("noticeResultBox");
  box.style.display = "block";
  box.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Running OCR...`;
  const res = await fetch("/api/vision/notice", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({image_base64: "dummy", mime_type: "image/jpeg"})
  });
  const data = await res.json();
  box.innerHTML = `
    <div class="fw-bold text-success mb-1">Notice Extracted</div>
    <div>Index: <code>${data.court_index_number}</code></div>
    <div>Arrears: $${data.claimed_arrears.toLocaleString()}</div>
  `;
}

function openAudioIntakeModal() {
  document.getElementById("multimodalPopup").classList.remove("show");
  sendPrompt("I have a voice statement from the tenant. The radiators have been cold since early November, there is black mold around the tub, and hearing is Monday morning.");
}

// Auto-load Marisol case into workspace on first load
window.addEventListener("DOMContentLoaded", () => {
  openCaseInWorkspace("case-lt-029481-26");
});
</script>

</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST if hasattr(config, "HOST") else "127.0.0.1", port=8000)
