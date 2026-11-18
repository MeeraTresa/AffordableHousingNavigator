"""Subagent 3: Statutory Defense & Counterclaim Strategist."""

from typing import Dict, Any
from .base_agent import BaseSubagent, AgentStatus
from .. import statutes
from ..case_intake import TenantCase


class StatutoryDefenseAgent(BaseSubagent):
    """Subagent responsible for mapping corroborated hazards to affirmative defenses and statutes."""

    def __init__(self):
        super().__init__(
            name="StatutoryDefenseAgent",
            role="Housing Court Defense Strategist",
            description="Maps verified habitability violations to state/municipal warranty of habitability statutes, rent abatements, and cure deadlines."
        )

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.status = AgentStatus.RUNNING
        tc: TenantCase = context.get("tenant_case")
        evidence = context.get("corroborated_evidence", [])

        self.log("Analyzing statutory defenses and repair deadlines under local housing code...", level="INFO")

        statute_matches = statutes.match_statutory_defenses(tc, evidence)
        context["applicable_statutes"] = statute_matches

        self.log(
            f"Identified {len(statute_matches)} affirmative defenses and statutory grounds.",
            level="SUCCESS",
            payload={"citations": [s.code_citation for s in statute_matches]}
        )
        self.status = AgentStatus.COMPLETED
        return context
