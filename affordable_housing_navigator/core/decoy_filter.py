"""Relational post-filter enforcing residential and open status, explaining exclusions."""

from typing import Tuple, List, Dict, Any
import pandas as pd
from .case_intake import CorroboratedEvidence, ExcludedNearMatch


def classify_hazard(narrative: str, complaint_type: str = "") -> str:
    """Classify complaint narrative into habitability hazard category."""
    text = (narrative + " " + complaint_type).lower()
    if any(k in text for k in ["heat", "boiler", "radiator", "cold", "hot water", "warmth"]):
        return "Heat / Boiler / Hot Water (Class C Life-Safety)"
    if any(k in text for k in ["mold", "mildew", "spore", "fungus", "asthma"]):
        return "Visible Mold & Environmental Hazard (Class A/B)"
    if any(k in text for k in ["leak", "water", "pipe", "ceiling", "drip", "sewage", "drain"]):
        return "Water Intrusion & Plumbing (Class B Hazardous)"
    if any(k in text for k in ["electric", "wire", "breaker", "fuse", "spark", "shock"]):
        return "Electrical Safety & Fire Hazard"
    if any(k in text for k in ["lead", "paint", "peeling"]):
        return "Lead-Based Paint Hazard"
    if any(k in text for k in ["rat", "mouse", "mice", "roach", "pest", "vermin", "bedbug"]):
        return "Severe Infestation / Vermin"
    return "General Habitability & Code Violation"


def filter_candidates(
    candidates_df: pd.DataFrame,
    tenant_block: str = "",
) -> Tuple[List[CorroboratedEvidence], List[ExcludedNearMatch]]:
    """Apply the required relational filter: property_type == 'Residential' AND closed_date IS NULL.
    
    Any excluded row carries a human-readable explanation of why it was rejected.
    """
    kept: List[CorroboratedEvidence] = []
    excluded: List[ExcludedNearMatch] = []

    tenant_block_norm = tenant_block.lower().replace("block of ", "").replace("block ", "").strip()

    for _, row in candidates_df.iterrows():
        req_id = str(row.get("request_id", ""))
        prop_type = str(row.get("property_type", ""))
        closed_date = row.get("closed_date")
        insp_status = str(row.get("inspection_status", ""))
        narrative = str(row.get("complaint_narrative", ""))
        complaint_type = str(row.get("raw_complaint_type", ""))
        block_addr = str(row.get("block_address", ""))
        similarity = float(row.get("similarity_score", 0.0))
        is_decoy = "DECOY" in req_id or "[Planted Case]" in str(row.get("data_provenance", ""))

        rejection_reason = None

        # Rule 1: Must be Residential property
        if prop_type.lower() != "residential":
            rejection_reason = f"Commercial/Non-Residential property ('{prop_type}'). Commercial units are not covered by residential tenant protections."

        # Rule 2: Must be an OPEN case (closed_date is NULL)
        elif pd.notna(closed_date) and str(closed_date).strip() != "":
            rejection_reason = f"Closed case (closed on {str(closed_date)[:10]}). Inspector or landlord marked condition as abated/resolved."

        # Rule 3: Inspection status indicates no violation found
        elif any(phrase in insp_status.lower() for phrase in ["no violation", "not violation", "condition not found"]):
            rejection_reason = f"Inspection resolved with no violation found ('{insp_status}'). Cannot corroborate active code breach."

        if rejection_reason:
            excluded.append(
                ExcludedNearMatch(
                    request_id=req_id,
                    block_address=block_addr,
                    property_type=prop_type,
                    closed_date=str(closed_date) if pd.notna(closed_date) else None,
                    inspection_status=insp_status,
                    complaint_narrative=narrative,
                    similarity_score=similarity,
                    rejection_reason=rejection_reason,
                    is_planted_decoy=is_decoy,
                )
            )
        else:
            is_same_block = bool(tenant_block_norm and tenant_block_norm in block_addr.lower())
            hazard_cat = classify_hazard(narrative, complaint_type)
            kept.append(
                CorroboratedEvidence(
                    request_id=req_id,
                    block_address=block_addr,
                    property_type=prop_type,
                    raw_complaint_type=complaint_type,
                    inspection_status=insp_status,
                    complaint_narrative=narrative,
                    similarity_score=similarity,
                    hazard_category=hazard_cat,
                    is_same_block=is_same_block,
                )
            )

    return kept, excluded
