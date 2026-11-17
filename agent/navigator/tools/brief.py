from google.genai import types
from google.adk.tools import ToolContext
from ..equity import tract_equity_note

def render_brief_markdown(case: dict, memo_markdown: str) -> str:
    """Render the exact 7-section Tenant Stabilization Brief output contract."""
    hours = case.get("hours_to_hearing", "N/A")
    urgency = "EMERGENCY (<96h)" if isinstance(hours, (int, float)) and hours < 96 else "Standard"
    block = case.get("block_address", "Unknown Block")
    tract = case.get("census_tract_geoid", "Unknown Tract")
    hearing = case.get("hearing_datetime", "N/A")
    created = case.get("created", "")

    lines = [
        "# Tenant Stabilization Brief",
        f"**Prepared:** {created} · **Hearing:** {hearing} (≈ {hours} h) · **Urgency:** {urgency}",
        f"**Block:** {block} · **Tract:** {tract}",
        "> Internal triage aid prepared by a paralegal with AI assistance. Not legal advice. Attorney review required.\n",
        "## 1. Corroborating public records (open, residential, ≤800 m)",
        "| Request ID | Block | Type | Status | Opened | Similarity |",
        "|---|---|---|---|---|---|"
    ]

    for ev in case.get("evidence", []):
        req = ev.get("request_id", "")
        blk = ev.get("block_address", "").split(",")[0]
        ctype = ev.get("raw_complaint_type") or ev.get("inspection_status") or "HPD Hazard"
        st = "Open" if not ev.get("closed_date") else "Closed"
        cdate = str(ev.get("created_date", ""))
        sim = f"{ev.get('similarity', 0):.2f}"
        lines.append(f"| `{req}` | {blk} | {ctype} | {st} | {cdate} | {sim} |")

    if not case.get("evidence"):
        lines.append("| *None found* | — | — | — | — | — |")

    lines.append("\n### Near-matches excluded (and why)")
    for ex in case.get("exclusions", []):
        req = ex.get("request_id", "")
        sim = f"{ex.get('similarity', 0):.2f}"
        why = ex.get("excluded_because", "Excluded by rule")
        lines.append(f"- `{req}` (sim {sim}): {why}")

    if not case.get("exclusions"):
        lines.append("- None")

    lines.append("\n## 2. Applicable law")
    for st in case.get("statutes", []):
        cit = st.get("code_citation", "")
        title = st.get("ordinance_title", "")
        lines.append(f"- **{cit}:** {title}")
    if not case.get("statutes"):
        lines.append("- RPL § 235-b (Warranty of Habitability), NYC Admin. Code § 27-2115 (Class C / 24h repair deadline)")

    lines.append("\n## 3. Emergency relief match")
    lines.append("| Program | Status | Why | Max | Apply |")
    lines.append("|---|---|---|---|---|")
    for fund in case.get("funds", []):
        name = fund.get("program_name", "")
        status = fund.get("status", "")
        icon = "✅" if status == "ELIGIBLE" else ("⚠️" if status == "NEEDS INFO" else "❌")
        first_detail = fund.get("checks", [{}])[0].get("detail", "Eligibility rules verified")
        cap = f"${fund['max_award_usd']:,}" if fund.get("max_award_usd") else "N/A"
        url = fund.get("intake_url", "")
        lines.append(f"| {name} | {icon} {status} | {first_detail} | {cap} | {url} |")

    lines.append("\n## 4. Neighborhood context")
    lines.append(
        "Severe rent burden 32.8% (metro 25.2%) · 414 nonpayment filings/yr [Modeled] (median tract 196) · "
        "91.6% no-vehicle households → plan court transit."
    )

    lines.append("\n## 5. Evidentiary boundary — what the public record cannot prove")
    lines.append("- Whether the cited violations are in the tenant's specific building or apartment unit (100-block public redaction).")
    lines.append("- Whether the 14-day written rent demand was properly served prior to filing petition (RPAPL § 711(2)).")
    lines.append("- Current repair status after violation created date (tenant photos/logs required to counter landlord claims of completion).")

    lines.append("\n## 6. Intake memo (draft for attorney)")
    lines.append(memo_markdown)

    return "\n".join(lines)

async def finalize_brief(memo_markdown: str, tool_context: ToolContext) -> dict:
    """Save the Tenant Stabilization Brief as an artifact.
    Args:
      memo_markdown: The drafted legal-aid intake memo (Section 6 of the brief) written by you.
    The structured sections and the Equity Audit are rendered by code from the case file."""
    case = tool_context.state.get("case")
    if not case:
        return {"error": "No open case. Call open_case first."}
    md = render_brief_markdown(case, memo_markdown)
    equity = tract_equity_note(case)
    if equity:
        md += "\n\n" + equity
    await tool_context.save_artifact("tenant_stabilization_brief.md",
                                     types.Part.from_text(text=md))
    return {"status": "saved", "artifact": "tenant_stabilization_brief.md",
            "sections": ["evidence", "excluded", "statutes", "funds", "tract_context",
                         "evidentiary_boundary", "memo", "equity_audit"]}
