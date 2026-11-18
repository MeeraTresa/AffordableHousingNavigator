"""Command Centre Coordinator: Orchestrates subagents for full intake and defense lifecycle."""

import uuid
from typing import Dict, Any, List
from .base_agent import AgentEvent
from .intake_agent import IntakeAgent
from .evidence_agent import EvidenceCorroboratorAgent
from .defense_agent import StatutoryDefenseAgent
from .relief_agent import ReliefFundMatcherAgent
from .tract_agent import TractContextAgent
from .brief_agent import BriefCompilerAgent
from ..case_intake import CaseIntakeSession


class CommandCentreCoordinator:
    """Central AI orchestrator coordinating all specialized housing subagents."""

    def __init__(self):
        self.intake_agent = IntakeAgent()
        self.evidence_agent = EvidenceCorroboratorAgent()
        self.defense_agent = StatutoryDefenseAgent()
        self.relief_agent = ReliefFundMatcherAgent()
        self.tract_agent = TractContextAgent()
        self.brief_agent = BriefCompilerAgent()

        self.subagents = [
            self.intake_agent,
            self.evidence_agent,
            self.defense_agent,
            self.relief_agent,
            self.tract_agent,
            self.brief_agent,
        ]

    def get_all_events(self) -> List[AgentEvent]:
        """Aggregate chronological audit logs from all subagents."""
        all_events = []
        for agent in self.subagents:
            all_events.extend(agent.events)
        return all_events

    def execute_pipeline(self, raw_intake_input: Dict[str, Any]) -> CaseIntakeSession:
        """Run the end-to-end multi-agent Command Centre pipeline."""
        session_id = f"CC-{uuid.uuid4().hex[:8].upper()}"
        context: Dict[str, Any] = {
            "session_id": session_id,
            "raw_input": raw_intake_input,
        }

        # Step 1: Intake & Multilingual Extraction
        context = self.intake_agent.run(context)

        # Resolve Building Location & Google Maps Coordinates (stripping any apartment PII)
        from ..building_mapper import resolve_building_location
        tc = context["tenant_case"]
        bld_info = resolve_building_location(tc.block_address, metro_area=tc.metro_area, census_tract_geoid=tc.census_tract_geoid)
        context["building_location"] = bld_info
        if not tc.census_tract_geoid and bld_info.get("census_tract_geoid"):
            tc.census_tract_geoid = bld_info["census_tract_geoid"]

        # Step 2: Municipal 311 Evidence Corroboration & Decoy Resilience
        context = self.evidence_agent.run(context)

        # Step 3: Statutory Defense & Counterclaim Strategy
        context = self.defense_agent.run(context)

        # Step 4: Emergency Relief Program Evaluation (Habitability Gate)
        context = self.relief_agent.run(context)

        # Step 5: Census Tract Displacement & Transit Context
        context = self.tract_agent.run(context)

        # Step 6: Attorney Brief & Action Plan Synthesis
        context = self.brief_agent.run(context)

        return context["case_session"]
