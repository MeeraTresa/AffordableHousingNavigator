import os

PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-03-ee26737d3114")
DATASET = os.getenv("A4I_DATASET", "a4i_housing")
BQ_LOCATION = os.getenv("A4I_LOCATION", "US")
METRO = "New York"
MODEL = os.getenv("NAVIGATOR_MODEL", "gemini-2.5-flash")

PROXIMITY_METERS = 800          # ~ 8-10 Manhattan blocks
MIN_SIMILARITY = 0.55           # threshold for relevance
EMERGENCY_HOURS = 96            # hearing within ~4 days

# HHS poverty guidelines (48 states)
FPL_BASE = 15_650
FPL_PER_EXTRA = 5_500

def fpl(household_size: int) -> int:
    return FPL_BASE + FPL_PER_EXTRA * max(household_size - 1, 0)

# Human-readable exclusion reasons
EXCLUSION_REASONS = {
    "commercial": "Commercial property — no residential tenants; cannot support a residential habitability defense.",
    "closed_abated": "Closed – Abated — condition was repaired and re-inspected; not an active hazard.",
    "closed_no_violation": "Closed – No Violation — inspector found no defect; this record would undercut, not support, the claim.",
    "closed_other": "Closed — no longer an open enforcement case.",
    "too_far": "Outside the {m} m corroboration radius from the tenant's block.",
    "low_similarity": "Semantic similarity below threshold — different hazard.",
    "planted": "Labeled [Planted Case] teaching decoy.",
}
