-- Validation queries equivalent to notebook Section 12 for New York (state FIPS 36)

-- 1. Tenure stats
SELECT
    COUNT(*) AS n,
    COUNT(DISTINCT census_tract_geoid) AS n_distinct,
    COUNTIF(LENGTH(census_tract_geoid) != 11) AS bad_geoid_len,
    COUNTIF(SUBSTR(census_tract_geoid, 1, 2) != '36') AS bad_fips_prefix,
    COUNTIF(metro_area != 'New York') AS wrong_metro,
    COUNTIF(renter_occupied_units <= 0) AS nonpos_renters,
    COUNTIF(renter_hh_rent_50_pct_plus_count > renter_occupied_units) AS impossible_burden,
    COUNTIF(
        audit_black_share < 0 OR audit_black_share > 1
        OR audit_hispanic_share < 0 OR audit_hispanic_share > 1
        OR audit_asian_share < 0 OR audit_asian_share > 1
        OR audit_indigenous_share < 0 OR audit_indigenous_share > 1
        OR audit_white_share < 0 OR audit_white_share > 1
    ) AS bad_audit_bounds
FROM `a4i_housing.acs_tract_housing_tenure`;

-- 2. Filings stats
SELECT
    COUNT(*) AS n,
    COUNT(DISTINCT filing_record_id) AS n_distinct,
    COUNT(DISTINCT reporting_quarter) AS n_quarters,
    COUNTIF(metro_area != 'New York') AS wrong_metro,
    COUNTIF(nonpayment_filings_count < 0 OR holdover_or_no_fault_filings_count < 0) AS neg_counts,
    COUNTIF(census_tract_geoid NOT IN (
        SELECT census_tract_geoid FROM `a4i_housing.acs_tract_housing_tenure`
    )) AS orphan_tracts
FROM `a4i_housing.court_eviction_filings`;

-- 3. 311 Complaints stats
SELECT
    COUNT(*) AS n,
    COUNT(DISTINCT request_id) AS n_distinct,
    COUNTIF(metro_area != 'New York') AS wrong_metro,
    COUNTIF(LENGTH(census_tract_geoid) != 11) AS bad_geoid_len,
    COUNTIF(census_tract_geoid NOT IN (
        SELECT census_tract_geoid FROM `a4i_housing.acs_tract_housing_tenure`
    )) AS orphan_tracts,
    COUNTIF(request_id LIKE 'DECOY-%') AS n_decoys,
    COUNTIF(request_id LIKE 'DECOY-%' AND property_type = 'Commercial' AND closed_date IS NULL) AS decoy_comm_open,
    COUNTIF(request_id LIKE 'DECOY-%' AND property_type = 'Residential' AND inspection_status = 'Closed - Abated') AS decoy_res_abated,
    COUNTIF(request_id LIKE 'DECOY-%' AND property_type = 'Residential' AND inspection_status = 'Closed - No Violation') AS decoy_res_noviol,
    COUNTIF(property_type = 'Residential' AND closed_date IS NULL AND request_id NOT LIKE 'DECOY-%') AS open_real_res,
    COUNTIF(REGEXP_CONTAINS(complaint_narrative, r'(?i)\bmy\s+name\s+is\s+[A-Z][a-z]+')) AS pii_names_left,
    COUNTIF(REGEXP_CONTAINS(complaint_narrative, r'(?i)license\s+plate\s*#?\s*[A-Z0-9]{4,}')) AS pii_plates_left,
    COUNTIF(REGEXP_CONTAINS(complaint_narrative, r'(?i)\b(dwelling\s+unit|apt\.?|apartment|room)\s*[:#]?\s*\d+')) AS pii_units_left
FROM `a4i_housing.municipal_311_housing_complaints`;

-- 4. Bulletins and statutes
SELECT
    COUNT(*) AS n_bul,
    COUNTIF(requires_open_habitability_case) AS n_hab_req,
    COUNTIF(NOT requires_open_habitability_case) AS n_general,
    (SELECT COUNT(*) FROM `a4i_housing.municipal_housing_ordinance_statutes` WHERE metro_area = 'New York') AS n_stat
FROM `a4i_housing.rental_relief_program_bulletins`
WHERE metro_area = 'New York';
