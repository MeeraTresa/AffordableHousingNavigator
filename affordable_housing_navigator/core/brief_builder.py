"""Assembles the Tenant Stabilization Brief and Attorney Defense Packet."""

from datetime import datetime
from typing import List
from .case_intake import CaseIntakeSession, TenantCase, CorroboratedEvidence, ExcludedNearMatch, StatuteMatch, ReliefFundMatch, TractRiskProfile


def build_tenant_stabilization_brief(session: CaseIntakeSession) -> str:
    """Generate Markdown text for the Tenant Stabilization Brief."""
    tc = session.tenant_case
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Build markdown sections
    md = []
    md.append(f"# TENANT STABILIZATION BRIEF & LEGAL DEFENSE MEMO")
    md.append(f"**Intake Date/Time:** {now_str} | **Case ID:** `{session.session_id}` | **Metro:** {tc.metro_area}\n")
    md.append("---\n")

    # Section 1: Case Summary
    md.append("## 1. Case Intake & Urgency Profile")
    md.append(f"- **100-Block Address:** {tc.block_address} (Census Tract: `{tc.census_tract_geoid or 'N/A'}`)")
    if session.building_location:
        bld = session.building_location
        md.append(f"- **Building Spatial Identity:** Lat {bld.get('latitude')}, Lon {bld.get('longitude')} ([Google Maps Search]({bld.get('google_maps_url')}) | [Street View]({bld.get('google_street_view_url')})) *(Note: Apartment numbers omitted for privacy)*")
    md.append(f"- **Upcoming Court Hearing:** **{tc.hearing_date or 'To Be Scheduled'}** {tc.hearing_time or ''}")
    md.append(f"- **Claimed Rent Arrears:** **${tc.claimed_arrears:,.2f}**")
    md.append(f"- **Notice Type / Demand:** {tc.notice_type or '14-Day Demand / Nonpayment Petition'}")
    md.append(f"- **Court Index Number:** `{tc.court_index_number or 'Pending Intake'}`")
    md.append(f"- **Household Composition:** {tc.household_size} person(s) | Annual Income: ${tc.annual_income:,.2f} | Language: {tc.tenant_language}")
    md.append(f"- **Reported Habitability Hazards:** {tc.hazard_narrative}")
    if tc.landlord_notified_date:
        md.append(f"- **Landlord First Notified:** {tc.landlord_notified_date}")
    md.append("")

    # Section 2: Recommended Affirmative Defenses & Statutes
    md.append("## 2. Recommended Legal Defenses & Statutory Grounding")
    if session.applicable_statutes:
        for idx, sm in enumerate(session.applicable_statutes, 1):
            md.append(f"### {idx}. {sm.code_citation} — {sm.ordinance_title}")
            md.append(f"**Remedy:** {sm.remedy_type}")
            if sm.statutory_deadline:
                md.append(f"**Statutory Deadline / Rule:** `{sm.statutory_deadline}`")
            md.append(f"**Legal Defense Application:** {sm.relevance_rationale}\n")
    else:
        md.append("*No specific statutes mapped yet.*\n")

    # Section 3: Corroborated 311 Evidence
    md.append("## 3. Corroborated Municipal 311 Habitability Records")
    if session.corroborated_evidence:
        md.append("| Request ID | Block Address | Hazard Classification | Status | Narrative Snippet |")
        md.append("|---|---|---|---|---|")
        for ev in session.corroborated_evidence:
            narr = ev.complaint_narrative.replace("\n", " ")[:100] + ("..." if len(ev.complaint_narrative) > 100 else "")
            md.append(f"| `{ev.request_id}` | {ev.block_address} | **{ev.hazard_category}** | {ev.inspection_status} | {narr} |")
        md.append("")
    else:
        md.append("*No open residential complaints corroborated on block.*\n")

    # Section 4: Transparent Exclusions & Decoy Audit
    md.append("## 4. Transparent Exclusions & Decoy Audit Trail")
    md.append("> *Vector search acts as a candidate generator. Relational rules enforce `property_type = 'Residential' AND closed_date IS NULL`.*")
    if session.excluded_matches:
        md.append("| Candidate ID | Property Type | Closed Date / Status | Relational Exclusion Reason |")
        md.append("|---|---|---|---|")
        for ex in session.excluded_matches:
            decoy_tag = " `[Planted Decoy]`" if ex.is_planted_decoy else ""
            c_date = ex.closed_date or "Open"
            md.append(f"| `{ex.request_id}`{decoy_tag} | {ex.property_type} | {c_date} | {ex.rejection_reason} |")
        md.append("")
    else:
        md.append("*No near-matches required exclusion.*\n")

    # Section 5: Emergency Relief Funds Action Plan
    md.append("## 5. Emergency Rental Assistance & Stabilization Action Plan")
    if session.eligible_funds:
        for f in session.eligible_funds:
            verdict_badge = "✅ **QUALIFIED**" if f.verdict == "QUALIFIED" else f"⚠️ **{f.verdict}**"
            cap_str = f" (Cap: {f.max_assistance_amount})" if f.max_assistance_amount else ""
            md.append(f"### {f.program_name}{cap_str}")
            md.append(f"- **Verdict:** {verdict_badge} | **Agency:** {f.administering_agency} ({f.funding_stream})")
            md.append(f"- **Habitability Requirement:** {'Required & Corroborated ✅' if f.requires_open_habitability_case and f.habitability_satisfied else ('Required but Uncorroborated ❌' if f.requires_open_habitability_case else 'General Arrears Fund')}")
            md.append(f"- **Eligibility Rationale:** {f.rationale}")
            md.append(f"- **Immediate Caseworker Action:** {f.action_item}\n")
    else:
        md.append("*No relief programs evaluated.*\n")

    # Section 6: Neighborhood Risk Context
    if session.tract_profile:
        tp = session.tract_profile
        md.append("## 6. Neighborhood Eviction Pressure & Structural Context")
        md.append(f"- **Census Tract:** `{tp.census_tract_geoid}` ({tp.metro_area})")
        md.append(f"- **Severe Rent Burden Rate (50%+ income on rent):** **{tp.severe_rent_burden_rate*100:.1f}%** *(Metro median: {tp.metro_median_burden_rate*100:.1f}%)*")
        md.append(f"- **Modeled Annual Nonpayment Filings:** **{tp.annual_nonpayment_filings}** {tp.data_label} *(Metro median: {tp.metro_median_annual_filings})*")
        md.append(f"- **Modeled Default Judgments:** **{tp.annual_default_judgments}** {tp.data_label}")
        md.append(f"- **Median Claimed Arrears in Tract:** **${tp.median_claimed_arrears:,.2f}** {tp.data_label}")
        md.append(f"- **Households Without a Vehicle:** **{tp.no_vehicle_rate*100:.1f}%**")
        if tp.transit_barrier_warning:
            md.append("> ⚠️ **Courthouse Transit Barrier Alert:** Over 70% of tract households lack a private vehicle. Flag subway/bus transit schedule to courthouse and emphasize arriving 45 minutes early to avoid default judgment at calendar call.")
        md.append("")

    # Section 7: Evidentiary Boundaries & What Still Needs Proof
    md.append("## 7. Evidentiary Boundaries — What the Public Record Can't Prove Yet")
    md.append("The 100-block municipal public record corroborates that severe habitability hazards exist on this block, but housing court requires unit-specific proof. The supervising attorney and caseworker must gather the following items before the hearing:")
    limits = [
        "**Apartment-Specific Condition Evidence:** Take dated time-stamped photographs and videos of the cold radiators, boiler temperature log, and mold spreading around the bathroom.",
        "**Notice to Landlord Verification:** Gather copies of text messages, emails, certified mail receipts, or superintendent repair logs proving when the landlord was first alerted.",
        "**Payment Receipts & Ledger:** Reconcile tenant rent receipts against landlord's claimed arrears ledger ($3,350) to dispute improper late fees or misapplied payments.",
        "**Municipal Re-Inspection:** If landlord claims conditions were repaired, immediately file an official municipal 311 re-inspection ticket to generate an updated inspector inspection report for court.",
        "**Transit & Accessibility Check:** Confirm tenant has transit fare and exact route directions to arrive at Housing Court before 9:00 AM.",
    ]
    session.evidentiary_limits = limits
    for item in limits:
        md.append(f"- [ ] {item}")
    md.append("")

    return "\n".join(md)
