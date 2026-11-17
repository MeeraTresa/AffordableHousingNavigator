-- Section 12.2 Batch Equity Audit
-- Evaluates whether requiring an open 311 record penalizes high-burden "silent distress" tracts.
-- Only permitted in sql/05_equity_audit.sql, scripts/run_equity_audit.py, and agent/navigator/equity.py.

WITH t AS (SELECT * FROM `a4i_housing.v_tract_context`),
policy AS (
  SELECT census_tract_geoid,
         open_residential_311 > 0 AS prioritized_by_311_rule,
         (open_residential_311 <= 1
          AND severe_rent_burden_pct >= (SELECT metro_severe_rent_burden_pct FROM `a4i_housing.v_metro_baseline`)
          AND annual_nonpayment_filings_modeled >= (SELECT median_tract_nonpayment_filings_modeled FROM `a4i_housing.v_metro_baseline`)
         ) AS silent_distress
  FROM t
)
SELECT
  CASE WHEN p.prioritized_by_311_rule THEN 'A. Prioritized by open-311 rule'
       WHEN p.silent_distress THEN 'B. Silent distress (missed by 311 rule)'
       ELSE 'C. Other tracts' END AS grp,
  COUNT(*) AS tracts,
  SUM(a.renter_hh_rent_50_pct_plus_count) AS severely_burdened_households,
  ROUND(AVG(a.no_vehicle_rate) * 100, 1)        AS no_vehicle_pct,
  ROUND(AVG(a.audit_black_share) * 100, 1)      AS black_pct,
  ROUND(AVG(a.audit_hispanic_share) * 100, 1)   AS hispanic_pct,
  ROUND(AVG(a.audit_asian_share) * 100, 1)      AS asian_pct,
  ROUND(AVG(a.audit_white_share) * 100, 1)      AS white_pct
FROM policy p JOIN `a4i_housing.acs_tract_housing_tenure` a USING (census_tract_geoid)
GROUP BY grp ORDER BY grp;
