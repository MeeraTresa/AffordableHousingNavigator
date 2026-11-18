"""Statutory defense and tenant protection matcher based on local housing ordinances."""

from typing import List, Optional
import pandas as pd
from .case_intake import StatuteMatch, TenantCase, CorroboratedEvidence
from .. import data_loader


def match_statutory_defenses(
    tenant_case: TenantCase,
    corroborated_evidence: List[CorroboratedEvidence],
) -> List[StatuteMatch]:
    """Identify applicable statutory protections and affirmative defenses for tenant's case."""
    metro = tenant_case.metro_area
    statutes_df = data_loader.get_statutes(metro)
    matches: List[StatuteMatch] = []

    has_heat_hazard = any("heat" in e.hazard_category.lower() or "boiler" in e.hazard_category.lower() for e in corroborated_evidence) or any(k in tenant_case.hazard_narrative.lower() for k in ["heat", "boiler", "cold", "radiator"])
    has_leak_or_mold = any("mold" in e.hazard_category.lower() or "water" in e.hazard_category.lower() for e in corroborated_evidence) or any(k in tenant_case.hazard_narrative.lower() for k in ["mold", "leak", "drip", "water"])
    has_open_evidence = len(corroborated_evidence) > 0

    for _, row in statutes_df.iterrows():
        citation = str(row.get("code_citation", ""))
        title = str(row.get("ordinance_title", ""))
        text = str(row.get("raw_statute_text", ""))

        relevance = ""
        deadline = None

        if metro == "New York":
            if "RPL § 235-b" in citation or "RPAPL § 711" in citation:
                relevance = (
                    "Affirmative Defense: Implied Warranty of Habitability. Under NY RPL § 235-b, tenant is entitled to a rent abatement for days apartment was without essential services (heat/hot water/leakage). Also verify strict compliance with RPAPL § 711(2) 14-day written rent demand requirement prior to nonpayment petition."
                )
                deadline = "14 days prior written demand required before petition filing"
            elif "27-2115" in citation or "Right to Counsel" in title:
                relevance = (
                    "Housing Maintenance Code Enforcement & Counsel: NYC Admin Code § 27-2115 mandates Class C immediately hazardous violations (such as lack of heat/hot water) must be cured within 24 hours. Class B hazardous violations (leaks/mold) must be cured within 30 days. Tenant <=200% FPL qualifies for full Right to Counsel legal representation."
                )
                deadline = "24 hours for Class C (Heat); 30 days for Class B (Leaks/Mold)"
            elif "143-b" in citation or "Spiegel" in title:
                relevance = (
                    "Complete Defense / Rent Suspension: Under NY Social Services Law § 143-b (Spiegel Law) and MDL § 302-a, severe uncorrected rent-impairing or hazardous housing code violations on public record can form a complete defense against nonpayment eviction proceedings."
                )
                deadline = "Applicable if condition remains uncorrected on municipal violation record"

        elif metro == "San Francisco":
            if "1941.1" in citation:
                relevance = (
                    "Affirmative Defense & Rent Bar: Under Cal. Civ. Code § 1941.1 & § 1942.4, landlord is barred from demanding rent, increasing rent, or serving a 3-day notice to pay or quit when premises substantially lack tenantable habitability conditions."
                )
                deadline = "35 days after notice or immediate if dangerous condition"
            elif "1942.5" in citation:
                relevance = (
                    "Anti-Retaliation Defense: Cal. Civ. Code § 1942.5 establishes a statutory defense if eviction was initiated within 180 days after tenant complained about habitability or called building inspectors."
                )
                deadline = "180-day statutory anti-retaliation bar"
            elif "Prop F" in citation or "Right to Counsel" in title:
                relevance = (
                    "San Francisco Universal Right to Counsel (Prop F): Guarantees free legal representation for residential tenants facing eviction proceedings, regardless of income."
                )

        elif metro == "Chicago":
            if "5-12-110" in citation:
                relevance = (
                    "Chicago RLTO Habitability Defense: Under Mun. Code § 5-12-110, covered tenants may withhold rent or exercise repair-and-deduct rights after delivering written notice of failure to maintain habitability standards."
                )
                deadline = "14 days written notice to landlord"
            elif "5-12-150" in citation:
                relevance = (
                    "Rebuttable Presumption of Retaliation: Mun. Code § 5-12-150 creates a legal presumption of unlawful landlord retaliation if eviction is brought within 12 months of habitability complaint."
                )
                deadline = "12 months following code complaint"
            elif "735 ILCS" in citation:
                relevance = (
                    "Mandatory 5-Day Notice & Mediation: Strict compliance with Illinois 5-day cure notice required; Cook County Early Resolution Program (ERP) mandates mediation opportunity."
                )
                deadline = "Strict 5-day statutory notice"

        else:
            # General fallback using statute text
            relevance = f"Statutory protection under {title}: {text[:200]}..."

        if relevance:
            matches.append(
                StatuteMatch(
                    code_citation=citation,
                    ordinance_title=title,
                    remedy_type="Affirmative Defense / Statutory Abatement",
                    relevance_rationale=relevance,
                    statutory_deadline=deadline,
                )
            )

    return matches
