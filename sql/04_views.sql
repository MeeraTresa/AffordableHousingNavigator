CREATE OR REPLACE VIEW `a4i_housing.v_tract_context` AS
WITH annual_filings AS (
  SELECT census_tract_geoid,
         SUM(nonpayment_filings_count)              AS annual_nonpayment_filings,
         SUM(holdover_or_no_fault_filings_count)    AS annual_holdover_filings,
         SUM(default_judgments_count)               AS annual_default_judgments,
         ROUND(AVG(median_claimed_arrears_usd), 0)  AS avg_claimed_arrears_usd,
         COUNT(*)                                   AS quarters_aggregated   -- must be 4
  FROM `a4i_housing.court_eviction_filings`
  GROUP BY census_tract_geoid
),
open_res AS (
  SELECT census_tract_geoid, COUNT(*) AS open_residential_311
  FROM `a4i_housing.municipal_311_housing_complaints`
  WHERE property_type = 'Residential' AND closed_date IS NULL
    AND request_id NOT LIKE 'DECOY-%'
  GROUP BY census_tract_geoid
)
SELECT
  a.census_tract_geoid,                        -- STRING, 11 chars. Never cast.
  a.county_name,
  a.renter_occupied_units,
  a.median_household_income,
  a.median_gross_rent,
  ROUND(SAFE_DIVIDE(a.renter_hh_rent_50_pct_plus_count, a.renter_occupied_units) * 100, 1) AS severe_rent_burden_pct,
  ROUND(SAFE_DIVIDE(a.renter_hh_rent_30_to_49_pct_count, a.renter_occupied_units) * 100, 1) AS rent_burden_30_49_pct,
  ROUND(a.poverty_rate * 100, 1)    AS poverty_pct,
  ROUND(a.no_vehicle_rate * 100, 1) AS no_vehicle_pct,
  COALESCE(f.annual_nonpayment_filings, 0) AS annual_nonpayment_filings_modeled,
  COALESCE(f.annual_holdover_filings, 0)   AS annual_holdover_filings_modeled,
  COALESCE(f.annual_default_judgments, 0)  AS annual_default_judgments_modeled,
  f.avg_claimed_arrears_usd                AS avg_claimed_arrears_usd_modeled,
  f.quarters_aggregated,
  COALESCE(o.open_residential_311, 0)      AS open_residential_311
  -- NOTE: audit_* columns intentionally NOT exposed in this view.
FROM `a4i_housing.acs_tract_housing_tenure` a
LEFT JOIN annual_filings f USING (census_tract_geoid)
LEFT JOIN open_res o USING (census_tract_geoid);

CREATE OR REPLACE VIEW `a4i_housing.v_metro_baseline` AS
SELECT
  ROUND(SAFE_DIVIDE(SUM(a.renter_hh_rent_50_pct_plus_count), SUM(a.renter_occupied_units)) * 100, 1) AS metro_severe_rent_burden_pct,
  APPROX_QUANTILES(t.annual_nonpayment_filings_modeled, 2)[OFFSET(1)] AS median_tract_nonpayment_filings_modeled,
  COUNT(*) AS tracts
FROM `a4i_housing.acs_tract_housing_tenure` a
JOIN `a4i_housing.v_tract_context` t USING (census_tract_geoid);
