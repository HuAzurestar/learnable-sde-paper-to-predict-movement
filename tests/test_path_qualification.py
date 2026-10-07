"""Offline quotas and dispatch guards; real owner exports run in paired CI."""

import ast
from pathlib import Path

import pytest

from scripts.pirc25.path_qualification import validate_path_qualification
from scripts.pirc25.validate_paths import validate
from scripts.pirc25.aggregate import aggregate, csv_bytes
from scripts.pirc25.output_eligibility import comparison_eligible, path_output_status
from test_shared_evidence import bundle, seal
from test_shared_adjudication import evidence, compare
import csv
import io
import json


@pytest.mark.parametrize("expected", [None, "", "f"*63, "x"*64, "0"*64])
def test_separately_trusted_transport_hash_is_required(expected):
    with pytest.raises(ValueError, match="trusted expected bundle hash"):
        validate({"bundle_hash": "f"*64}, expected)


@pytest.mark.parametrize("receipt", [{}, {"documents": {}}, {"documents": {"propagation_qualification": {}}},
    {"documents": {"propagation_qualification": {"status": "PASSED"}}}])
def test_plain_pass_flag_or_missing_owner_numeric_proof_is_refused(receipt):
    with pytest.raises(ValueError):
        validate_path_qualification(receipt, {})


def test_reader_imports_only_stdlib_and_saved_evidence_helpers():
    path = Path(__file__).resolve().parents[1]/"scripts/pirc25/path_qualification.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    imports.update(a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names)
    assert imports <= {"fractions", "math", "analytic_qualification"}
    calls = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert not calls & {"validate_analytic_qualification", "monte_carlo", "importance_sampling", "bound_affine_reference"}


@pytest.mark.parametrize("value", [float("nan"), float("inf"), 1 << 4097, [0]*100001],
    ids=["nan", "inf", "integer", "nodes"])
def test_untrusted_direct_call_quota_precedes_hashing(value):
    with pytest.raises(ValueError):
        validate_path_qualification({"bad": value}, {})


def test_cyclic_direct_call_fails_before_recursion_or_copying():
    receipt = {}
    receipt["cycle"] = receipt
    with pytest.raises(ValueError, match="structural quota"):
        validate_path_qualification(receipt, {})


@pytest.mark.parametrize("status", ["FAILED", None, "UNKNOWN", [], True])
def test_nonpassed_current_target_is_not_a_complete_comparison_block(status):
    value = bundle()
    value["cells"][0]["result"] = {"forecast": {"path_output_analysis": {}, "current_output_qualification": status}}
    result = aggregate(seal(value))
    assert result["expected_cell_count"] == result["successful_cell_count"] == 8
    assert result["comparison_eligible_cell_count"] == 7
    arm = result["arms"][0]
    assert arm["expected_cells"] == arm["successful_cells"] == 4
    assert arm["comparison_eligible_cells"] == 3 and arm["independent_n"] == 1
    assert arm["status_rates"]["denominator"] == 4 and arm["status_rates"]["values"] == {"SUCCEEDED": 1.}
    assert result["comparisons"][0]["independent_n"] == 1
    rows = list(csv.DictReader(io.StringIO(csv_bytes(result).decode())))
    baseline = [row for row in rows if row["arm_id"] == "baseline"][0]
    assert baseline["expected_cells"] == baseline["successful_cells"] == "4"
    assert baseline["comparison_eligible_cells"] == "3"
    assert json.loads(baseline["path_output_dispositions"]) == arm["path_output_dispositions"]


def test_numeric_failure_cannot_enter_paired_adjudication_or_trigger_expansion():
    value = evidence()
    value["cells"][0]["result"] = {"forecast": {"path_output_analysis": {}, "current_output_qualification": "FAILED"}}
    record = compare(seal(value))["records"][0]
    assert record["verdict"] == "INSUFFICIENT_DATA" and record["interval"] is None
    assert record["independent_n"] == 1 and record["stop_expansion"] is True
    assert record["cell_counts"]["expected"] == record["cell_counts"]["successful"] == 8
    assert record["cell_counts"]["comparison_eligible"] == 7
    assert record["cell_counts"]["path_output_dispositions"] == {"FAILED": 1}
    assert record["status_rates"]["denominator"] == 8


@pytest.mark.parametrize("row", [
    {"status": "MISSING", "registered_cell": {"plugin_id": "affine-path-production-chunk"}, "result": None},
    {"status": "SUCCEEDED", "admission": {"cell": {"plugin_id": "affine-path-production-chunk"}}},
    {"status": "SUCCEEDED", "result": {"forecast": {"path_output_analysis": {}}}},
])
def test_missing_classification_or_removed_registered_cell_has_no_eligibility_fallback(row):
    assert path_output_status(row) == "UNRESOLVED" and not comparison_eligible(row)
