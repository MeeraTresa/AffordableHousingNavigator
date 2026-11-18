"""Semantic search over municipal 311 housing complaints with decoy post-filtering."""

from typing import Tuple, List, Optional
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from . import decoy_filter
from .case_intake import CorroboratedEvidence, ExcludedNearMatch
from .. import data_loader, config


def _search_local_tfidf(
    query: str,
    df: pd.DataFrame,
    top_k: int = 20,
) -> pd.DataFrame:
    """Run exact brute-force semantic similarity over complaint narratives using TF-IDF."""
    if df.empty:
        return df

    corpus = (df["raw_complaint_type"].fillna("") + " " + df["complaint_narrative"].fillna("")).tolist()
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        stop_words="english",
        sublinear_tf=True,
    )
    tfidf_matrix = vectorizer.fit_transform(corpus)
    query_vec = vectorizer.transform([query])
    scores = cosine_similarity(query_vec, tfidf_matrix).flatten()

    df_out = df.copy()
    df_out["similarity_score"] = scores
    # Sort descending by similarity
    df_out = df_out.sort_values(by="similarity_score", ascending=False).head(top_k)
    return df_out


def _search_bigquery(
    query: str,
    metro_area: str,
    top_k: int = 20,
) -> pd.DataFrame:
    """Execute BigQuery VECTOR_SEARCH with AI.EMBED over embedded complaints."""
    from google.cloud import bigquery

    client = bigquery.Client(project=config.GOOGLE_CLOUD_PROJECT)
    sql = f"""
    SELECT
      base.request_id,
      base.state_code,
      base.metro_area,
      base.jurisdiction,
      base.block_address,
      base.census_tract_geoid,
      base.agency_code,
      base.property_type,
      base.raw_complaint_type,
      base.complaint_narrative,
      base.inspection_status,
      base.created_date,
      base.closed_date,
      base.data_provenance,
      ROUND(1.0 - distance, 4) AS similarity_score
    FROM VECTOR_SEARCH(
      TABLE `{config.BIGQUERY_DATASET}.complaints_embedded`,
      'embedding',
      (
        SELECT AI.EMBED(
          @query_text,
          connection_id => '{config.VERTEX_CONNECTION_ID}',
          endpoint => '{config.EMBEDDING_ENDPOINT}'
        ).result AS query_vec
      ),
      query_column_to_search => 'query_vec',
      top_k => @top_k,
      options => '{{"use_brute_force":true}}'
    )
    WHERE base.metro_area = @metro_area
    ORDER BY distance ASC;
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("query_text", "STRING", query),
            bigquery.ScalarQueryParameter("metro_area", "STRING", metro_area),
            bigquery.ScalarQueryParameter("top_k", "INT64", top_k),
        ]
    )
    return client.query(sql, job_config=job_config).to_dataframe()


def search_habitability_evidence(
    query: str,
    metro_area: str = "New York",
    tenant_block: str = "",
    top_k: int = 20,
) -> Tuple[List[CorroboratedEvidence], List[ExcludedNearMatch]]:
    """Run vector search over 311 complaint narratives, followed by relational decoy filtering."""
    if config.USE_BIGQUERY and config.GOOGLE_CLOUD_PROJECT:
        try:
            candidates_df = _search_bigquery(query, metro_area, top_k=top_k)
        except Exception:
            # Fall back gracefully to local parquet
            df = data_loader.get_311_complaints(metro_area)
            candidates_df = _search_local_tfidf(query, df, top_k=top_k)
    else:
        df = data_loader.get_311_complaints(metro_area)
        candidates_df = _search_local_tfidf(query, df, top_k=top_k)

    return decoy_filter.filter_candidates(candidates_df, tenant_block=tenant_block)
