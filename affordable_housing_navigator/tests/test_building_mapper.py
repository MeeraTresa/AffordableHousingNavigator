"""Test building location identification and Google Maps integration without PII."""

import pytest
from affordable_housing_navigator.core.building_mapper import clean_address_strip_units, resolve_building_location


def test_strip_units_and_apartment_numbers():
    """Verify apartment numbers, floors, and unit tags are stripped to prevent PII leaks."""
    test_cases = [
        ("1000 Block of St. Nicholas Ave Apt 4B", "1000 Block of St. Nicholas Ave"),
        ("1000 St. Nicholas Ave, Unit 12", "1000 St. Nicholas Ave"),
        ("450 Example Way #3A", "450 Example Way"),
        ("1200 Grand Concourse, Floor 4", "1200 Grand Concourse"),
        ("2900 Frederick Douglass Blvd Ste 101", "2900 Frederick Douglass Blvd"),
    ]
    for raw, expected in test_cases:
        assert clean_address_strip_units(raw) == expected


def test_resolve_building_location_generates_google_maps_urls():
    """Verify building location resolver produces coordinates and Google Maps links."""
    res = resolve_building_location("1000 Block of St. Nicholas Ave Apt 2C", metro_area="New York")
    assert res["building_address"] == "1000 Block of St. Nicholas Ave"
    assert "google.com/maps" in res["google_maps_url"]
    assert "output=embed" in res["google_maps_embed_url"]
    assert "map_action=pano" in res["google_street_view_url"]
    assert res["latitude"] > 40.0
    assert res["longitude"] < -70.0
    assert len(str(res["census_tract_geoid"])) == 11
