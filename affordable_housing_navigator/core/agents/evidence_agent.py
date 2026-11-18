"""Subagent 2: Municipal Code & Habitability Corroborator."""

from typing import Dict, Any
from .base_agent import BaseSubagent, AgentStatus
from .. import vector_search
from ..case_intake import TenantCase


class EvidenceCorroboratorAgent(BaseSubagent):
    """Subagent responsible for vector search over municipal 311 complaints and decoy resilience."""

    def __init__(self):
        super().__init__(
            name="EvidenceCorroboratorAgent",
            role="Municipal 311 Habitability Corroborator",
            description="Executes semantic vector search against municipal 311 records and filters out commercial/closed decoys."
        )

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.status = AgentStatus.RUNNING
        tc: TenantCase = context.get("tenant_case")
        if not tc:
            self.log("Missing tenant_case in context", level="ERROR")
            self.status = AgentStatus.FAILED
            return context

        self.log(f"Searching 311 housing records for query: '{tc.hazard_narrative[:60]}...'", level="INFO")

        kept_ev, excluded = vector_search.search_habitability_evidence(
            query=tc.hazard_narrative,
            metro_area=tc.metro_area,
            tenant_block=tc.block_address,
            top_k=20,
        )

        context["corroborated_evidence"] = kept_ev
        context["excluded_matches"] = excluded

        decoy_count = sum(1 for e in excluded if e.is_planted_decoy)
        self.log(
            f"Corroborated {len(kept_ev)} open residential violations. Excluded {len(excluded)} non-qualifying near-matches ({decoy_count} planted decoys caught).",
            level="SUCCESS",
            payload={"kept_count": len(kept_ev), "excluded_count": len(excluded), "decoys_caught": decoy_count}
        )
        self.status = AgentStatus.COMPLETED
        return context
