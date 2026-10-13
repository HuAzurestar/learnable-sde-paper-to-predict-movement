"""Independent stdlib checks of saved mixture proof and settled owner lineage.

No runtime import, raw inputs, numerical replay or Gaussian approval. The
separately trusted bundle hash is essential: a self-rehashed journal cannot
establish authenticity. Scope is one retained functional of a declared law.
"""

from fractions import Fraction

if __package__:
    from .analytic_qualification import (METRIC, artifact, bounded, certificate,
        encoded, fingerprint, finite, interval, outward, sealed, source_chain)
else:
    from analytic_qualification import (METRIC, artifact, bounded, certificate,
        encoded, fingerprint, finite, interval, outward, sealed, source_chain)


PLUGIN_ID = "affine-mixture-production-chunk"
PAYLOAD_KEY = "managed_mixture_qualification"


def require(condition, detail):
    if not condition:
        raise ValueError("invalid admission evidence: mixture qualification " + detail)


def policy_values(policy, mixture, spec, cell):
    bounded(policy, 8192, nodes=100, depth_limit=3)
    bounded(mixture, 8192, nodes=100, depth_limit=3)
    required = {"schema_version", "request_hash", "model_package_hash", "code_hash", "mixture_policy_hash",
        "maximum_reference_width", "maximum_retained_functional_error", "maximum_time_bias",
        "maximum_total_functional_error", "maximum_scaled_transition_norm", "maximum_reference_operations",
        "maximum_job_seconds"}
    mixture_keys = {"schema_version", "request_hash", "model_package_hash", "code_hash", "component_cap",
        "merge_distance", "prune_weight", "state_scales", "maximum_discarded_mass", "maximum_work_units",
        "maximum_job_seconds"}
    require(type(policy) is dict and set(policy) == required
        and policy["schema_version"] == "affine-mixture-functional-qualification-policy-v1"
        and type(mixture) is dict and set(mixture) == mixture_keys
        and mixture["schema_version"] == "bounded-cubature-mixture-policy-v1", "complete explicit policies")
    request, model = cell["propagation_request"], cell["frozen_dynamics"]
    bounded(request, 64*1024, nodes=2048, depth_limit=10)
    bounded(model, 64*1024, nodes=2048, depth_limit=10)
    for key, expected in (("request_hash", fingerprint(request)), ("model_package_hash", fingerprint(model)),
            ("code_hash", spec["code_hash"])):
        require(type(expected) is str and len(expected) == 64 and all(c in "0123456789abcdef" for c in expected)
            and policy[key] == mixture[key] == expected, "full policy/model/request/source hash")
    require(policy["model_package_hash"] == request["model_package_hash"]
        and policy["mixture_policy_hash"] == fingerprint(mixture)
        and cell["mixture_policy"] == mixture and cell["mixture_qualification_policy"] == policy,
        "current frozen policies")
    require(model["schema_version"] == "frozen-affine-dynamics-v1" and model["family"] == "affine-oracle"
        and model["frozen"] is True and model["qualification"] == {"scope": "oracle-fixture", "scientific_qualification": False},
        "declared synthetic law, not scientific model qualification")
    require(all(finite(policy[k], positive=True) for k in ("maximum_reference_width", "maximum_retained_functional_error",
        "maximum_time_bias", "maximum_total_functional_error", "maximum_scaled_transition_norm", "maximum_job_seconds"))
        and policy["maximum_job_seconds"] <= 1800
        and type(policy["maximum_reference_operations"]) is int and 1 <= policy["maximum_reference_operations"] <= 400001,
        "finite qualification caps")
    require(type(mixture["component_cap"]) is int and 1 <= mixture["component_cap"] <= 32
        and finite(mixture["merge_distance"]) and mixture["merge_distance"] >= 0
        and all(finite(mixture[k]) and 0 <= mixture[k] < 1 for k in ("prune_weight", "maximum_discarded_mass"))
        and type(mixture["state_scales"]) is list and len(mixture["state_scales"]) == 4
        and all(finite(s, positive=True) for s in mixture["state_scales"])
        and type(mixture["maximum_work_units"]) is int and 1 <= mixture["maximum_work_units"] <= 1000000
        and finite(mixture["maximum_job_seconds"], positive=True)
        and policy["maximum_job_seconds"] <= mixture["maximum_job_seconds"] <= 7200, "bounded physical mixture caps")
    require(type(request["steps"]) is int and 1 <= request["steps"] <= 8192
        and request["functional"] in {"endpoint-x", "endpoint-halfspace"}
        and request["arm_id"] == cell["arm_id"] and finite(request["tolerance"], positive=True)
        and policy["maximum_total_functional_error"] <= request["tolerance"], "frozen functional and accuracy target")
    cap = mixture["component_cap"]
    work = request["steps"]*8*cap*(cap+1+4**3)
    require(work <= mixture["maximum_work_units"] and work+400001 <= 1000000, "fixed worst-case reference allocation")
    arms = [a for a in spec["arms"] if a["arm_id"] == cell["arm_id"]]
    require(len(arms) == 1 and arms[0]["method_family_id"] == "mixture"
        and cell["plugin_id"] == PLUGIN_ID and cell["execution_role"] == "production", "explicit original-arm target")
    return request, work


def configuration(request, mixture, policy, work):
    return {"method": "mixture", "samples": request["samples"], "base_steps": request["steps"],
        "steps": request["steps"], "chunk_size": request["chunk_size"], "level_samples": [], "proposal": [0., 0.],
        "work_steps": work, "mixture_policy_hash": fingerprint(mixture), "component_cap": mixture["component_cap"],
        "candidate_cap": 8*mixture["component_cap"], "qualification_policy_hash": fingerprint(policy)}


def analysis_values(analysis, policy, mixture, request, functional, work):
    bounded(analysis, 512*1024)
    bounded(functional, 512*1024)
    estimate = functional["estimate"]
    require(finite(estimate) and functional["kind"] == "functional_estimate"
        and functional["estimator_id"] == "retained-cubature-mixture-euler-v1"
        and functional["request_hash"] == fingerprint(request)
        and type(functional["sample_count"]) is int and functional["sample_count"] == 0
        and type(functional["standard_error"]) in (int, float) and functional["standard_error"] == 0
        and functional["interval"] is None and functional["interval_kind"] == "deterministic-mixture-no-sampling"
        and functional["status"] == "APPROXIMATION_ONLY", "actual retained source functional")
    sealed(analysis, "analysis_hash")
    require(analysis["schema_version"] == "affine-mixture-functional-qualification-analysis-v1"
        and analysis["scope"] == "one-retained-mixture-functional-vs-declared-affine-continuous-and-Euler-law"
        and analysis["scientific_qualification"] is False
        and all(analysis[k] == policy[k] for k in ("request_hash", "model_package_hash", "code_hash", "mixture_policy_hash"))
        and analysis["policy_hash"] == fingerprint(policy) and analysis["actual_functional_hash"] == fingerprint(functional)
        and encoded(analysis["actual_estimate"]) == encoded(estimate), "mixture analysis binding and scope")
    cm, tm = analysis["continuous_certificate"], analysis["target_certificate"]
    component_policy = {**policy, "state_scales": mixture["state_scales"]}
    cb, cn = certificate(cm, component_policy)
    tb, tn = certificate(tm, component_policy, discrete=True, request=request)
    require(analysis["continuous_certificate_hash"] == fingerprint(cm)
        and analysis["target_certificate_hash"] == fingerprint(tm)
        and analysis["target_grid"] == {"solver": "euler", "steps": request["steps"]}, "saved reference hashes/grid")
    bias = interval(analysis["signed_time_bias_bounds"])
    require(bias == (tb[0]-cb[1], tb[1]-cb[0]), "signed Euler-minus-continuous bias")
    retained, total = (max(abs(Fraction(estimate)-v) for v in bounds) for bounds in (tb, cb))
    width, absolute_bias, norm = max(cb[1]-cb[0], tb[1]-tb[0]), max(map(abs, bias)), max(cn, tn)
    operations = cm["operations"]+tm["operations"]+1
    checks = {"resolved_reference": cm["status"] == tm["status"] == "BOUNDED",
        "reference_width": width <= Fraction(policy["maximum_reference_width"]),
        "retained_functional_error": retained <= Fraction(policy["maximum_retained_functional_error"]),
        "time_bias": absolute_bias <= Fraction(policy["maximum_time_bias"]),
        "total_functional_error": total <= Fraction(policy["maximum_total_functional_error"]),
        "scaled_transition_growth": norm <= Fraction(policy["maximum_scaled_transition_norm"]),
        "reference_operations": operations <= policy["maximum_reference_operations"]}
    require(analysis["checks"] == checks and all(type(v) is bool for v in analysis["checks"].values())
        and analysis["status"] == "PASSED" and all(checks.values()), "seven actual numerical checks")
    unknown = {"value": None, "status": "NOT_IDENTIFIABLE"}
    expected = {"reference_width_upper": outward(width), "retained_functional_error_upper": outward(retained),
        "total_functional_error_upper": outward(total), "absolute_time_bias_upper": outward(absolute_bias),
        "scaled_transition_norm_upper": outward(norm), "reference_operations": operations, "mixture_work_units": work,
        "retained_error_scope": "closure-pruning-normalization-and-implementation-roundoff-inseparable",
        "propagation_approximation": unknown, "implementation_roundoff": unknown, "model_error": unknown,
        "sampling_error": {"value": 0, "status": "NOT_APPLICABLE"}, "cost_status": "OWNER_SETTLEMENT_REQUIRED",
        "maximum_job_seconds": policy["maximum_job_seconds"],
        "scaled_transition_norm_definition": "max row sum |F_ij| scale_j/scale_i; declared horizon"}
    require(all(encoded(analysis.get(k)) == encoded(v) for k, v in expected.items()), "numeric definitions and unknowns")
    return cb, tb, bias


def resource(receipt, cell, mixture, work, plugin, resume_level):
    plan, entry = receipt["resource_plan"], receipt["registry_entry"]
    sealed(plan, "resource_plan_hash")
    counts = plan["counts"]
    require(entry["component_id"] == plugin and entry["version"] == "1.0.0" and entry["resume_level"] == resume_level
        and plan["registry_entry_hash"] == fingerprint(entry) and cell["execution"]["resource_plan_hash"] == plan["resource_plan_hash"]
        and counts["state_dim"] == 4 and counts["paths"] == 1 and counts["components"] == mixture["component_cap"]
        and counts["observations"] == 8*mixture["component_cap"] and counts["steps"] == work
        and type(plan["tensor_bytes"]) is int and plan["tensor_bytes"] >= 64*1024*1024, "bounded numerical resource contract")


def validate_mixture_qualification(receipt, row):
    try:
        _validate(receipt, row)
    except (KeyError, TypeError, AttributeError, IndexError, OverflowError, RecursionError) as exc:
        raise ValueError("missing or malformed mixture qualification evidence") from exc


def _validate(receipt, row):
    # Quotas precede copying, hashing and rational arithmetic, including cyclic
    # direct-call objects (JSON transport alone is not the only caller).
    bounded(receipt, 8*1024*1024)
    bounded(row, 16*1024*1024, nodes=200000)
    spec, cell, docs = receipt["spec"], receipt["cell"], receipt["documents"]
    evidence = docs["propagation_qualification"]
    bounded(evidence, 2*1024*1024)
    sealed(evidence, "evidence_hash")
    require(evidence["schema_version"] == "managed-affine-mixture-admission-evidence-v1"
        and evidence["target_spec_hash"] == receipt["spec_hash"] == fingerprint(spec)
        and evidence["target_cell_hash"] == receipt["cell_hash"] == fingerprint(cell)
        and receipt["mode"] == "formal" and receipt["qualification"] == "qualified", "current formal target identity")
    policy, mixture = evidence["policy"], evidence["mixture_policy"]
    request, work = policy_values(policy, mixture, spec, cell)
    pointer = docs["package"]["payload"][PAYLOAD_KEY]
    require(type(pointer) is dict and set(pointer) == {"schema_version", "policy", "source_attempt_id", "source_artifact_id",
        "source_authorization_id", "source_authorization_version"}
        and pointer["schema_version"] == "managed-affine-mixture-qualification-v1" and pointer["policy"] == policy,
        "explicit source pointer")
    prereg = docs["preregistration"]
    policies = prereg["mixture_qualification_policies"]
    require(type(policies) is list and 0 < len(policies) <= 10000 and policies.count(policy) == 1
        and len({fingerprint(p) for p in policies}) == len(policies) and prereg["primary_metrics"] == [METRIC]
        and evidence["preregistration_hash"] == fingerprint(prereg), "frozen mixture policy and primary metric")
    source = source_chain(evidence, receipt, pointer, policy, source_kind="mixture")
    source_cell = evidence["source_run"]["cell"]
    require(encoded(cell["execution"]["config"]) == encoded(configuration(request, mixture, policy, work))
        and encoded(source_cell["execution"]["config"]) == encoded(configuration(request, mixture, policy, work+400001)),
        "fixed target and pilot work/configuration")
    resource(evidence["source_admission"], source_cell, mixture, work+400001, "affine-mixture-qualification", "restart-only")
    resource(receipt, cell, mixture, work, PLUGIN_ID, "chunk")
    original = source["forecast"]["functional"]
    analysis = source["forecast"]["mixture_qualification_analysis"]
    cb, tb, bias = analysis_values(analysis, policy, mixture, request, original, work)
    result, metadata = row["result"], row["result_artifact"]
    artifact(result, metadata, spec, cell, resume_level="chunk")
    require(row["artifact_id"] == metadata["artifact_id"] and result["admission_hash"] == receipt["admission_hash"]
        and row["metrics"] == result["metrics"] and row["metric_units"] == result["metric_units"]
        and row["qualification"] == result["qualification"] == "qualified", "current row/artifact/admission")
    charges = [e["payload"] for e in row["cost"]["sources"] if e["payload"]["attempt_id"] == row["attempt_id"]]
    require(len(charges) == 1 and charges[0]["settled"] is True and charges[0]["outcome"] == "SUCCEEDED"
        and type(charges[0]["charged_ms"]) is int and type(charges[0]["reserved_ms"]) is int
        and 0 < charges[0]["charged_ms"] <= charges[0]["reserved_ms"] <= Fraction(policy["maximum_job_seconds"])*1000,
        "actual target cost under frozen cap")
    forecast, functional = result["forecast"], result["forecast"]["functional"]
    budget = functional["error_budget"]
    raw = {**functional, "error_budget": {**budget, **{k: original["error_budget"][k]
        for k in ("reference", "time_discretization")}}}
    require(fingerprint(raw) == analysis["actual_functional_hash"], "current full deterministic functional and lineage")
    estimate = functional["estimate"]
    require(finite(estimate) and forecast["kind"] == "functional_estimate"
        and forecast["request_hash"] == fingerprint(request) and forecast["model_package_hash"] == policy["model_package_hash"]
        and forecast["horizons"] == request["horizons"], "current forecast identity")
    retained, total = (max(abs(Fraction(estimate)-v) for v in bounds) for bounds in (tb, cb))
    require(retained <= Fraction(policy["maximum_retained_functional_error"])
        and total <= Fraction(policy["maximum_total_functional_error"]) <= Fraction(request["tolerance"]), "current accuracy caps")
    components = {"reference_width_upper": outward(max(cb[1]-cb[0], tb[1]-tb[0])),
        "retained_functional_error_upper": outward(retained), "total_functional_error_upper": outward(total),
        "time_bias_absolute_upper": outward(max(map(abs, bias))), "signed_time_bias_bounds": analysis["signed_time_bias_bounds"],
        "propagation_approximation": analysis["propagation_approximation"], "implementation_roundoff": analysis["implementation_roundoff"],
        "model_error": analysis["model_error"], "retained_error_scope": analysis["retained_error_scope"],
        "scope": "one-functional-of-declared-affine-law-only", "policy_hash": fingerprint(policy), "mixture_policy_hash": fingerprint(mixture),
        "qualification_evidence_hash": evidence["evidence_hash"], "qualification_source_attempt_id": evidence["source_attempt"]["attempt_id"]}
    unit = "m" if request["functional"] == "endpoint-x" else "1"
    require(encoded(forecast["qualified_error_components"]) == encoded(components)
        and encoded(result["metrics"]) == encoded({METRIC: outward(total)}) and result["metric_units"] == {METRIC: unit},
        "current numeric upper, unknown errors and provenance")
    require(encoded(budget["reference"]) == encoded({"value": components["reference_width_upper"], "units": unit,
            "estimated_by": "outward max of continuous and Euler functional interval widths", "status": "BOUNDED"})
        and encoded(budget["time_discretization"]) == encoded({"value": components["time_bias_absolute_upper"], "units": unit,
            "estimated_by": "outward absolute signed grid-minus-continuous expectation bound", "status": "BOUNDED"}),
        "bounded component values, units and definitions")
