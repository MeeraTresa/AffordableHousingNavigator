"""Subagent 5: Neighborhood Displacement & Equity Auditor."""

from typing import Dict, Any
from .base_agent import BaseSubagent, AgentStatus
from .. import tract_context
from ..case_intake import TenantCase


class TractContextAgent(BaseSubagent):
    """Subagent responsible for fan-out-safe census tract risk indicators and transit barrier warnings."""

    def __init__(self):
        super().__init__(
            name="TractContextAgent",
            role="Neighborhood Risk & Spatial Equity Monitor",
            description="Aggregates census tract tenure and modeled court filings without 4x fan-out, flagging transit barriers."
        )

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.status = AgentStatus.RUNNING
        tc: TenantCase = context.get("tenant_case")

        self.log(f"Paging census tract indicators for metro '{tc.metro_area}'...", level="INFO")

        tract_profile = tract_context.get_tract_risk_profile(
            metro_area=tc.metro_area,
            census_tract_geoid=tc.census_tract_geoid,
            block_address=tc.block_address,
        )
        context["tract_profile"] = tract_profile

        alerts = []
        if tract_profile.transit_barrier_warning:
            alerts.append(f"High transit barrier: {tract_profile.no_vehicle_rate*100:.1f}% households without private vehicle.")

        self.log(
            f"Tract {tract_profile.census_tract_geoid}: Severe Rent Burden = {tract_profile.severe_rent_burden_rate*100:.1f}% (Metro median: {tract_profile.metro_median_burden_rate*100:.1f}%), Modeled Filings = {tract_profile.annual_nonpayment_filings} [Modeled].",
            level="SUCCESS" if not alerts else "WARNING",
            payload={"geoid": tract_profile.census_tract_geoid, "alerts": alerts}
        )
        self.status = AgentStatus.COMPLETED
        return context
