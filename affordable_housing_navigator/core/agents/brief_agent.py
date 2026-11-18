"""Subagent 6: Attorney Brief & Action Plan Synthesizer."""

from typing import Dict, Any
from .base_agent import BaseSubagent, AgentStatus
from .. import brief_builder
from ..case_intake import CaseIntakeSession, TenantCase


class BriefCompilerAgent(BaseSubagent):
    """Subagent responsible for assembling the court-ready Tenant Stabilization Brief and action plan."""

    def __init__(self):
        super().__init__(
            name="BriefCompilerAgent",
            role="Attorney Brief & Action Plan Synthesizer",
            description="Compiles corroborated evidence, defenses, funds, and evidentiary limits into an intake brief."
        )

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.status = AgentStatus.RUNNING
        session_id = context.get("session_id", "INTAKE-AUTO")
        tc: TenantCase = context.get("tenant_case")

        self.log("Synthesizing court-ready Tenant Stabilization Brief and action checklist...", level="INFO")

        session = CaseIntakeSession(
            session_id=session_id,
            tenant_case=tc,
            corroborated_evidence=context.get("corroborated_evidence", []),
            excluded_matches=context.get("excluded_matches", []),
            applicable_statutes=context.get("applicable_statutes", []),
            eligible_funds=context.get("eligible_funds", []),
            tract_profile=context.get("tract_profile"),
            building_location=context.get("building_location"),
        )

        brief_md = brief_builder.build_tenant_stabilization_brief(session)
        session.brief_markdown = brief_md
        context["brief_markdown"] = brief_md
        context["case_session"] = session

        self.log(
            f"Brief compiled successfully ({len(brief_md.splitlines())} lines). Evidentiary boundaries codified.",
            level="SUCCESS"
        )
        self.status = AgentStatus.COMPLETED
        return context
