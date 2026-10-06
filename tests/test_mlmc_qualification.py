"""Offline MLMC reader gates/quotas; actual chain controls live in paired CI."""

import ast
from copy import deepcopy
import math
from pathlib import Path

import pytest

from scripts.pirc25.mlmc_qualification import sampling, validate_mlmc_qualification
from scripts.pirc25.validate_mlmc import validate


@pytest.mark.parametrize("expected", [None, "", "f"*63, "x"*64, "0"*64])
def test_expected_authorized_hash_is_required(expected):
    with pytest.raises(ValueError, match="trusted expected bundle hash"):
        validate({"bundle_hash": "f"*64}, expected)


@pytest.mark.parametrize("document", [{}, {"documents": {}}, {"documents": {"propagation_qualification": {}}}])
def test_missing_numeric_receipt_never_falls_back_to_operator_pass(document):
    with pytest.raises(ValueError):
        validate_mlmc_qualification(document, {})


def test_reader_imports_only_standard_library_or_own_saved_evidence_helpers():
    path = Path(__file__).resolve().parents[1]/"scripts/pirc25/mlmc_qualification.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    imported.update(a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names)
    assert imported <= {"fractions", "math", "analytic_qualification"}


def payload():
    from scripts.pirc25.analytic_qualification import fingerprint
    request = {"functional": "endpoint-x"}
    se = math.sqrt(3.)
    f = {"request_hash": fingerprint(request), "kind": "functional_estimate", "estimator_id": "coupled-euler-mlmc-v1",
        "sample_count": 6, "estimate": 3., "standard_error": se,
        "interval": [3.-1.959963984540054*se, 3.+1.959963984540054*se],
        "interval_kind": "independent-level-normal-approximation-95", "status": "SUCCEEDED",
        "diagnostics": [["level_samples", [2, 2, 2]], ["level_means", [1., 1., 1.]], ["level_variances", [2., 2., 2.]],
            ["coupling", "coarse-increment=sum(two-fine-increments)"]]}
    return f, request


def test_independent_reader_recomputes_signed_mean_and_approximate_interval():
    f, request = payload()
    assert sampling(f, request, [2, 2, 2])["level_variances"] == [2., 2., 2.]


@pytest.mark.parametrize("fault", ["scalar", "se", "interval", "kind", "normal-as-exact", "variance", "duplicate"])
def test_forged_current_sampling_identity_or_statistics_refused(fault):
    f, request = payload()
    if fault in {"scalar", "se", "interval", "kind", "normal-as-exact"}:
        key = {"scalar": "estimate", "se": "standard_error", "interval": "interval", "kind": "kind", "normal-as-exact": "interval_kind"}[fault]
        f[key] = {"scalar": 0., "se": 0., "interval": [0, 0], "kind": "analytic", "normal-as-exact": "exact-95"}[fault]
    elif fault == "variance":
        f["diagnostics"][2][1][0] = -1
    else:
        f["diagnostics"].append(deepcopy(f["diagnostics"][0]))
    with pytest.raises(ValueError):
        sampling(f, request, [2, 2, 2])
