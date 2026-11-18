"""Pydantic data models for tenant case intake, defenses, evidence, and briefs."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import date


class TenantCase(BaseModel):
    """Core tenant intake facts collected by caseworker."""
    metro_area: str = "New York"
    block_address: str = Field(..., description="100-block coarsened address, e.g. '1000 Block of St. Nicholas Ave'")
    census_tract_geoid: Optional[str] = None
    hearing_date: Optional[str] = Field(None, description="Court hearing date, e.g. '2026-11-23'")
    hearing_time: Optional[str] = Field(None, description="Court hearing time, e.g. '09:30 AM'")
    claimed_arrears: float = Field(0.0, description="Amount landlord claims is owed in rent")
    notice_type: Optional[str] = Field(None, description="Type of notice received, e.g. '14-Day Demand', 'Nonpayment Petition'")
    court_index_number: Optional[str] = Field(None, description="Court index or case number if petition filed")
    household_size: int = Field(1, description="Number of people in household")
    annual_income: float = Field(0.0, description="Estimated total annual household income")
    hazard_narrative: str = Field(..., description="Tenant's description of physical apartment conditions and timeline")
    landlord_notified_date: Optional[str] = Field(None, description="When landlord/super was first notified")
    tenant_language: str = Field("English", description="Primary language spoken by tenant")


class CorroboratedEvidence(BaseModel):
    """Corroborated open residential 311 complaint matching tenant claims."""
    request_id: str
    block_address: str
    property_type: str
    raw_complaint_type: str
    inspection_status: str
    complaint_narrative: str
    similarity_score: float
    hazard_category: str  # Heat/Boiler, Mold, Water/Leak, Electrical, Pests, Structural
    is_same_block: bool = False


class ExcludedNearMatch(BaseModel):
    """Near-match record or decoy rejected by the relational filter."""
    request_id: str
    block_address: str
    property_type: str
    closed_date: Optional[str] = None
    inspection_status: str
    complaint_narrative: str
    similarity_score: float
    rejection_reason: str
    is_planted_decoy: bool = False


class StatuteMatch(BaseModel):
    """Applicable statutory protection or affirmative defense."""
    code_citation: str
    ordinance_title: str
    remedy_type: str
    relevance_rationale: str
    statutory_deadline: Optional[str] = None


class ReliefFundMatch(BaseModel):
    """Evaluation of an emergency rental assistance fund."""
    program_id: str
    program_name: str
    administering_agency: str
    funding_stream: str
    max_assistance_amount: Optional[str] = None
    requires_open_habitability_case: bool
    habitability_satisfied: bool
    income_satisfied: bool
    arrears_satisfied: bool
    verdict: str  # "QUALIFIED", "PARTIALLY_QUALIFIED", "UNQUALIFIED"
    rationale: str
    action_item: str


class TractRiskProfile(BaseModel):
    """Neighborhood risk indicators avoiding 4x fan-out inflation."""
    census_tract_geoid: str
    metro_area: str
    severe_rent_burden_rate: float
    metro_median_burden_rate: float
    annual_nonpayment_filings: int
    metro_median_annual_filings: int
    annual_default_judgments: int
    median_claimed_arrears: float
    no_vehicle_rate: float
    transit_barrier_warning: bool
    data_label: str = "[Modeled]"


class CaseIntakeSession(BaseModel):
    """Complete intake session state containing facts, defenses, and brief."""
    session_id: str
    tenant_case: TenantCase
    corroborated_evidence: List[CorroboratedEvidence] = []
    excluded_matches: List[ExcludedNearMatch] = []
    applicable_statutes: List[StatuteMatch] = []
    eligible_funds: List[ReliefFundMatch] = []
    tract_profile: Optional[TractRiskProfile] = None
    brief_markdown: Optional[str] = None
    tenant_action_checklist: List[str] = []
    evidentiary_limits: List[str] = []
    building_location: Optional[Dict[str, Any]] = None
