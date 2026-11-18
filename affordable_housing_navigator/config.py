"""Configuration settings for Affordable Housing Navigator."""

from pathlib import Path
import os
from pydantic import BaseModel

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
DATA_DIR = REPO_ROOT / "data"

# Google Cloud & BigQuery Settings
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "a4i_housing")
BIGQUERY_LOCATION = os.getenv("BIGQUERY_LOCATION", "US")
VERTEX_CONNECTION_ID = os.getenv("VERTEX_CONNECTION_ID", "us.a4i-vertex")
EMBEDDING_ENDPOINT = os.getenv("EMBEDDING_ENDPOINT", "gemini-embedding-2")
USE_BIGQUERY = os.getenv("USE_BIGQUERY", "false").lower() in ("true", "1", "yes")

# Supported Metropolitan Corridors
SUPPORTED_METROS = [
    "New York",
    "San Francisco",
    "Chicago",
    "Austin",
    "Baton Rouge",
    "Cincinnati",
]
DEFAULT_METRO = os.getenv("DEFAULT_METRO", "New York")

# 2026 Federal Poverty Guidelines (48 contiguous states & DC)
# NYC Housing Court programs (Right to Counsel, One Shot Deal, CityFHEPS) use <=200% FPL
FPL_ANNUAL_BASELINE = {
    1: 15650,
    2: 21150,
    3: 26650,
    4: 32150,
    5: 37650,
    6: 43150,
    7: 48650,
    8: 54150,
}
FPL_ADDITIONAL_PERSON = 5500


def get_fpl_threshold(household_size: int, multiplier: float = 2.0) -> float:
    """Calculate FPL dollar threshold for a given household size and multiplier (e.g., 2.0 for 200%)."""
    size = max(1, int(household_size))
    if size <= 8:
        base = FPL_ANNUAL_BASELINE[size]
    else:
        base = FPL_ANNUAL_BASELINE[8] + (size - 8) * FPL_ADDITIONAL_PERSON
    return base * multiplier
