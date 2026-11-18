"""Test decoy resilience: verify all planted DECOY-* records are excluded with reasons."""

import pytest
from affordable_housing_navigator import data_loader
from affordable_housing_navigator.core import decoy_filter, vector_search


def test_all_planted_decoys_are_filtered_out():
    """Verify that every planted decoy in municipal_311 is rejected across all metros."""
    complaints = data_loader.get_311_complaints()
    decoy_rows = complaints[complaints["request_id"].str.startswith("DECOY-")].copy()
    assert len(decoy_rows) == 54  # 9 decoys * 6 metros = 54 planted cases

    # Run through filter
    decoy_rows["similarity_score"] = 0.99
    kept, excluded = decoy_filter.filter_candidates(decoy_rows)

    assert len(kept) == 0, f"Expected 0 decoys to pass filter, but {len(kept)} passed: {[k.request_id for k in kept]}"
    assert len(excluded) == 54, f"Expected all 54 decoys to be excluded, got {len(excluded)}"

    # Ensure every single excluded decoy has a clear, non-empty human-readable rejection reason
    for ex in excluded:
        assert ex.rejection_reason and len(ex.rejection_reason) > 10
        assert ex.is_planted_decoy is True


def test_vector_search_rejects_decoys_on_heat_query():
    """Verify vector search on 'boiler broken no heat' rejects commercial/closed decoys."""
    kept, excluded = vector_search.search_habitability_evidence(
        query="no heat in apartment radiators cold boiler broken",
        metro_area="New York",
        top_k=20,
    )
    # Kept should contain only Residential with NULL closed_date
    for k in kept:
        assert k.property_type.lower() == "residential"
        assert not k.request_id.startswith("DECOY-")

    # Excluded should contain decoys or closed/commercial records with reasons
    for e in excluded:
        assert e.rejection_reason != ""
