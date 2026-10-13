"""Offline bounded-reader controls; actual positive owner chains run in paired CI."""

import ast
from pathlib import Path

import pytest

from scripts.pirc25.analytic_qualification import bounded, interval
from scripts.pirc25.mixture_qualification import validate_mixture_qualification
from scripts.pirc25.validate_mixture import validate


@pytest.mark.parametrize("expected", [None, "", "f"*63, "x"*64, "0"*64])
def test_separately_trusted_expected_hash_required(expected):
    with pytest.raises(ValueError, match="trusted expected bundle hash"):
        validate({"bundle_hash": "f"*64}, expected)


@pytest.mark.parametrize("document", [{}, {"documents": {}}, {"documents": {"propagation_qualification": {}}},
    {"documents": {"propagation_qualification": {"status": "PASSED", "scientific_qualification": True}}}])
def test_missing_numeric_proof_or_plain_pass_flag_refused(document):
    with pytest.raises(ValueError):
        validate_mixture_qualification(document, {})


def test_only_stdlib_and_low_level_saved_evidence_helpers_imported():
    path = Path(__file__).resolve().parents[1]/"scripts/pirc25/mixture_qualification.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    imported.update(a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names)
    assert imported <= {"fractions", "analytic_qualification"}
    names = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "validate_analytic_qualification" not in names


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -(float("inf")), 1 << 4097,
    "x"*65537, {"x"*129: 0}, [0]*100001], ids=["nan", "inf", "negative-inf", "integer", "string", "key", "nodes"])
def test_structural_and_finite_quotas_before_hashing(value):
    with pytest.raises(ValueError):
        bounded({"value": value}, 2*1024*1024)


def test_cyclic_direct_call_refused_without_recursion_failure():
    receipt = {}
    receipt["cycle"] = receipt
    with pytest.raises(ValueError, match="structural quota"):
        validate_mixture_qualification(receipt, {})


@pytest.mark.parametrize("bounds", [[["01", "2"], ["1", "1"]], [["2", "4"], ["1", "1"]],
    [["1", "3"], ["1", "1"]], [["1", "0"], ["1", "1"]], [["2", "1"], ["1", "1"]],
    [["1", "2"], ["1", "0"]], [[1, "2"], ["1", "1"]]])
def test_noncanonical_dyadic_or_unordered_saved_interval_refused(bounds):
    with pytest.raises(ValueError):
        interval(bounds)
