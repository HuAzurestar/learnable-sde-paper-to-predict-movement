"""Offline saved-proof controls; no numeric calibration or data permission."""

import ast
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.pirc25.probability_calibration import (
    policy_values, validate_saved_calibration, validate_calibrated_admission,
    summarize_calibration_sources,
)


def inputs():
    model = {"schema_version": "frozen-affine-dynamics-v1", "family": "affine-oracle",
        "frozen": True, "qualification": {"scope": "oracle-fixture", "scientific_qualification": False}}
    from scripts.pirc25.analytic_qualification import fingerprint
    request = {"model_package_hash": fingerprint(model), "functional": "endpoint-halfspace",
        "normal": [1., 0., 0., 0.], "threshold": 0., "horizons": [1.]}
    policy = {"schema_version": "affine-halfspace-calibration-policy-v1",
        "source_request_hash": fingerprint(request), "model_package_hash": fingerprint(model),
        "code_hash": "1"*64, "target_probability": 1e-6,
        "maximum_relative_probability_error": .01, "maximum_relative_probability_width": .01,
        "maximum_operations": 200000, "maximum_job_seconds": 60.}
    return policy, model, request


def test_calibration_policy_keeps_its_original_caps_and_scope():
    policy, model, request = inputs()
    before = deepcopy((policy, model, request))
    policy_values(policy, model, request, policy["code_hash"])
    assert (policy, model, request) == before


@pytest.mark.parametrize("field,value", [("target_probability", True), ("target_probability", 1e-9),
    ("maximum_operations", True), ("maximum_operations", 200001), ("maximum_job_seconds", 1801),
    ("maximum_relative_probability_error", 2), ("maximum_relative_probability_width", 0),
    ("schema_version", "affine-analytic-qualification-policy-v1"), ("code_hash", "2"*64)])
def test_calibration_policy_cannot_be_coerced_or_expanded(field, value):
    policy, model, request = inputs()
    policy[field] = value
    with pytest.raises(ValueError, match="calibration"):
        policy_values(policy, model, request, "1"*64)


@pytest.mark.parametrize("proof", [{}, None, {"scientific_qualification": 0}])
def test_missing_or_opaque_proof_never_inherits_generic_admission(proof):
    with pytest.raises(ValueError, match="calibration"):
        validate_saved_calibration(proof, {}, consumer_study_id="consumer")


def test_legacy_admission_has_no_implicit_calibration():
    receipt = {"spec": {}, "cell": {}, "documents": {}}
    assert validate_calibrated_admission(receipt, {}) is None
    receipt["documents"]["probability_calibration"] = {}
    with pytest.raises(ValueError, match="calibration"):
        validate_calibrated_admission(receipt, {})


def test_zero_sources_are_unavailable_not_free():
    result = summarize_calibration_sources([])
    assert result["charged_ms"] is None and result["unique_sources"] == 0
    assert "independent_n" not in result


def test_saved_reader_has_no_runtime_provider_or_free_reference_imports():
    path = Path(__file__).resolve().parents[1]/"scripts/pirc25/probability_calibration.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    imports.update(alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
    assert imports <= {"fractions", "math", "analytic_qualification"}
    forbidden = {"sqrt", "exp", "cdf", "calibrate_affine_halfspace", "inverse_cdf"}
    assert not any(isinstance(n, ast.Call) and (
        isinstance(n.func, ast.Name) and n.func.id in forbidden or
        isinstance(n.func, ast.Attribute) and n.func.attr in forbidden) for n in ast.walk(tree))
