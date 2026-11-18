"""Test fan-out safety: verify tract joins aggregate 4-quarter filings without multiplication."""

import pytest
from affordable_housing_navigator import data_loader


def test_tract_counts_match_expected():
    """Verify that tract summaries match real census tract counts for all metros."""
    expected = {
        "New York": 168,
        "San Francisco": 42,
        "Chicago": 42,
        "Austin": 42,
        "Baton Rouge": 42,
        "Cincinnati": 42,
    }
    for metro, exp_count in expected.items():
        summary = data_loader.get_fanout_safe_tract_summary(metro)
        assert len(summary) == exp_count, f"Metro {metro} produced {len(summary)} tracts, expected {exp_count}"


def test_geoid_is_always_11_char_string():
    """Verify census_tract_geoid is always string of 11 characters (preserving leading zeros)."""
    # Test San Francisco (state FIPS 06) and New York (state FIPS 36)
    for metro in ["San Francisco", "New York"]:
        summary = data_loader.get_fanout_safe_tract_summary(metro)
        for geoid in summary["census_tract_geoid"]:
            assert isinstance(geoid, str), f"GEOID {geoid} is not a string!"
            assert len(geoid) == 11, f"GEOID {geoid} does not have 11 characters (leading zero lost!)"
            if metro == "San Francisco":
                assert geoid.startswith("06"), f"SF GEOID {geoid} lost leading zero!"
