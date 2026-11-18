"""Deterministic eligibility evaluation for emergency rental relief programs."""

from typing import List
import pandas as pd
from .case_intake import ReliefFundMatch, TenantCase, CorroboratedEvidence
from .. import data_loader, config


def evaluate_relief_programs(
    tenant_case: TenantCase,
    corroborated_evidence: List[CorroboratedEvidence],
) -> List[ReliefFundMatch]:
    """Evaluate tenant eligibility for all available emergency relief funds in the metro."""
    metro = tenant_case.metro_area
    bulletins_df = data_loader.get_relief_programs(metro)
    matches: List[ReliefFundMatch] = []

    has_open_habitability = len(corroborated_evidence) > 0
    fpl_200_threshold = config.get_fpl_threshold(tenant_case.household_size, 2.0)
    income = tenant_case.annual_income
    arrears = tenant_case.claimed_arrears
    has_court_index = bool(tenant_case.court_index_number and tenant_case.court_index_number.strip())

    for _, row in bulletins_df.iterrows():
        prog_id = str(row.get("bulletin_id", ""))
        prog_name = str(row.get("program_name", ""))
        agency = str(row.get("administering_agency", ""))
        funding = str(row.get("funding_stream", ""))
        req_habitability = bool(row.get("requires_open_habitability_case", False))
        res_only = bool(row.get("residential_tenants_only", True))
        raw_text = str(row.get("raw_bulletin_text", ""))

        habitability_ok = True
        if req_habitability and not has_open_habitability:
            habitability_ok = False

        income_ok = True
        arrears_ok = True
        max_grant = None
        reasons = []
        action = ""

        # Extract max dollar amount from bulletin text if present
        if "$18,000" in raw_text:
            max_grant = "$18,000"
            arrears_ok = arrears <= 18000
        elif "$15,000" in raw_text:
            max_grant = "$15,000"
            arrears_ok = arrears <= 15000
        elif "$12,000" in raw_text:
            max_grant = "$12,000"
            arrears_ok = arrears <= 12000
        elif "$10,000" in raw_text:
            max_grant = "$10,000"
            arrears_ok = arrears <= 10000
        elif "$8,000" in raw_text:
            max_grant = "$8,000"
            arrears_ok = arrears <= 8000
        elif "$7,500" in raw_text:
            max_grant = "$7,500"
            arrears_ok = arrears <= 7500
        elif "$6,500" in raw_text:
            max_grant = "$6,500"
            arrears_ok = arrears <= 6500
        elif "$6,000" in raw_text:
            max_grant = "$6,000"
            arrears_ok = arrears <= 6000
        elif "$5,500" in raw_text:
            max_grant = "$5,500"
            arrears_ok = arrears <= 5500
        elif "$4,500" in raw_text:
            max_grant = "$4,500"
            arrears_ok = arrears <= 4500
        elif "$4,000" in raw_text:
            max_grant = "$4,000"
            arrears_ok = arrears <= 4000
        elif "$3,500" in raw_text:
            max_grant = "$3,500"
            arrears_ok = arrears <= 3500

        # Income checks
        if "200%" in raw_text or "FPL" in raw_text:
            if income > 0 and income > fpl_200_threshold:
                income_ok = False
                reasons.append(f"Income (${income:,.0f}) exceeds 200% FPL cap (${fpl_200_threshold:,.0f} for household of {tenant_case.household_size})")
            else:
                reasons.append(f"Income satisfies <=200% FPL requirement (${income:,.0f} <= ${fpl_200_threshold:,.0f})")

        # Specific program logic
        if "CityFHEPS" in prog_name:
            if not has_court_index:
                reasons.append("Notice: CityFHEPS pathway requires pending Housing Court index number or active written rent demand")
                action = "Submit copy of 14-day notice or petition to DSS Homebase"
            else:
                reasons.append(f"Court index number present ({tenant_case.court_index_number})")
                action = "Fast-track application through Homebase eviction prevention network"

        elif "One Shot Deal" in prog_name:
            action = "File urgent online application via ACCESS HRA with court index number & notice attached"

        elif "Right to Counsel" in prog_name or "Local Law 136" in prog_name:
            if has_open_habitability:
                reasons.append("Open residential violations corroborated; qualifies for Class C Spiegel defense and legal representation")
                action = "Request Legal Aid / NYLAG Housing Court assignment on Monday intake calendar"
            else:
                reasons.append("Requires active habitability violation to unlock rent-impairing escrow bridge")
                action = "File urgent 311 complaint / HPD inspection request"

        elif "Emergency Repair" in prog_name or "Clinic" in prog_name:
            if has_open_habitability:
                reasons.append(f"Active violations on record qualify household for HP action filing and up to {max_grant} grant")
                action = "Prepare HP Action petition for order to repair"
            else:
                reasons.append("Requires open code-enforcement case on block")
                action = "Inspect block violation records"

        if not habitability_ok:
            reasons.append("FAILS habitability requirement: No open residential code violations corroborated on block.")

        # Determine verdict
        if habitability_ok and income_ok and arrears_ok:
            verdict = "QUALIFIED"
        elif not habitability_ok or not income_ok:
            verdict = "UNQUALIFIED"
        else:
            verdict = "PARTIALLY_QUALIFIED"

        matches.append(
            ReliefFundMatch(
                program_id=prog_id,
                program_name=prog_name,
                administering_agency=agency,
                funding_stream=funding,
                max_assistance_amount=max_grant,
                requires_open_habitability_case=req_habitability,
                habitability_satisfied=habitability_ok,
                income_satisfied=income_ok,
                arrears_satisfied=arrears_ok,
                verdict=verdict,
                rationale="; ".join(reasons),
                action_item=action or f"Contact {agency} to submit intake packet",
            )
        )

    # Sort qualified first
    matches.sort(key=lambda m: (m.verdict != "QUALIFIED", m.verdict != "PARTIALLY_QUALIFIED"))
    return matches
