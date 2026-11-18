CREATE OR REPLACE TABLE `a4i_housing.complaints_embedded` AS
SELECT
  request_id, metro_area, jurisdiction, census_tract_geoid, block_address,
  agency_code, property_type, raw_complaint_type, inspection_status,
  created_date, closed_date, latitude, longitude, data_provenance,
  complaint_narrative,
  embedded.result AS embedding
FROM (
  SELECT *,
    AI.EMBED(complaint_narrative,
             connection_id => 'us.a4i-vertex',
             endpoint => 'gemini-embedding-2') AS embedded
  FROM `a4i_housing.municipal_311_housing_complaints`
)
WHERE embedded.status = '';

-- Sanity: expect 174 (165 real + 9 decoys)
SELECT COUNT(*) AS n, COUNTIF(request_id LIKE 'DECOY-%') AS decoys
FROM `a4i_housing.complaints_embedded`;
