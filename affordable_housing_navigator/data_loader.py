"""Data loader providing parquet and BigQuery access for housing datasets."""

from typing import Optional
import pandas as pd
from . import config

# In-memory cache for parquet dataframes
_CACHE = {}


def load_parquet_table(table_name: str) -> pd.DataFrame:
    """Load a parquet table from data/ directory with caching."""
    if table_name not in _CACHE:
        file_path = config.DATA_DIR / f"{table_name}.parquet"
        if not file_path.exists():
            raise FileNotFoundError(f"Parquet table not found: {file_path}")
        df = pd.read_parquet(file_path)
        # Ensure census_tract_geoid is always string with leading zeros preserved
        if "census_tract_geoid" in df.columns:
            df["census_tract_geoid"] = df["census_tract_geoid"].astype(str).str.zfill(11)
        _CACHE[table_name] = df
    return _CACHE[table_name].copy()


def get_311_complaints(metro_area: Optional[str] = None) -> pd.DataFrame:
    """Return municipal 311 housing complaints filtered by metro_area."""
    df = load_parquet_table("municipal_311_housing_complaints")
    if metro_area:
        df = df[df["metro_area"] == metro_area].copy()
    return df


def get_statutes(metro_area: Optional[str] = None) -> pd.DataFrame:
    """Return municipal housing ordinance statutes filtered by metro_area."""
    df = load_parquet_table("municipal_housing_ordinance_statutes")
    if metro_area:
        df = df[df["metro_area"] == metro_area].copy()
    return df


def get_relief_programs(metro_area: Optional[str] = None) -> pd.DataFrame:
    """Return rental relief program bulletins filtered by metro_area."""
    df = load_parquet_table("rental_relief_program_bulletins")
    if metro_area:
        df = df[df["metro_area"] == metro_area].copy()
    return df


def get_court_filings(metro_area: Optional[str] = None) -> pd.DataFrame:
    """Return court eviction filings [Modeled] filtered by metro_area."""
    df = load_parquet_table("court_eviction_filings")
    if metro_area:
        df = df[df["metro_area"] == metro_area].copy()
    return df


def get_tract_tenure(metro_area: Optional[str] = None) -> pd.DataFrame:
    """Return ACS tract housing tenure filtered by metro_area."""
    df = load_parquet_table("acs_tract_housing_tenure")
    if metro_area:
        df = df[df["metro_area"] == metro_area].copy()
    return df


def get_fanout_safe_tract_summary(metro_area: str) -> pd.DataFrame:
    """Pre-aggregate court_eviction_filings by tract before joining to acs_tract_housing_tenure.
    
    This avoids the 4x fan-out trap (4 reporting quarters per tract in court_eviction_filings).
    """
    tenure_df = get_tract_tenure(metro_area)
    filings_df = get_court_filings(metro_area)

    # 1. Pre-aggregate filings by census_tract_geoid
    filings_agg = filings_df.groupby("census_tract_geoid").agg(
        annual_nonpayment_filings=("nonpayment_filings_count", "sum"),
        annual_holdover_filings=("holdover_or_no_fault_filings_count", "sum"),
        annual_default_judgments=("default_judgments_count", "sum"),
        median_claimed_arrears_usd=("median_claimed_arrears_usd", "median"),
    ).reset_index()

    # 2. Join 1:1 with tract tenure
    merged = pd.merge(
        tenure_df,
        filings_agg,
        on="census_tract_geoid",
        how="left",
    )

    # Calculate severe rent burden rate (50%+ rent burden / renter units)
    if "renter_occupied_units" in merged.columns and "renter_hh_rent_50_pct_plus_count" in merged.columns:
        merged["severe_rent_burden_rate"] = (
            merged["renter_hh_rent_50_pct_plus_count"] / merged["renter_occupied_units"].replace(0, pd.NA)
        ).fillna(0.0)

    return merged
