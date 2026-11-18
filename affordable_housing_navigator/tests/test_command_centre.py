"""Test multi-agent Command Centre coordinator and subagent lifecycle."""

import pytest
from affordable_housing_navigator.core.agents import CommandCentreCoordinator, AgentStatus


def test_command_centre_pipeline_execution():
    """Verify that CommandCentreCoordinator executes all 6 subagents in sequence."""
    coordinator = CommandCentreCoordinator()
    assert len(coordinator.subagents) == 6

    raw_input = {
        "metro_area": "New York",
        "block_address": "1000 Block of St. Nicholas Ave",
        "census_tract_geoid": "36061024500",
        "hearing_date": "2026-11-23",
        "hearing_time": "09:30 AM",
        "claimed_arrears": 3350.0,
        "notice_type": "Nonpayment Petition",
        "court_index_number": "LT-029481/26",
        "household_size": 3,
        "annual_income": 31000.0,
        "hazard_narrative": "Radiators cold since early Nov. Black mold around tub. Water coming through bathroom wall.",
        "tenant_language": "Spanish",
    }

    session = coordinator.execute_pipeline(raw_input)

    # 1. Check all subagents completed
    for agent in coordinator.subagents:
        assert agent.status == AgentStatus.COMPLETED, f"Agent {agent.name} did not complete, status is {agent.status}"
        assert len(agent.events) > 0, f"Agent {agent.name} produced no telemetry events"

    # 2. Check aggregated events
    all_events = coordinator.get_all_events()
    assert len(all_events) >= 10
    agent_names_logged = {e.agent_name for e in all_events}
    assert agent_names_logged == {
        "IntakeAgent",
        "EvidenceCorroboratorAgent",
        "StatutoryDefenseAgent",
        "ReliefFundMatcherAgent",
        "TractContextAgent",
        "BriefCompilerAgent",
    }

    # 3. Check artifacts produced
    assert session.session_id.startswith("CC-")
    assert len(session.corroborated_evidence) > 0
    assert len(session.excluded_matches) > 0
    assert len(session.applicable_statutes) == 3
    assert len(session.eligible_funds) == 4
    assert session.tract_profile is not None
    assert session.brief_markdown is not None
    assert "TENANT STABILIZATION BRIEF" in session.brief_markdown
