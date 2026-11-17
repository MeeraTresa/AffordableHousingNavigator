from google.cloud import bigquery
from .config import PROJECT, BQ_LOCATION

_client = bigquery.Client(project=PROJECT, location=BQ_LOCATION)

def run_query(sql: str, params: list | None = None) -> list[dict]:
    job = _client.query(sql, job_config=bigquery.QueryJobConfig(query_parameters=params or []))
    return [dict(r) for r in job.result()]
