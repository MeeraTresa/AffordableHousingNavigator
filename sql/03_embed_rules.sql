CREATE OR REPLACE TABLE `a4i_housing.statutes_embedded` AS
SELECT s.* EXCEPT(embedded), embedded.result AS embedding
FROM (
  SELECT *, AI.EMBED(CONCAT(ordinance_title, '. ', raw_statute_text),
                     connection_id => 'us.a4i-vertex',
                     endpoint => 'gemini-embedding-2') AS embedded
  FROM `a4i_housing.municipal_housing_ordinance_statutes`
) AS s
WHERE embedded.status = '';

CREATE OR REPLACE TABLE `a4i_housing.bulletins_embedded` AS
SELECT b.* EXCEPT(embedded), embedded.result AS embedding
FROM (
  SELECT *, AI.EMBED(CONCAT(program_name, '. ', raw_bulletin_text),
                     connection_id => 'us.a4i-vertex',
                     endpoint => 'gemini-embedding-2') AS embedded
  FROM `a4i_housing.rental_relief_program_bulletins`
) AS b
WHERE embedded.status = '';

SELECT 'statutes' AS tbl, COUNT(*) AS n FROM `a4i_housing.statutes_embedded`
UNION ALL
SELECT 'bulletins' AS tbl, COUNT(*) AS n FROM `a4i_housing.bulletins_embedded`;
