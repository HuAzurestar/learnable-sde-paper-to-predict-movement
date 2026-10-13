"""Independent stdlib verification of saved affine cubature owner evidence.

No runtime import, worker, matrix/CDF replay, grant or model qualification.
The separately trusted transport hash remains mandatory at the entry point.
"""

from fractions import Fraction

if __package__:
    from .analytic_qualification import (artifact, bounded, certificate, finite,
        fingerprint, interval, outward, require, sealed, source_chain)
else:
    from analytic_qualification import (artifact, bounded, certificate, finite,
        fingerprint, interval, outward, require, sealed, source_chain)


METRIC = "absolute_error_upper_vs_declared_affine_law"
SCOPE = "declared-affine-eight-point-Euler-endpoint-functional-for-one-request"


def policy_values(policy, spec, cell):
    required = {"schema_version", "request_hash", "model_package_hash", "code_hash",
        "maximum_reference_width", "maximum_functional_roundoff", "maximum_time_bias",
        "maximum_scaled_transition_norm", "state_scales", "maximum_operations", "maximum_job_seconds"}
    require(type(policy) is dict and set(policy) == required
        and policy["schema_version"] == "affine-cubature-qualification-policy-v1", "cubature complete frozen policy")
    request, model = cell["propagation_request"], cell["frozen_dynamics"]
    require(cell["plugin_id"] == "affine-cubature" and cell["execution"]["config"]["method"] == "cubature"
        and policy["request_hash"] == fingerprint(request)
        and policy["model_package_hash"] == fingerprint(model) == request["model_package_hash"]
        and policy["code_hash"] == spec["code_hash"]
        and model["schema_version"] == "frozen-affine-dynamics-v1" and model["family"] == "affine-oracle"
        and model["frozen"] is True and model["qualification"] == {"scope": "oracle-fixture", "scientific_qualification": False},
        "cubature exact affine source/model/request identity")
    require(all(finite(policy[k], positive=True) for k in ("maximum_reference_width", "maximum_functional_roundoff",
        "maximum_time_bias", "maximum_scaled_transition_norm", "maximum_job_seconds"))
        and policy["maximum_job_seconds"] <= 1800
        and type(policy["maximum_operations"]) is int and 1 <= policy["maximum_operations"] <= 400001
        and type(policy["state_scales"]) is list and len(policy["state_scales"]) == 4
        and all(finite(v, positive=True) for v in policy["state_scales"]), "cubature finite policy caps")
    require(type(request["steps"]) is int and 1 <= request["steps"] <= 8192
        and request["functional"] in {"endpoint-x", "endpoint-halfspace"}
        and request["arm_id"] == cell["arm_id"]
        and cell["execution"]["config"]["work_steps"] == 8*request["steps"], "cubature original grid/arm/work")
    return request


def functional_values(functional, request):
    require(finite(functional["estimate"]) and functional["request_hash"] == fingerprint(request)
        and functional["estimator_id"] == "gaussian-cubature-euler-v1" and functional["kind"] == "functional_estimate"
        and type(functional["sample_count"]) is int and functional["sample_count"] == 0
        and functional["standard_error"] == 0 and functional["interval"] is None
        and functional["interval_kind"] == "deterministic-closure-no-sampling"
        and functional["status"] == "APPROXIMATION_ONLY", "cubature current estimator identity")
    pairs = functional["diagnostics"]
    require(type(pairs) is list and len(pairs) == 6
        and all(type(p) is list and len(p) == 2 and type(p[0]) is str for p in pairs), "cubature diagnostics shape")
    values = dict(pairs)
    require(len(values) == len(pairs) and type(values["point_count"]) is int and values["point_count"] == 8
        and values["point_weight"] == .125 and values["covariance_projection"] is False,
        "cubature equal-weight/no-projection diagnostics")
    mean, covariance = values["mean"], values["covariance"]
    require(type(mean) is list and len(mean) == 4 and type(covariance) is list and len(covariance) == 4
        and all(type(row) is list and len(row) == 4 for row in covariance)
        and all(finite(v) for v in [*mean, *(v for row in covariance for v in row)]), "cubature finite four-state moments")


def analysis_values(analysis, policy, request, estimate):
    bounded(analysis, 512*1024)
    sealed(analysis, "analysis_hash")
    require(analysis["schema_version"] == "affine-cubature-qualification-analysis-v1"
        and analysis["scope"] == SCOPE and analysis["scientific_qualification"] is False
        and analysis["policy_hash"] == fingerprint(policy)
        and all(analysis[k] == policy[k] for k in ("code_hash", "request_hash", "model_package_hash"))
        and type(analysis["point_count"]) is int and analysis["point_count"] == 8
        and type(analysis["point_weight"]) is float and analysis["point_weight"] == .125
        and analysis["covariance_projection"] is False
        and type(analysis["cubature_point_updates"]) is int and analysis["cubature_point_updates"] == 8*request["steps"]
        and type(analysis["output_replay_point_updates"]) is int and analysis["output_replay_point_updates"] == 8*request["steps"],
        "cubature saved analysis/eight-point work")
    cm, tm = analysis["continuous_certificate"], analysis["target_certificate"]
    cb, cn = certificate(cm, policy)
    tb, tn = certificate(tm, policy, discrete=True, request=request)
    require(analysis["continuous_certificate_hash"] == fingerprint(cm)
        and analysis["target_certificate_hash"] == fingerprint(tm)
        and analysis["target_grid"] == {"solver": "euler", "steps": request["steps"]}, "cubature component hashes/grid")
    bias = interval(analysis["signed_time_bias_bounds"])
    require(bias == (tb[0]-cb[1], tb[1]-cb[0]), "cubature signed grid bias")
    width = cb[1]-cb[0]
    error = max(abs(Fraction(estimate)-v) for v in tb)
    absolute_bias, norm = max(map(abs, bias)), max(cn, tn)
    operations = cm["operations"]+tm["operations"]+1
    checks = {"resolved_reference": True, "reference_width": width <= Fraction(policy["maximum_reference_width"]),
        "functional_roundoff": error <= Fraction(policy["maximum_functional_roundoff"]),
        "time_bias": absolute_bias <= Fraction(policy["maximum_time_bias"]),
        "scaled_transition_growth": norm <= Fraction(policy["maximum_scaled_transition_norm"]),
        "reference_arithmetic_operations": operations <= policy["maximum_operations"]}
    require(analysis["status"] == "PASSED" and analysis["checks"] == checks
        and all(type(v) is bool for v in analysis["checks"].values()) and all(checks.values()), "cubature actual saved checks")
    expected = {"reference_width_upper": outward(width), "functional_roundoff_upper": outward(error),
        "absolute_time_bias_upper": outward(absolute_bias), "scaled_transition_norm_upper": outward(norm),
        "reference_arithmetic_operations": operations, "sampling_error": {"value": 0, "status": "NOT_APPLICABLE"},
        "model_error": {"value": None, "status": "NOT_IDENTIFIABLE"},
        "cost_status": "OWNER_SETTLEMENT_REQUIRED", "maximum_job_seconds": policy["maximum_job_seconds"]}
    require(all(analysis.get(k) == v for k, v in expected.items()), "cubature saved numerical values")
    return cb, tb, bias


def validate_cubature_qualification(receipt, row):
    try:
        _validate(receipt, row)
    except (KeyError, TypeError, AttributeError, IndexError, OverflowError, RecursionError) as exc:
        raise ValueError("missing or malformed cubature qualification evidence") from exc


def _validate(receipt, row):
    spec, cell, docs = receipt["spec"], receipt["cell"], receipt["documents"]
    evidence = docs["propagation_qualification"]
    bounded(evidence, 2*1024*1024)
    sealed(evidence, "evidence_hash")
    require(evidence["schema_version"] == "managed-affine-cubature-admission-evidence-v1"
        and evidence["target_spec_hash"] == receipt["spec_hash"]
        and evidence["target_cell_hash"] == receipt["cell_hash"]
        and evidence["target_request_hash"] == fingerprint(cell["propagation_request"])
        and evidence["source_cell_hash"] == fingerprint(evidence["source_run"]["cell"]), "cubature evidence source/target")
    pointer = docs["package"]["payload"]["managed_cubature_qualification"]
    require(type(pointer) is dict and set(pointer) == {"schema_version", "policy", "source_attempt_id",
        "source_artifact_id", "source_authorization_id", "source_authorization_version"}
        and pointer["schema_version"] == "managed-affine-cubature-qualification-v1"
        and pointer["policy"] == evidence["policy"], "cubature explicit frozen pointer")
    policy = evidence["policy"]
    request = policy_values(policy, spec, cell)
    prereg, policies = docs["preregistration"], docs["preregistration"]["cubature_qualification_policies"]
    require(type(policies) is list and 0 < len(policies) <= 10000 and policies.count(policy) == 1
        and len({fingerprint(p) for p in policies}) == len(policies)
        and prereg["primary_metrics"] == [METRIC] and evidence["preregistration_hash"] == fingerprint(prereg),
        "cubature preregistered policy/metric")
    source = source_chain(evidence, receipt, pointer, policy, source_kind="cubature")
    functional_values(source["forecast"]["functional"], request)
    cb, tb, bias = analysis_values(source["forecast"]["cubature_qualification_analysis"], policy, request,
        source["forecast"]["functional"]["estimate"])
    result, metadata = row["result"], row["result_artifact"]
    artifact(result, metadata, spec, cell)
    require(row["artifact_id"] == metadata["artifact_id"] and result["admission_hash"] == receipt["admission_hash"]
        and row["metrics"] == result["metrics"] and row["metric_units"] == result["metric_units"]
        and row["qualification"] == result["qualification"] == "qualified", "cubature actual current row/artifact")
    forecast, functional = result["forecast"], result["forecast"]["functional"]
    functional_values(functional, request)
    require(forecast["kind"] == "functional_estimate" and forecast["request_hash"] == fingerprint(request)
        and forecast["model_package_hash"] == policy["model_package_hash"] and forecast["horizons"] == request["horizons"],
        "cubature current forecast identity")
    roundoff = max(abs(Fraction(functional["estimate"])-v) for v in tb)
    require(roundoff <= Fraction(policy["maximum_functional_roundoff"]), "cubature current roundoff cap")
    components = {"reference_width_upper": outward(cb[1]-cb[0]), "implementation_roundoff_upper": outward(roundoff),
        "time_bias_absolute_upper": outward(max(map(abs, bias))),
        "signed_time_bias_bounds": source["forecast"]["cubature_qualification_analysis"]["signed_time_bias_bounds"],
        "affine_finite_grid_closure_error": 0, "model_error": {"value": None, "status": "NOT_IDENTIFIABLE"},
        "scope": SCOPE, "qualification_evidence_hash": evidence["evidence_hash"],
        "qualification_source_attempt_id": evidence["source_attempt"]["attempt_id"], "policy_hash": fingerprint(policy)}
    unit = "m" if request["functional"] == "endpoint-x" else "1"
    require(result["metrics"] == {METRIC: outward(max(abs(Fraction(functional["estimate"])-v) for v in cb))}
        and result["metric_units"] == {METRIC: unit} and forecast["qualified_error_components"] == components,
        "cubature current scalar error/provenance")
    budget = functional["error_budget"]
    for name, value, status in (("reference", components["reference_width_upper"], "BOUNDED"),
        ("time_discretization", components["time_bias_absolute_upper"], "BOUNDED"),
        ("propagation_approximation", 0, "IDENTIFIED"), ("sampling", 0, "NOT_APPLICABLE")):
        require(budget[name]["value"] == value and budget[name]["status"] == status and budget[name]["units"] == unit,
            "cubature separated affine-only error")
    require(budget["model"]["value"] is None and budget["model"]["status"] == "NOT_IDENTIFIABLE", "cubature model error stays unknown")
