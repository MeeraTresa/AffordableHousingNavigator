"""Subagent 4: Emergency Relief Fund Allocator."""

from typing import Dict, Any
from .base_agent import BaseSubagent, AgentStatus
from .. import relief_funds
from ..case_intake import TenantCase


class ReliefFundMatcherAgent(BaseSubagent):
    """Subagent responsible for emergency rental assistance triage and habitability-gate checks."""

    def __init__(self):
        super().__init__(
            name="ReliefFundMatcherAgent",
            role="Relief Fund Eligibility Coordinator",
            description="Evaluates tenant eligibility for emergency rental relief streams and unlocks habitability-gated funds."
        )

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.status = AgentStatus.RUNNING
        tc: TenantCase = context.get("tenant_case")
        evidence = context.get("corroborated_evidence", [])

        self.log(f"Evaluating emergency relief funds for claimed arrears of ${tc.claimed_arrears:,.2f}...", level="INFO")

        fund_matches = relief_funds.evaluate_relief_programs(tc, evidence)
        context["eligible_funds"] = fund_matches

        qualified = [f for f in fund_matches if f.verdict == "QUALIFIED"]
        habitability_unlocked = [f for f in qualified if f.requires_open_habitability_case]

        self.log(
            f"Evaluated {len(fund_matches)} funds: {len(qualified)} QUALIFIED ({len(habitability_unlocked)} unlocked via open habitability evidence).",
            level="SUCCESS",
            payload={"qualified_count": len(qualified), "habitability_unlocked": len(habitability_unlocked)}
        )
        self.status = AgentStatus.COMPLETED
        return context
