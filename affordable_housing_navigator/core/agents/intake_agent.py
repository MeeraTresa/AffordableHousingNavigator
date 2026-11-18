"""Subagent 1: Tenant Intake & Multilingual Interviewer."""

from typing import Dict, Any
from .base_agent import BaseSubagent, AgentStatus
from ..case_intake import TenantCase
from ...translation import translator


class IntakeAgent(BaseSubagent):
    """Subagent responsible for client engagement, multilingual translation, and fact extraction."""

    def __init__(self):
        super().__init__(
            name="IntakeAgent",
            role="Client Intake & Multilingual Interviewer",
            description="Interacts with tenant in native language, extracts structured case facts, and translates dialogue."
        )

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.status = AgentStatus.RUNNING
        raw_input = context.get("raw_input", {})
        tenant_lang = raw_input.get("tenant_language", "English")

        self.log(f"Starting intake session in language: {tenant_lang}", level="INFO")

        # Create or parse structured TenantCase
        tc = TenantCase(
            metro_area=raw_input.get("metro_area", "New York"),
            block_address=raw_input.get("block_address", ""),
            census_tract_geoid=raw_input.get("census_tract_geoid"),
            hearing_date=raw_input.get("hearing_date"),
            hearing_time=raw_input.get("hearing_time"),
            claimed_arrears=float(raw_input.get("claimed_arrears", 0.0)),
            notice_type=raw_input.get("notice_type"),
            court_index_number=raw_input.get("court_index_number"),
            household_size=int(raw_input.get("household_size", 1)),
            annual_income=float(raw_input.get("annual_income", 0.0)),
            hazard_narrative=raw_input.get("hazard_narrative", ""),
            landlord_notified_date=raw_input.get("landlord_notified_date"),
            tenant_language=tenant_lang,
        )

        # Translation check
        if tenant_lang.lower() not in ("english", "en"):
            translated_welcome = translator.translate_text("welcome", target_lang=tenant_lang[:2].lower())
            context["tenant_translated_greeting"] = translated_welcome
            self.log(f"Generated greeting for tenant: '{translated_welcome[:40]}...'", level="INFO")

        context["tenant_case"] = tc
        self.log(
            f"Extracted intake facts: Block='{tc.block_address}', Arrears=${tc.claimed_arrears:,.2f}, Hearing='{tc.hearing_date or 'N/A'}'",
            level="SUCCESS",
            payload={"block": tc.block_address, "arrears": tc.claimed_arrears}
        )
        self.status = AgentStatus.COMPLETED
        return context
