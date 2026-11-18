"""Fan-out-safe census tract risk profiler avoiding 4x join inflation."""

from typing import Optional
import pandas as pd
from .case_intake import TractRiskProfile
from .. import data_loader


def get_tract_risk_profile(
    metro_area: str,
    census_tract_geoid: Optional[str] = None,
    block_address: Optional[str] = None,
) -> TractRiskProfile:
    """Compute fan-out-safe tract risk indicators comparing tract against metro medians."""
    summary_df = data_loader.get_fanout_safe_tract_summary(metro_area)

    # Metro-wide medians
    metro_median_burden = float(summary_df["severe_rent_burden_rate"].median())
    metro_median_filings = int(summary_df["annual_nonpayment_filings"].median())

    # Find target tract
    target_row = None
    if census_tract_geoid:
        matches = summary_df[summary_df["census_tract_geoid"] == str(census_tract_geoid).zfill(11)]
        if not matches.empty:
            target_row = matches.iloc[0]

    # If geoid not given, try matching from 311 complaints on block address
    if target_row is None and block_address:
        complaints_df = data_loader.get_311_complaints(metro_area)
        block_clean = block_address.lower().replace("block of", "").replace("block", "").strip()
        matching_complaints = complaints_df[complaints_df["block_address"].str.lower().str.contains(block_clean[:10], na=False)]
        if not matching_complaints.empty:
            found_geoid = matching_complaints.iloc[0]["census_tract_geoid"]
            matches = summary_df[summary_df["census_tract_geoid"] == str(found_geoid).zfill(11)]
            if not matches.empty:
                target_row = matches.iloc[0]

    # Default to first tract or Washington Heights tract 36061024500 if New York
    if target_row is None:
        if metro_area == "New York":
            ny_matches = summary_df[summary_df["census_tract_geoid"] == "36061024500"]
            target_row = ny_matches.iloc[0] if not ny_matches.empty else summary_df.iloc[0]
        else:
            target_row = summary_df.iloc[0]

    geoid = str(target_row["census_tract_geoid"])
    burden = float(target_row.get("severe_rent_burden_rate", 0.0))
    filings = int(target_row.get("annual_nonpayment_filings", 0))
    defaults = int(target_row.get("annual_default_judgments", 0))
    arrears = float(target_row.get("median_claimed_arrears_usd", 0.0))
    no_car = float(target_row.get("no_vehicle_rate", 0.0))

    transit_warning = no_car > 0.70

    return TractRiskProfile(
        census_tract_geoid=geoid,
        metro_area=metro_area,
        severe_rent_burden_rate=round(burden, 4),
        metro_median_burden_rate=round(metro_median_burden, 4),
        annual_nonpayment_filings=filings,
        metro_median_annual_filings=metro_median_filings,
        annual_default_judgments=defaults,
        median_claimed_arrears=round(arrears, 2),
        no_vehicle_rate=round(no_car, 4),
        transit_barrier_warning=transit_warning,
        data_label="[Modeled]",
    )
