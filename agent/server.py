import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from agent.navigator.agent import root_agent
from agent.navigator.tools.case_file import open_case, update_case
from agent.navigator.tools.evidence import search_habitability_evidence
from agent.navigator.tools.statutes import match_statutes
from agent.navigator.tools.funds import match_relief_funds
from agent.navigator.tools.tract import get_tract_context, find_tract_for_block
from agent.navigator.tools.brief import render_brief_markdown
from agent.navigator.equity import tract_equity_note
from unittest.mock import MagicMock

# Enable Vertex AI for ADK
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
os.environ["GOOGLE_CLOUD_LOCATION"] = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

app = FastAPI(title="Stabilization Navigator API & Rich Chat", description="AI Intake Co-pilot with Rich UI & Live BigQuery Tool State")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name="navigator", session_service=session_service)

# In-memory mapping from web session_id -> ADK session object
adk_sessions = {}

async def get_or_create_adk_session(session_id: str):
    if session_id not in adk_sessions:
        s = await session_service.create_session(app_name="navigator", user_id="web_user")
        adk_sessions[session_id] = s
    return adk_sessions[session_id]

class ChatMessageRequest(BaseModel):
    session_id: str = "default"
    message: str

class OpenCaseRequest(BaseModel):
    session_id: str = "default"
    block_address: str
    hearing_datetime: str
    hazards: list[str]
    tenant_narrative: str
    census_tract_geoid: str = ""

class UpdateCaseRequest(BaseModel):
    session_id: str = "default"
    household_size: int | None = None
    annual_income_usd: float | None = None
    arrears_usd: float | None = None
    has_court_index_number: bool | None = None
    received_written_rent_demand: bool | None = None
    notes: str = ""

class FinalizeBriefRequest(BaseModel):
    session_id: str = "default"
    memo_markdown: str

@app.get("/", response_class=HTMLResponse)
def index_page():
    html_file = os.path.join(os.path.dirname(__file__), "static_index.html")
    if os.path.exists(html_file):
        with open(html_file) as f:
            return f.read()
    return "<h1>Stabilization Navigator Online</h1>"

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Stabilization Navigator",
        "metro": "New York",
        "dataset": "a4i_housing",
        "model": "gemini-2.5-flash via Vertex AI"
    }

@app.get("/case/state")
async def get_case_state(session_id: str = "default"):
    """Fetch structured state of the case for this session."""
    adk_sess = await get_or_create_adk_session(session_id)
    s = await session_service.get_session(app_name="navigator", user_id="web_user", session_id=adk_sess.id)
    case = s.state.get("case") if s else None
    return {"session_id": session_id, "case": case}

@app.post("/chat")
async def chat_turn(req: ChatMessageRequest):
    """Conversational turn returning assistant message, invoked tools, and updated case state snapshot."""
    adk_sess = await get_or_create_adk_session(req.session_id)
    msg = types.Content(parts=[types.Part.from_text(text=req.message)])
    
    text_responses = []
    tool_calls = []
    
    async for event in runner.run_async(user_id="web_user", session_id=adk_sess.id, new_message=msg):
        if event.content and event.content.parts:
            for p in event.content.parts:
                if p.text:
                    text_responses.append(p.text)
                if p.function_call:
                    tool_calls.append({
                        "tool": p.function_call.name,
                        "args": p.function_call.args
                    })

    # Retrieve current case state from ADK session
    s = await session_service.get_session(app_name="navigator", user_id="web_user", session_id=adk_sess.id)
    case_snapshot = s.state.get("case") if s else None

    # If the case has evidence and funds haven't been evaluated or need auto-refresh
    return {
        "session_id": req.session_id,
        "reply": "\n\n".join(text_responses) if text_responses else "Case information processed.",
        "tool_calls": tool_calls,
        "case_state": case_snapshot
    }

# Retain direct endpoints for testing / manual trigger
sessions = {}
def get_context(session_id: str):
    if session_id not in sessions:
        ctx = MagicMock()
        ctx.state = {}
        sessions[session_id] = ctx
    return sessions[session_id]

@app.post("/case/open")
def api_open_case(req: OpenCaseRequest):
    ctx = get_context(req.session_id)
    return open_case(
        block_address=req.block_address,
        hearing_datetime=req.hearing_datetime,
        hazards=req.hazards,
        tenant_narrative=req.tenant_narrative,
        tool_context=ctx,
        census_tract_geoid=req.census_tract_geoid,
    )

@app.post("/case/update")
def api_update_case(req: UpdateCaseRequest):
    ctx = get_context(req.session_id)
    return update_case(
        tool_context=ctx,
        household_size=req.household_size,
        annual_income_usd=req.annual_income_usd,
        arrears_usd=req.arrears_usd,
        has_court_index_number=req.has_court_index_number,
        received_written_rent_demand=req.received_written_rent_demand,
        notes=req.notes,
    )

@app.get("/evidence/search")
def api_search_evidence(session_id: str = "default"):
    ctx = get_context(session_id)
    return search_habitability_evidence(ctx)

@app.get("/statutes/match")
def api_match_statutes(session_id: str = "default"):
    ctx = get_context(session_id)
    return match_statutes(ctx)

@app.get("/funds/match")
def api_match_funds(session_id: str = "default"):
    ctx = get_context(session_id)
    return match_relief_funds(ctx)

@app.get("/tract/context/{geoid}")
def api_get_tract(geoid: str):
    return get_tract_context(geoid)

@app.post("/brief/generate")
def api_generate_brief(req: FinalizeBriefRequest):
    ctx = get_context(req.session_id)
    case = ctx.state.get("case")
    if not case:
        return {"error": "No open case found for session"}
    brief_md = render_brief_markdown(case, req.memo_markdown)
    equity_md = tract_equity_note(case)
    if equity_md:
        brief_md += "\n\n" + equity_md
    return {
        "status": "success",
        "brief_markdown": brief_md,
        "case_summary": {
            "block_address": case.get("block_address"),
            "census_tract_geoid": case.get("census_tract_geoid"),
            "evidence_count": len(case.get("evidence", [])),
            "excluded_count": len(case.get("exclusions", [])),
            "funds_count": len(case.get("funds", []))
        }
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
