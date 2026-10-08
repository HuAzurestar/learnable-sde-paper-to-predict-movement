"""Independent stdlib validation of settled MLMC pilot/production receipts.

Only saved bounded enclosures and recorded moments/costs are checked. Trusted
expected export hash remains essential; no runtime, data, execution, authority,
matrix/CDF replay, complexity theorem or rigorous coverage claim is created.
"""

from fractions import Fraction
import math

if __package__:
    from .analytic_qualification import (bounded, sealed, require, fingerprint, encoded,
        certificate, interval, outward, finite, artifact, source_chain)
else:
    from analytic_qualification import (bounded, sealed, require, fingerprint, encoded,
        certificate, interval, outward, finite, artifact, source_chain)


METRIC = "absolute_error_upper_vs_declared_affine_law"
PLUGIN_ID = "affine-mlmc-production-chunk"


def sampling(functional, request, counts, *, pilot=False):
    diagnostics = functional["diagnostics"]
    require(type(diagnostics) is list and all(type(v) is list and len(v) == 2 for v in diagnostics), "MLMC diagnostics shape")
    d = dict(diagnostics)
    require(len(d) == len(diagnostics) and d["level_samples"] == counts, "unique actual level allocation")
    means, variances = d["level_means"], d["level_variances"]
    require(type(means) is list and type(variances) is list and len(means) == len(variances) == len(counts)
        and all(finite(v) for v in means+variances) and all(v >= 0 for v in variances), "finite level statistics")
    estimate = math.fsum(means)
    se = math.sqrt(math.fsum(v/n for v, n in zip(variances, counts)))
    unresolved = request["functional"] == "endpoint-halfspace" and se == 0
    ci = None if unresolved else [estimate-1.959963984540054*se, estimate+1.959963984540054*se]
    require(functional["request_hash"] == fingerprint(request) and functional["kind"] == "functional_estimate"
        and functional["estimator_id"] == ("coupled-euler-mlmc-pilot-v1" if pilot else "coupled-euler-mlmc-v1")
        and functional["sample_count"] == sum(counts) and functional["estimate"] == estimate
        and functional["standard_error"] == (None if unresolved else se) and functional["interval"] == ci
        and functional["interval_kind"] == ("unavailable-zero-observed-level-variance" if unresolved else "independent-level-normal-approximation-95")
        and functional["status"] == ("UNRESOLVED_SAMPLING" if unresolved else "PILOT_ONLY" if pilot else "SUCCEEDED")
        and d["coupling"] == "coarse-increment=sum(two-fine-increments)", "current sampling identity/scalar/SE/interval")
    return d


def pilot_analysis(functional, request, pilot, counts):
    required = {"schema_version", "pilot_request_hash", "production_seed", "production_coupling_id", "sampling_tolerance",
        "bias_tolerance", "maximum_variance_ratio", "maximum_cost_ratio", "minimum_level_samples", "maximum_samples", "maximum_work_steps"}
    require(type(pilot) is dict and set(pilot) == required and pilot["schema_version"] == "endpoint-mlmc-pilot-policy-v1"
        and pilot["pilot_request_hash"] == fingerprint(request)
        and type(pilot["production_seed"]) is int and 0 <= pilot["production_seed"] < 2**63
        and pilot["production_seed"] != request["seed"]
        and type(pilot["production_coupling_id"]) is str and 0 < len(pilot["production_coupling_id"]) <= 128
        and not any(ord(c) < 32 for c in pilot["production_coupling_id"])
        and all(finite(pilot[k], positive=True) for k in ("sampling_tolerance", "bias_tolerance", "maximum_variance_ratio", "maximum_cost_ratio"))
        and pilot["maximum_variance_ratio"] < 1 and pilot["maximum_cost_ratio"] > 1
        and all(type(pilot[k]) is int and 2 <= pilot[k] <= 1_000_000 for k in ("minimum_level_samples", "maximum_samples"))
        and type(pilot["maximum_work_steps"]) is int and 1 <= pilot["maximum_work_steps"] <= 1_000_000
        and all(n >= pilot["minimum_level_samples"] for n in counts) and sum(counts) <= pilot["maximum_samples"], "complete independent pilot policy")
    d = sampling(functional, request, counts, pilot=True)
    work = [request["steps"]*2**level+(request["steps"]*2**(level-1) if level else 0) for level in range(len(counts))]
    elapsed, variances = d["level_compute_ns"], d["level_variances"]
    require(type(d["pilot_phase"]) is int and d["pilot_phase"] == 2
        and type(d["production_phase"]) is int and d["production_phase"] == 1
        and d["level_work_per_sample"] == work and sum(n*w for n, w in zip(counts, work)) <= pilot["maximum_work_steps"]
        and d["cost_scope"] == "compute-only-excludes-checkpoint-ACK-not-budget-charge"
        and type(elapsed) is list and len(elapsed) == len(counts) and all(type(v) is int and 0 < v < 2**63 for v in elapsed), "real measured phase/coupling/cost")
    costs = [ns/n for ns, n in zip(elapsed, counts)]
    variance_ratios = [variances[l]/variances[l-1] if variances[l-1] > 0 else None for l in range(2, len(counts))]
    variance_ratios = [v if finite(v) else None for v in variance_ratios]
    cost_ratios = [costs[l]/costs[l-1] for l in range(1, len(counts))]
    require(all(v is not None and v <= pilot["maximum_variance_ratio"] for v in variance_ratios)
        and all(v > 0 for v in variances[1:]) and all(finite(v) and v <= pilot["maximum_cost_ratio"] for v in cost_ratios)
        and functional["status"] == "PILOT_ONLY", "empirical pilot variance/cost/sampling gate")
    normalizer = math.fsum(math.sqrt(v)*math.sqrt(c) for v, c in zip(variances, costs))/pilot["sampling_tolerance"]**2
    proposal = [max(2, math.ceil(normalizer*math.sqrt(v/c))) for v, c in zip(variances, costs)]
    require(sum(proposal) <= pilot["maximum_samples"] and sum(n*w for n, w in zip(proposal, work)) <= pilot["maximum_work_steps"], "bounded sampling allocation")
    bias = functional["error_budget"]["time_discretization"]["value"]
    reference = functional["error_budget"]["reference"]["value"]
    require(bias is None or finite(bias), "finite or unknown original bias")
    require(reference is None or finite(reference) and reference >= 0, "finite or unknown original reference")
    reasons = []
    if bias is None:
        reasons.append("BIAS_UNRESOLVED")
    elif abs(bias) > pilot["bias_tolerance"]:
        reasons.append("BIAS_TOLERANCE_FAILED")
    if reference is None:
        reasons.append("REFERENCE_UNRESOLVED")
    reasons.append("ENGINEERING_ONLY")
    return {"schema_version": "endpoint-mlmc-pilot-analysis-v1", "request_hash": fingerprint(request),
        "policy_hash": fingerprint(pilot), "status": "UNQUALIFIED", "reasons": reasons,
        "qualification_scope": "empirical-engineering-pilot-not-scientific-approval",
        "level_variance_ratios": variance_ratios, "level_cost_ratios": cost_ratios, "level_unit_compute_ns": costs,
        "signed_discretization_bias": bias, "reference_uncertainty": reference, "sampling_only_proposal": proposal,
        "production_stream": {"seed": pilot["production_seed"], "coupling_id": pilot["production_coupling_id"], "phase": 1},
        "requires_separate_production_registration": True, "automatic_execution": False,
        "cost_scope": "compute-only;shared-ledger-remains-sole-budget-authority"}


def analysis_values(analysis, reference, pilot, request, functional):
    bounded(analysis, 384*1024)
    sealed(analysis, "analysis_hash")
    required = {"schema_version", "request_hash", "model_package_hash", "code_hash", "pilot_policy_hash", "level_samples",
        "maximum_reference_width", "maximum_scaled_transition_norm", "state_scales", "maximum_operations", "maximum_job_seconds"}
    counts = reference["level_samples"]
    require(set(reference) == required and reference["schema_version"] == "affine-mlmc-reference-policy-v1"
        and reference["request_hash"] == fingerprint(request) and reference["pilot_policy_hash"] == fingerprint(pilot)
        and reference["model_package_hash"] == request["model_package_hash"]
        and type(counts) is list and 3 <= len(counts) <= 9 and all(type(n) is int and 2 <= n <= 1_000_000 for n in counts)
        and sum(counts) == request["samples"] and type(request["steps"]) is int and 1 <= request["steps"] <= 8192
        and request["steps"]*2**(len(counts)-1) <= 8192
        and all(finite(reference[k], positive=True) for k in ("maximum_reference_width", "maximum_scaled_transition_norm", "maximum_job_seconds"))
        and reference["maximum_job_seconds"] <= 1800 and type(reference["maximum_operations"]) is int
        and 1 <= reference["maximum_operations"] <= 400_001
        and type(reference["state_scales"]) is list and len(reference["state_scales"]) == 4
        and all(finite(v, positive=True) for v in reference["state_scales"]), "complete bounded MLMC reference policy")
    require(analysis["schema_version"] == "affine-mlmc-reference-pilot-analysis-v1" and analysis["status"] == "NUMERICAL_READY"
        and analysis["qualification"] == "UNQUALIFIED" and analysis["scientific_qualification"] is False
        and analysis["reference_policy_hash"] == fingerprint(reference) and analysis["pilot_policy_hash"] == fingerprint(pilot)
        and all(analysis[k] == reference[k] for k in ("request_hash", "model_package_hash", "code_hash")), "source readiness/identity")
    empirical = pilot_analysis(functional, request, pilot, counts)
    require(analysis["empirical_pilot_analysis"] == empirical and analysis["empirical_failures"] == [], "recomputed empirical pilot")
    finest_steps = request["steps"]*2**(len(counts)-1)
    cm, fm = analysis["continuous_certificate"], analysis["finest_certificate"]
    cb, cn = certificate(cm, reference)
    fb, fn = certificate(fm, reference, discrete=True, request={**request, "steps": finest_steps})
    require(analysis["continuous_certificate_hash"] == fingerprint(cm) and analysis["finest_certificate_hash"] == fingerprint(fm)
        and analysis["finest_grid"] == {"solver": "euler", "base_steps": request["steps"], "level_count": len(counts), "steps": finest_steps}, "finest-grid hashes/identity")
    bias = interval(analysis["signed_finest_grid_bias_bounds"])
    require(bias == (fb[0]-cb[1], fb[1]-cb[0]), "signed finest-grid bias")
    width, absolute_bias, norm = cb[1]-cb[0], max(map(abs, bias)), max(cn, fn)
    operations = cm["operations"]+fm["operations"]+1
    checks = {"resolved_reference": True, "reference_width": width <= Fraction(reference["maximum_reference_width"]),
        "finest_grid_bias": absolute_bias <= Fraction(pilot["bias_tolerance"]),
        "scaled_transition_growth": norm <= Fraction(reference["maximum_scaled_transition_norm"]),
        "arithmetic_operations": operations <= reference["maximum_operations"], "empirical_sampling_and_cost": True}
    require(analysis["checks"] == checks and all(type(v) is bool for v in analysis["checks"].values()) and all(checks.values()), "actual numeric/empirical checks")
    expected = {"reference_width_upper": outward(width), "finest_grid_bias_absolute_upper": outward(absolute_bias),
        "scaled_transition_norm_upper": outward(norm), "operations": operations,
        "observed_pilot_error_upper_vs_continuous_law": outward(max(abs(Fraction(functional["estimate"])-v) for v in cb)),
        "state_scales": reference["state_scales"], "state_scale_units": ["m", "m", "m/s", "m/s"],
        "functional_unit": "m" if request["functional"] == "endpoint-x" else "1",
        "sampling_error": {"value": functional["standard_error"], "status": "ESTIMATED", "interval_kind": functional["interval_kind"], "confidence_interval": functional["interval"]},
        "sampler_roundoff": {"value": None, "status": "NOT_IDENTIFIABLE"}, "model_error": {"value": None, "status": "NOT_IDENTIFIABLE"},
        "cost_status": "OWNER_SETTLEMENT_REQUIRED", "maximum_job_seconds": reference["maximum_job_seconds"],
        "production_stream": empirical["production_stream"], "requires_separate_production_registration": True, "automatic_execution": False,
        "scope": "necessary-affine-finest-grid-and-empirical-pilot-checks-only",
        "observed_error_scope": "current scalar only; sampling and implementation effects not separated"}
    require(all(analysis.get(k) == v for k, v in expected.items()), "saved bounds/unknowns/stream")
    return cb, bias, empirical


def validate_mlmc_qualification(receipt, row):
    try:
        _validate(receipt, row)
    except (KeyError, TypeError, AttributeError, IndexError, OverflowError, RecursionError, ZeroDivisionError) as exc:
        raise ValueError("missing or malformed MLMC qualification evidence") from exc


def _validate(receipt, row):
    spec, cell, docs = receipt["spec"], receipt["cell"], receipt["documents"]
    evidence = docs["propagation_qualification"]
    bounded(evidence, 2*1024*1024)
    sealed(evidence, "evidence_hash")
    production, pilot, reference = evidence["production_policy"], evidence["pilot_policy"], evidence["reference_policy"]
    require(evidence["schema_version"] == "managed-affine-mlmc-admission-evidence-v1"
        and evidence["target_spec_hash"] == receipt["spec_hash"] and evidence["target_cell_hash"] == receipt["cell_hash"], "MLMC target evidence identity")
    required = {"schema_version", "request_hash", "model_package_hash", "code_hash", "pilot_request_hash",
        "pilot_policy_hash", "reference_policy_hash", "level_samples", "maximum_job_seconds"}
    request, model, config = cell["propagation_request"], cell["frozen_dynamics"], cell["execution"]["config"]
    counts = production["level_samples"]
    require(set(production) == required and production["schema_version"] == "affine-mlmc-production-policy-v1"
        and cell["plugin_id"] == PLUGIN_ID and cell["execution_role"] == "production" and config["method"] == "mlmc"
        and cell["mlmc_production_policy"] == production and production["request_hash"] == fingerprint(request)
        and production["model_package_hash"] == fingerprint(model) == request["model_package_hash"]
        and production["code_hash"] == reference["code_hash"] == spec["code_hash"]
        and production["pilot_request_hash"] == reference["request_hash"] != production["request_hash"]
        and production["pilot_policy_hash"] == fingerprint(pilot) and production["reference_policy_hash"] == fingerprint(reference)
        and type(counts) is list and 3 <= len(counts) <= 9 and all(type(n) is int and 2 <= n <= 1_000_000 for n in counts)
        and sum(counts) == request["samples"] <= 1_000_000 and config["level_samples"] == counts
        and config["production_policy_hash"] == fingerprint(production)
        and finite(production["maximum_job_seconds"], positive=True) and production["maximum_job_seconds"] <= 7200
        and model["schema_version"] == "frozen-affine-dynamics-v1" and model["family"] == "affine-oracle"
        and model["frozen"] is True and model["qualification"] == {"scope": "oracle-fixture", "scientific_qualification": False}, "frozen independent production policy/law")
    pointer = docs["package"]["payload"]["managed_mlmc_qualification"]
    require(type(pointer) is dict and set(pointer) == {"schema_version", "production_policy", "source_attempt_id",
        "source_artifact_id", "source_authorization_id", "source_authorization_version"}
        and pointer["schema_version"] == "managed-affine-mlmc-qualification-v1" and pointer["production_policy"] == production, "explicit source/production pointer")
    prereg = docs["preregistration"]
    policies = prereg["mlmc_production_policies"]
    require(type(policies) is list and 0 < len(policies) <= 10000 and policies.count(production) == 1
        and len({fingerprint(p) for p in policies}) == len(policies) and prereg["primary_metrics"] == [METRIC]
        and evidence["preregistration_hash"] == fingerprint(prereg), "separately frozen production registration")
    source = source_chain(evidence, receipt, pointer, reference, source_kind="mlmc")
    sc = evidence["source_run"]["cell"]
    sr = sc["propagation_request"]
    ignored = {"request_id", "seed", "coupling_id", "samples", "chunk_size"}
    require({k: v for k, v in request.items() if k not in ignored} == {k: v for k, v in sr.items() if k not in ignored}
        and request["seed"] == pilot["production_seed"] and request["coupling_id"] == pilot["production_coupling_id"]
        and sc["mlmc_pilot_policy"] == pilot and fingerprint(sr) == reference["request_hash"]
        and sc["execution"]["config"]["level_samples"] == reference["level_samples"]
        and sc["execution"]["config"]["reference_policy_hash"] == fingerprint(reference), "same source law/grid and independent stream")
    arms = [a for a in spec["arms"] if a["arm_id"] == cell["arm_id"]]
    require(len(arms) == 1 and arms[0]["method_family_id"] == "mlmc", "same original MLMC cumulative arm")
    analysis = source["forecast"]["bounded_mlmc_pilot_analysis"]
    cb, bias, empirical = analysis_values(analysis, reference, pilot, sr, source["forecast"]["functional"])
    require(counts == empirical["sampling_only_proposal"], "production allocation equals frozen pilot proposal")
    result, metadata = row["result"], row["result_artifact"]
    artifact(result, metadata, spec, cell, resume_level="chunk")
    require(row["artifact_id"] == metadata["artifact_id"] and result["admission_hash"] == receipt["admission_hash"]
        and row["metrics"] == result["metrics"] and row["metric_units"] == result["metric_units"]
        and row["qualification"] == result["qualification"] == "qualified", "current target row/artifact")
    plan, entry = receipt["resource_plan"], receipt["registry_entry"]
    sealed(plan, "resource_plan_hash")
    require(entry["component_id"] == PLUGIN_ID and plan["registry_entry_hash"] == fingerprint(entry)
        and cell["execution"]["resource_plan_hash"] == plan["resource_plan_hash"] and plan["counts"]["state_dim"] == 4
        and plan["tensor_bytes"] >= 64*1024*1024, "target resource contract")
    charges = [e["payload"] for e in row["cost"]["sources"] if e["payload"]["attempt_id"] == row["attempt_id"]]
    require(len(charges) == 1 and charges[0]["settled"] is True and charges[0]["outcome"] == "SUCCEEDED"
        and type(charges[0]["charged_ms"]) is int and 0 < charges[0]["charged_ms"] <= charges[0]["reserved_ms"]
        <= Fraction(production["maximum_job_seconds"])*1000, "production measured cost under frozen cap")
    forecast, functional = result["forecast"], result["forecast"]["functional"]
    d = sampling(functional, request, counts)
    require(functional["standard_error"] is not None and functional["standard_error"] <= pilot["sampling_tolerance"]
        and all(v > 0 for v in d["level_variances"]) and forecast["kind"] == "functional_estimate"
        and forecast["request_hash"] == fingerprint(request) and forecast["model_package_hash"] == production["model_package_hash"]
        and forecast["horizons"] == request["horizons"], "actual production sampling target")
    components = {"reference_width_upper": outward(cb[1]-cb[0]), "time_bias_absolute_upper": outward(max(map(abs, bias))),
        "signed_time_bias_bounds": analysis["signed_finest_grid_bias_bounds"],
        "sampling_error": {"value": functional["standard_error"], "status": "ESTIMATED", "interval_kind": functional["interval_kind"]},
        "sampler_roundoff": {"value": None, "status": "NOT_IDENTIFIABLE"}, "model_error": {"value": None, "status": "NOT_IDENTIFIABLE"},
        "scope": "declared-affine-law-only;current-scalar-error-includes-sampling-and-implementation",
        "confidence_scope": "normal-approximation-not-rigorous-coverage", "policy_hash": fingerprint(production),
        "qualification_evidence_hash": evidence["evidence_hash"], "qualification_source_attempt_id": evidence["source_attempt"]["attempt_id"],
        "stream": {"phase": 1, "seed": request["seed"], "coupling_id": request["coupling_id"], "level_samples": counts}}
    unit = "m" if request["functional"] == "endpoint-x" else "1"
    require(forecast["qualified_error_components"] == components
        and result["metrics"] == {METRIC: outward(max(abs(Fraction(functional["estimate"])-v) for v in cb))}
        and result["metric_units"] == {METRIC: unit}, "current scalar error upper and honest separated components")
    budget = functional["error_budget"]
    for key, value in (("reference", components["reference_width_upper"]), ("time_discretization", components["time_bias_absolute_upper"])):
        require(budget[key]["value"] == value and budget[key]["status"] == "BOUNDED" and budget[key]["units"] == unit, "bounded error separation")
    require(budget["sampling"]["value"] == functional["standard_error"] and budget["sampling"]["status"] == "ESTIMATED"
        and budget["model"]["value"] is None and budget["model"]["status"] == "NOT_IDENTIFIABLE", "estimated sampling/unknown model")
