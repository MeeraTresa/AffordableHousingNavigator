"""Building and 100-block spatial resolver integrating Google Maps without PII."""

import re
import urllib.parse
from typing import Dict, Any, Optional, Tuple
import pandas as pd
from .. import data_loader


def clean_address_strip_units(raw_address: str) -> str:
    """Strip apartment numbers, units, and floor designations to preserve tenant privacy and prevent PII leaks."""
    text = raw_address.strip()
    # Strip unit/apt/floor patterns like 'Apt 4B', 'Unit 12', '#3A', 'Fl 2', 'Suite 100'
    text = re.sub(r'(?i)(?:\b(apt|apartment|unit|suite|ste|fl|floor|rm|room)\b|#)\s*[\w\d-]+', '', text)
    # Remove dangling commas or hash signs
    text = re.sub(r'[,#\s]+$', '', text).strip()
    return text


def resolve_building_location(
    raw_address: str,
    metro_area: str = "New York",
    census_tract_geoid: Optional[str] = None,
) -> Dict[str, Any]:
    """Identify building/block centroid and generate Google Maps embed and navigation links."""
    clean_addr = clean_address_strip_units(raw_address)

    # City/State suffixes for Google Maps search
    metro_suffixes = {
        "New York": "New York, NY",
        "San Francisco": "San Francisco, CA",
        "Chicago": "Chicago, IL",
        "Austin": "Austin, TX",
        "Baton Rouge": "Baton Rouge, LA",
        "Cincinnati": "Cincinnati, OH",
    }
    city_suffix = metro_suffixes.get(metro_area, metro_area)

    # Check if city already in address, if not append it
    search_query = clean_addr
    if not any(k in clean_addr.lower() for k in ["new york", "san francisco", "chicago", "austin", "baton rouge", "cincinnati"]):
        search_query = f"{clean_addr}, {city_suffix}"

    # Default coordinates from tract tenure
    tracts_df = data_loader.get_tract_tenure(metro_area)
    lat: Optional[float] = None
    lon: Optional[float] = None
    matched_geoid = census_tract_geoid

    # 1. Try matching against 311 complaints on block address
    complaints_df = data_loader.get_311_complaints(metro_area)
    block_needle = clean_addr.lower().replace("block of", "").replace("block", "").strip()
    matches = complaints_df[complaints_df["block_address"].str.lower().str.contains(block_needle[:10], na=False)]
    if not matches.empty:
        row = matches.iloc[0]
        if pd.notna(row.get("latitude")) and pd.notna(row.get("longitude")):
            lat = float(row["latitude"])
            lon = float(row["longitude"])
        if not matched_geoid and pd.notna(row.get("census_tract_geoid")):
            matched_geoid = str(row["census_tract_geoid"]).zfill(11)

    # 2. Try matching tract coordinates if geoid provided or resolved
    if matched_geoid and (lat is None or lon is None):
        t_matches = tracts_df[tracts_df["census_tract_geoid"].astype(str) == str(matched_geoid).zfill(11)]
        if not t_matches.empty:
            t_row = t_matches.iloc[0]
            lat = float(t_row["latitude"])
            lon = float(t_row["longitude"])

    # 3. Fallback to Washington Heights tract 36061024500 if NY, or first tract
    if lat is None or lon is None:
        if metro_area == "New York":
            t_matches = tracts_df[tracts_df["census_tract_geoid"].astype(str) == "36061024500"]
            t_row = t_matches.iloc[0] if not t_matches.empty else tracts_df.iloc[0]
        else:
            t_row = tracts_df.iloc[0]
        lat = float(t_row["latitude"])
        lon = float(t_row["longitude"])
        if not matched_geoid:
            matched_geoid = str(t_row["census_tract_geoid"]).zfill(11)

    encoded_query = urllib.parse.quote(search_query)

    # Generate Google Maps URLs
    google_maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_query}"
    google_maps_embed_url = f"https://www.google.com/maps?q={encoded_query}&output=embed"
    google_street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}"

    return {
        "building_address": clean_addr,
        "full_search_address": search_query,
        "census_tract_geoid": matched_geoid,
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "google_maps_url": google_maps_url,
        "google_maps_embed_url": google_maps_embed_url,
        "google_street_view_url": google_street_view_url,
    }
