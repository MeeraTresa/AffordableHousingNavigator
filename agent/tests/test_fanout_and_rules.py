from agent.navigator.bq import run_query
import inspect
from agent.navigator import prompts, config, equity
from agent.navigator.tools import case_file, evidence, statutes, funds, brief

def test_fanout_and_tract_count():
    rows = run_query("SELECT COUNT(*) as n, COUNTIF(quarters_aggregated != 4) as bad_quarters FROM `a4i_housing.v_tract_context`")
    assert rows[0]["n"] == 168, f"Expected 168 tracts, got {rows[0]['n']}"
    assert rows[0]["bad_quarters"] == 0, f"Found unaggregated quarters: {rows[0]['bad_quarters']}"
    print("test_fanout_and_tract_count PASSED (168 tracts, all 4 quarters aggregated)!")

def test_no_audit_leak():
    # Hard rule 4: audit_* columns never in prompts, config, or user tools
    for mod in [prompts, config, case_file, evidence, statutes, funds, brief]:
        src = inspect.getsource(mod)
        assert "audit_" not in src, f"Found audit_ leak in {mod.__name__}"
    print("test_no_audit_leak PASSED (audit_* isolated to equity.py and sql/05)!")

if __name__ == "__main__":
    test_fanout_and_tract_count()
    test_no_audit_leak()
