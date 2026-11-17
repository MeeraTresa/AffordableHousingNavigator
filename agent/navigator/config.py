from datetime import datetime, timezone
from zoneinfo import ZoneInfo

PROJECT = "qwiklabs-gcp-03-ee26737d3114"
DATASET = "a4i_housing"
BQ_LOCATION = "US"
CONNECTION_ID = "us.a4i-vertex"
EMBEDDING_MODEL = "gemini-embedding-2"
NAVIGATOR_MODEL = "gemini-2.5-flash"
MODEL = "gemini-2.5-flash"

RADIUS_METERS = 800
PROXIMITY_METERS = 800
TOP_K = 15
MIN_SIMILARITY = 0.50
EMERGENCY_HOURS = 48
METRO = "New York"
NYC_TZ = ZoneInfo("America/New_York")

def calculate_hours_to_hearing(hearing_iso: str) -> float:
    """Calculate hours to hearing in New York Eastern Time."""
    if not hearing_iso:
        return 999.0
    try:
        if "T" in hearing_iso:
            dt_part = hearing_iso.split("+")[0].split("Z")[0]
            naive_dt = datetime.fromisoformat(dt_part)
            hearing_dt = naive_dt.replace(tzinfo=NYC_TZ)
        else:
            hearing_dt = datetime.fromisoformat(hearing_iso)
            if hearing_dt.tzinfo is None:
                hearing_dt = hearing_dt.replace(tzinfo=NYC_TZ)

        now_nyc = datetime.now(NYC_TZ)
        delta = hearing_dt - now_nyc
        return max(0.0, delta.total_seconds() / 3600.0)
    except Exception:
        return 999.0

# 2026 Federal Poverty Line
FPL_BASE = 15650
FPL_PER_PERSON = 5500

def get_fpl(household_size: int) -> float:
    return FPL_BASE + max(0, household_size - 1) * FPL_PER_PERSON

def get_200_pct_fpl(household_size: int) -> float:
    return 2.0 * get_fpl(household_size)

fpl = get_fpl

EXCLUSION_REASONS = {
    "commercial": "Commercial property type; not residential tenant corroboration.",
    "closed": "Violation is marked closed/abated as of record date.",
    "closed_abated": "Violation was marked closed/abated as of record date.",
    "closed_no_violation": "City inspection found no violation.",
    "closed_other": "Ticket closed prior to hearing date.",
    "too_far": "Beyond 800m corroboration radius from tenant block.",
    "distance": "Beyond 800m corroboration radius from tenant block.",
    "low_similarity": "Below semantic similarity threshold.",
    "planted": "[Planted Case] Known decoy record.",
}
STANDARD_EXCLUSION_REASONS = EXCLUSION_REASONS
