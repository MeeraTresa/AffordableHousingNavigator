CREATE OR REPLACE TABLE `a4i_housing.statutes_embedded` AS
SELECT s.* EXCEPT(embedded), embedded.result AS embedding
FROM (
  SELECT *, AI.EMBED(CONCAT(ordinance_title, '. ', raw_statute_text),
                     connection_id => 'us.a4i-vertex',
                     endpoint => 'gemini-embedding-2') AS embedded
  FROM `a4i_housing.municipal_housing_ordinance_statutes`
) AS s
WHERE embedded.status = '';

SELECT COUNT(*) AS statutes_count FROM `a4i_housing.statutes_embedded`;

CREATE OR REPLACE TABLE `a4i_housing.bulletins_embedded` AS
SELECT b.* EXCEPT(embedded), embedded.result AS embedding
FROM (
  SELECT *, AI.EMBED(CONCAT(program_name, '. ', raw_bulletin_text),
                     connection_id => 'us.a4i-vertex',
                     endpoint => 'gemini-embedding-2') AS embedded
  FROM `a4i_housing.rental_relief_program_bulletins`
) AS b
WHERE embedded.status = '';

SELECT COUNT(*) AS bulletins_count FROM `a4i_housing.bulletins_embedded`;
