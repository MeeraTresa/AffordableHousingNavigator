import os
import pathlib
import pytest
from google.cloud import bigquery
from agent.navigator.config import PROJECT, DATASET

def test_v_tract_context_has_no_audit_columns():
    """Rule 3: audit_* demographic columns must NEVER be exposed in v_tract_context."""
    client = bigquery.Client(project=PROJECT)
    cols = list(client.query(f"""
        SELECT column_name
        FROM `{PROJECT}.{DATASET}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = 'v_tract_context'
    """).result())
    col_names = [r["column_name"] for r in cols]
    audit_cols = [c for c in col_names if c.startswith("audit_")]
    assert len(audit_cols) == 0, f"Found leaked audit_* columns in v_tract_context: {audit_cols}"

def test_codebase_audit_isolation():
    """Rule 3: audit_* columns strictly restricted to equity.py (and sql/scripts)."""
    agent_dir = pathlib.Path(__file__).resolve().parent.parent
    leaks = []
    for py_file in agent_dir.rglob("*.py"):
        if py_file.name == "equity.py" or "tests" in str(py_file):
            continue
        content = py_file.read_text(encoding="utf-8")
        if "audit_" in content:
            leaks.append(str(py_file.relative_to(agent_dir)))
    assert len(leaks) == 0, f"audit_ string found outside equity.py: {leaks}"
