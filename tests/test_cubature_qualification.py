"""Independent reader structural controls; actual owner exports tested in PSDE."""

import ast
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.pirc25.cubature_qualification import policy_values, validate_cubature_qualification
from scripts.pirc25.analytic_qualification import fingerprint
from scripts.pirc25.validate_cubature import validate


def inputs():
    model = {"schema_version": "frozen-affine-dynamics-v1", "family": "affine-oracle", "frozen": True,
        "qualification": {"scope": "oracle-fixture", "scientific_qualification": False}}
    request = {"model_package_hash": fingerprint(model), "steps": 4, "functional": "endpoint-x", "arm_id": "cubature-original"}
    cell = {"plugin_id": "affine-cubature", "arm_id": request["arm_id"], "frozen_dynamics": model,
        "propagation_request": request, "execution": {"config": {"method": "cubature", "work_steps": 32}}}
    spec = {"code_hash": "1"*64}
    policy = {"schema_version": "affine-cubature-qualification-policy-v1", "request_hash": fingerprint(request),
        "model_package_hash": fingerprint(model), "code_hash": spec["code_hash"],
        "maximum_reference_width": 1e-8, "maximum_functional_roundoff": 1e-8, "maximum_time_bias": .5,
        "maximum_scaled_transition_norm": 100., "state_scales": [10., 10., 1., 1.],
        "maximum_operations": 400001, "maximum_job_seconds": 60.}
    return policy, spec, cell


def test_cubature_policy_keeps_a_separate_method_and_finite_caps():
    policy, spec, cell = inputs()
    before = deepcopy((policy, spec, cell))
    assert policy_values(policy, spec, cell) == cell["propagation_request"]
    assert (policy, spec, cell) == before


@pytest.mark.parametrize("field,value", [("schema_version", "affine-analytic-qualification-policy-v1"),
    ("request_hash", "0"*64), ("model_package_hash", "0"*64), ("code_hash", "0"*64),
    ("maximum_reference_width", 0), ("maximum_job_seconds", 1801),
    ("maximum_operations", 400002), ("maximum_operations", True), ("state_scales", [1, 1])])
def test_policy_cannot_inherit_analytic_bindings_or_exceed_caps(field, value):
    policy, spec, cell = inputs()
    policy[field] = value
    with pytest.raises(ValueError, match="cubature"):
        policy_values(policy, spec, cell)


@pytest.mark.parametrize("target", ["nonlinear", "analytic", "wrong-work", "wrong-arm"])
def test_declared_nonlinear_or_other_method_never_inherits_affine_closure(target):
    policy, spec, cell = inputs()
    if target == "nonlinear":
        cell["frozen_dynamics"]["family"] = "synthetic-tanh"
    elif target == "analytic":
        cell["plugin_id"] = "affine-propagation"
    elif target == "wrong-work":
        cell["execution"]["config"]["work_steps"] = 1
    else:
        cell["arm_id"] = "renamed-budget"
    with pytest.raises(ValueError, match="cubature"):
        policy_values(policy, spec, cell)


@pytest.mark.parametrize("expected", [None, "", "0"*64, "f"*63, "g"*64])
def test_expected_transport_hash_cannot_be_inferred(expected):
    with pytest.raises(ValueError, match="trusted expected bundle hash"):
        validate({"bundle_hash": "f"*64}, expected)


@pytest.mark.parametrize("receipt", [{}, {"spec": {}, "cell": {}, "documents": {}}, None])
def test_missing_own_source_proof_is_an_explicit_cubature_failure(receipt):
    with pytest.raises(ValueError, match="cubature"):
        validate_cubature_qualification(receipt, {})


def test_reader_never_imports_runtime_provider_or_numeric_kernels():
    path = Path(__file__).resolve().parents[1]/"scripts/pirc25/cubature_qualification.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    imports.update(alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
    assert imports <= {"fractions", "analytic_qualification"}
