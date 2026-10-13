"""Independent saved path/IS statistics, same-law proof and owner cost checks.

Stdlib only; no runtime imports, sampler, matrix/CDF replay or grant creation.
A source pass is not a target pass. The trusted external bundle hash remains
essential; these checks cannot authenticate arbitrary self-resealed journals.
"""

from fractions import Fraction
import math

if __package__:
    from .analytic_qualification import (ALGORITHM, artifact, bounded, encoded,
        fingerprint, finite, interval, outward, sealed, source_chain)
else:
    from analytic_qualification import (ALGORITHM, artifact, bounded, encoded,
        fingerprint, finite, interval, outward, sealed, source_chain)


PLUGIN_ID = "affine-path-production-chunk"
PAYLOAD_KEY = "managed_path_qualification"
METRIC = "observed_absolute_error_upper_vs_declared_affine_law"
METHODS = {"euler": "euler", "heun": "additive-heun", "reversible-heun": "reversible-heun", "importance": "importance"}
Z = 1.959963984540054


def require(condition, detail):
    if not condition:
        raise ValueError("invalid admission evidence: path qualification " + detail)


def policies(production, qualification, spec, cell, source_cell):
    bounded(production, 8192, nodes=100, depth_limit=3)
    bounded(qualification, 8192, nodes=100, depth_limit=3)
    pk = {"schema_version", "request_hash", "model_package_hash", "code_hash", "source_request_hash",
        "qualification_policy_hash", "maximum_job_seconds"}
    qk = {"schema_version", "request_hash", "model_package_hash", "code_hash", "method", "proposal", "state_scales",
        "maximum_reference_width", "maximum_observed_grid_error", "maximum_time_bias",
        "maximum_total_observed_functional_error", "maximum_sampling_uncertainty", "minimum_effective_sample_size",
        "maximum_scaled_transition_norm", "maximum_reference_operations", "maximum_job_seconds"}
    require(type(production) is dict and set(production) == pk
        and production["schema_version"] == "affine-independent-path-production-policy-v1"
        and type(qualification) is dict and set(qualification) == qk
        and qualification["schema_version"] == "affine-path-functional-qualification-policy-v1", "complete explicit policies")
    target, source, model = cell["propagation_request"], source_cell["propagation_request"], cell["frozen_dynamics"]
    for request in (target, source):
        bounded(request, 64*1024, nodes=2048, depth_limit=10)
        require(type(request["samples"]) is int and 2 <= request["samples"] <= 1000000
            and type(request["steps"]) is int and 1 <= request["steps"] <= 8192
            and type(request["chunk_size"]) is int and 1 <= request["chunk_size"] <= 1000000
            and type(request["seed"]) is int and request["seed"] >= 0
            and finite(request["tolerance"], positive=True)
            and request["functional"] in {"endpoint-x", "endpoint-halfspace"}, "bounded endpoint request")
    bounded(model, 64*1024, nodes=2048, depth_limit=10)
    require(production["request_hash"] == fingerprint(target)
        and production["source_request_hash"] == qualification["request_hash"] == fingerprint(source)
        and production["request_hash"] != production["source_request_hash"]
        and production["qualification_policy_hash"] == fingerprint(qualification)
        and production["model_package_hash"] == qualification["model_package_hash"] == fingerprint(model)
        == target["model_package_hash"] == source["model_package_hash"]
        and production["code_hash"] == qualification["code_hash"] == spec["code_hash"], "full source/target/law/code binding")
    require(model["schema_version"] == "frozen-affine-dynamics-v1" and model["family"] == "affine-oracle"
        and model["frozen"] is True and model["qualification"] == {"scope": "oracle-fixture", "scientific_qualification": False},
        "declared synthetic law, not scientific qualification")
    exceptions = {"request_id", "seed", "coupling_id", "samples", "chunk_size", "tolerance"}
    require(set(source) == set(target)
        and all(encoded(source[k]) == encoded(target[k]) for k in source if k not in exceptions)
        and all(source[k] != target[k] for k in ("request_id", "seed", "coupling_id")), "same physical law but distinct frozen streams")
    method = qualification["method"]
    require(type(method) is str and method in METHODS
        and type(qualification["proposal"]) is list and len(qualification["proposal"]) == 2
        and all(finite(v) for v in qualification["proposal"])
        and (method == "importance" and target["functional"] == "endpoint-halfspace"
            or method != "importance" and qualification["proposal"] == [0., 0.])
        and type(qualification["state_scales"]) is list and len(qualification["state_scales"]) == 4
        and all(finite(v, positive=True) for v in qualification["state_scales"]), "explicit solver/proposal/physical scales")
    caps = ("maximum_reference_width", "maximum_observed_grid_error", "maximum_time_bias",
        "maximum_total_observed_functional_error", "maximum_sampling_uncertainty", "minimum_effective_sample_size",
        "maximum_scaled_transition_norm", "maximum_job_seconds")
    require(all(finite(qualification[k], positive=True) for k in caps)
        and qualification["maximum_job_seconds"] <= 1800
        and finite(production["maximum_job_seconds"], positive=True) and production["maximum_job_seconds"] <= 7200
        and type(qualification["maximum_reference_operations"]) is int
        and 1 <= qualification["maximum_reference_operations"] <= 400001
        and 2 <= qualification["minimum_effective_sample_size"] <= min(source["samples"], target["samples"])
        and qualification["maximum_total_observed_functional_error"] <= min(source["tolerance"], target["tolerance"])
        and source["samples"]*source["steps"]+400001 <= 1000000
        and target["samples"]*target["steps"] <= 1000000, "frozen bounded caps/work")
    arms = [a for a in spec["arms"] if a["arm_id"] == target["arm_id"]]
    require(cell["path_qualification_policy"] == source_cell["path_qualification_policy"] == qualification
        and cell["path_production_policy"] == production and cell["plugin_id"] == PLUGIN_ID
        and cell["execution_role"] == "production" and target["arm_id"] == cell["arm_id"]
        and len(arms) == 1 and arms[0]["method_family_id"] == method, "explicit original-arm policies")
    return target, source


def configuration(request, q, p=None):
    work = request["samples"]*request["steps"]
    config = {"method": q["method"], "samples": request["samples"], "base_steps": request["steps"],
        "steps": request["steps"], "chunk_size": request["chunk_size"], "level_samples": [],
        "proposal": q["proposal"], "work_steps": work if p else work+400001,
        "qualification_policy_hash": fingerprint(q)}
    if p:
        config["production_policy_hash"] = fingerprint(p)
    return config


def saved_certificate(document, q, request, *, discrete=False):
    bounded(document, 128*1024, nodes=2048, depth_limit=10, string_limit=1235)
    require(document["schema_version"] == ("affine-discrete-certificate-v1" if discrete else "affine-reference-certificate-v1")
        and document["scope"] == ("declared-affine-finite-grid-Gaussian-law" if discrete else "declared-affine-Gaussian-endpoint-law")
        and document["scientific_qualification"] is False and document["status"] == "BOUNDED"
        and document["algorithm"] == ALGORITHM
        and all(document[k] == q[k] for k in ("request_hash", "model_package_hash", "code_hash"))
        and type(document["operations"]) is int and 0 < document["operations"] <= 200000
        and document["units"] == ("m" if request["functional"] == "endpoint-x" else "1"), "saved certificate binding/units")
    size = 8 if discrete and q["method"] == "reversible-heun" else 4
    def vector(values, length):
        require(type(values) is list and len(values) == length, "reference vector dimensions")
        return [interval(v) for v in values]
    def matrix(values, length):
        require(type(values) is list and len(values) == length, "reference matrix dimensions")
        return [vector(row, length) for row in values]
    transition = document["transition_bounds"]
    require(type(transition) is dict and set(transition) == {"F", "offset", "covariance"}, "reference transition fields")
    f = matrix(transition["F"], size)
    matrix(transition["covariance"], size)
    vector(transition["offset"], size)
    vector(document["mean_bounds"], 4)
    matrix(document["covariance_bounds"], 4)
    if discrete:
        require(document["grid"] == {"solver": "euler" if q["method"] == "importance" else q["method"],
            "steps": request["steps"], "time_step": "exact-horizon-rational/steps",
            "noise": "independent-centered-Gaussian-increments", "roundoff_scope": "mathematical-recurrence-only"}
            and type(document["physical_dimension"]) is int and document["physical_dimension"] == 4
            and type(document["auxiliary_dimension"]) is int and document["auxiliary_dimension"] == size-4
            and type(document["compositions"]) is int and 1 <= document["compositions"] <= 26, "declared grid/auxiliary dimensions")
    scales = list(map(Fraction, q["state_scales"]))*(size//4)
    norm = max(sum(max(map(abs, v))*scales[j]/scales[i] for j, v in enumerate(row)) for i, row in enumerate(f))
    return interval(document["functional_bounds"]), norm


def saved_statistics(last, request, q):
    bounded(last, 16384, nodes=256, depth_limit=8)
    require(type(last) is dict and set(last) == {"step", "data_position", "method_state", "rng_state", "chunk_complete"}
        and last["chunk_complete"] is True and type(last["step"]) is int
        and last["step"] == request["samples"]*request["steps"]
        and encoded(last["data_position"]) == encoded({"level": 1, "next_sample": 0}), "complete actual chunk boundary")
    weighted = q["method"] == "importance"
    proposal = q["proposal"] if weighted else []
    method = last["method_state"]
    require(type(method) is dict and set(method) == {"schema_version", "request_hash", "method_hash", "statistics"}
        and method["schema_version"] == "endpoint-chunk-state-v1" and method["request_hash"] == fingerprint(request)
        and method["method_hash"] == fingerprint({"method": METHODS[q["method"]], "counts": [request["samples"]],
            "costs": [request["steps"]], "phase": 0, "proposal": proposal})
        and type(method["statistics"]) is list and len(method["statistics"]) == 1, "full statistic method/request binding")
    rng = last["rng_state"]
    require(type(rng) is dict and set(rng) == {"scheme", "seed", "coupling_id", "phase", "bit_generator", "numpy_version"}
        and rng["scheme"] == "per-sample-seedsequence-v1" and rng["seed"] == request["seed"]
        and type(rng["seed"]) is int and rng["coupling_id"] == request["coupling_id"]
        and type(rng["phase"]) is int and rng["phase"] == 0 and rng["bit_generator"] == "PCG64"
        and type(rng["numpy_version"]) is str and 0 < len(rng["numpy_version"]) <= 64, "saved PRNG identity (not independence theorem)")
    stat = method["statistics"][0]
    keys = {"n", "hits", "log_w", "log_w2", "log_event", "log_event2", "max_log_w"} if weighted else {"n", "hits", "mean", "m2"}
    require(type(stat) is dict and set(stat) == keys and type(stat["n"]) is int and stat["n"] == request["samples"]
        and type(stat["hits"]) is int and 0 <= stat["hits"] <= stat["n"], "actual sample/event counts")
    for key in keys-{"n", "hits"}:
        none = weighted and key in {"log_event", "log_event2"} and stat["hits"] == 0
        require(stat[key] is None if none else finite(stat[key]), "finite sufficient statistics")
    if not weighted:
        require(stat["m2"] >= 0, "nonnegative centered second moment")
    return stat


def sampling(functional, last, request, q):
    bounded(functional, 64*1024, nodes=256, depth_limit=8)
    fk = {"request_hash", "estimator_id", "kind", "estimate", "standard_error", "interval", "interval_kind",
        "sample_count", "error_budget", "status", "diagnostics"}
    require(type(functional) is dict and set(functional) == fk and type(functional["estimate"]) is float
        and finite(functional["estimate"]) and type(functional["sample_count"]) is int
        and functional["request_hash"] == fingerprint(request) and functional["sample_count"] == request["samples"], "actual full functional")
    pairs = functional["diagnostics"]
    require(type(pairs) is list and 0 < len(pairs) <= 8
        and all(type(p) is list and len(p) == 2 and type(p[0]) is str for p in pairs), "unique diagnostic pairs")
    diagnostics = dict(pairs)
    require(len(diagnostics) == len(pairs), "duplicate diagnostics")
    stat = saved_statistics(last, request, q)
    n, hits = stat["n"], stat["hits"]
    weighted = q["method"] == "importance"
    if weighted:
        estimate = math.exp(stat["log_event"]-math.log(n)) if hits else 0.
        second = math.exp(stat["log_event2"]-math.log(n)) if hits else 0.
        se = math.sqrt(max(0., (second-estimate**2)*n/(n-1))/n) if hits else None
        ess = math.exp(2*stat["log_w"]-stat["log_w2"])
        status = "INSUFFICIENT_EVENTS" if not hits else "LOW_ESS" if ess < 2 else "SUCCEEDED"
        limits = [estimate-Z*se, estimate+Z*se] if hits else None
        interval_kind = "iid-weighted-normal-approximation-95" if hits else "unavailable-no-weighted-hits"
        kind, estimator = "weighted", "velocity-drift-is-unnormalized-v1"
        require(encoded(diagnostics) == encoded({"ess": ess, "hits": hits, "self_normalized": False, "proposal": q["proposal"],
            "proposal_hash": fingerprint(q["proposal"]), "log_sum_weights": stat["log_w"],
            "log_sum_squared_weights": stat["log_w2"], "max_log_weight": stat["max_log_w"]}), "unnormalized saved IS diagnostics")
        degenerate = hits == n and q["proposal"] == [0., 0.]
        radius = Z*se if se is not None and se > 0 and not degenerate else None
        evidence_interval, evidence_kind = limits, interval_kind
        coverage = "estimated-only; finite-variance iid weighted normal approximation; no guaranteed coverage"
        if hits and radius is None:
            evidence_interval, evidence_kind = None, "unavailable-degenerate-weighted-event-statistics"
            coverage = "no sampling uncertainty identified from degenerate weighted event statistics; no coverage guarantee"
    else:
        estimate, ess = stat["mean"], None
        se = math.sqrt(stat["m2"]/(n-1)/n)
        limits, interval_kind = [estimate-Z*se, estimate+Z*se], "normal-approximation-95"
        kind, estimator, status = "functional_estimate", METHODS[q["method"]]+"-path-mc-v1", "SUCCEEDED"
        expected_diagnostics = {"hits": hits, "coupling_id": request["coupling_id"],
            "brownian_scheme": "per-sample-seedsequence-v1"}
        if q["method"] == "reversible-heun":
            # Saved float is descriptive, not a stability/accuracy certificate.
            # Do not replay eigensolvers or use it as an approval threshold.
            radius_value = diagnostics["extended_spectral_radius"]
            require(finite(radius_value) and radius_value >= 0, "finite descriptive auxiliary spectral radius")
            expected_diagnostics.update(numerical_state="physical-and-auxiliary-initially-identical",
                noise_scope="constant-additive-only-Ito-Stratonovich-equivalent",
                stability="not-A-stable; no finite-grid scientific qualification",
                drift_evaluations_per_path=request["steps"]+1, extended_spectral_radius=radius_value)
        require(encoded(diagnostics) == encoded(expected_diagnostics), "actual MC stream/event diagnostics")
        if request["functional"] == "endpoint-halfspace" and hits == 0:
            se, limits = None, [0., -math.expm1(math.log(.05)/n)]
            interval_kind = "exact-binomial-one-sided-95"
        evidence_interval, evidence_kind = limits, interval_kind
        if request["functional"] == "endpoint-halfspace" and hits in (0, n):
            radius = -math.expm1(math.log(.05)/n)
            evidence_interval = [0., radius] if hits == 0 else [1.-radius, 1.]
            evidence_kind = "exact-binomial-one-sided-95-formula"
            coverage = "one-sided95 under ideal iid Bernoulli law only; float64 formula/PRNG coverage not certified"
        else:
            radius = Z*se if se > 0 else None
            coverage = "estimated-only; iid normal approximation; no guaranteed coverage"
    require(all(encoded(functional[k]) == encoded(v) for k, v in {"estimate": estimate, "standard_error": se,
        "interval": limits, "interval_kind": interval_kind, "kind": kind, "estimator_id": estimator, "status": status}.items()),
        "actual output recomputed from saved statistics")
    unit = "m" if request["functional"] == "endpoint-x" else "1"
    budget = functional["error_budget"]
    def component(value, estimated_by, status):
        return {"value": value, "units": unit, "estimated_by": estimated_by, "status": status}
    expected = {"reference": component(None, "float64 analytic reference; no certified roundoff bound", "NOT_IDENTIFIABLE"),
        "propagation_approximation": component(0., "constant affine Gaussian model; no nonlinear closure", "IDENTIFIED"),
        "sampling": component(se, "estimator standard error", "ESTIMATED" if se is not None else "NOT_IDENTIFIABLE"),
        "model": component(None, "no observed real dynamics in synthetic recipe", "NOT_IDENTIFIABLE")}
    require(type(budget) is dict and set(budget) == set(expected)|{"time_discretization"}
        and all(encoded(budget[k]) == encoded(v) for k, v in expected.items()), "kernel sampling and unknown component definitions")
    time = budget["time_discretization"]
    require(type(time) is dict and set(time) == {"value", "units", "estimated_by", "status"}
        and finite(time["value"]) and time["units"] == unit and time["status"] == "IDENTIFIED"
        and time["estimated_by"] == "discrete affine Gaussian expectation minus continuous reference", "kernel time definition")
    return {"status": "ESTIMATED" if radius is not None else "NOT_IDENTIFIABLE", "standard_error": se,
        "uncertainty_radius": radius, "interval": evidence_interval, "interval_kind": evidence_kind, "coverage_scope": coverage,
        "sample_count": n, "hits": hits, "effective_sample_size": ess, "self_normalized": False if weighted else None,
        "zero_observed_variance_is_not_a_zero_error_certificate": True}


def analysis_values(analysis, q, request, functional, cm, tm, *, target=False, production=None, evidence=None):
    bounded(analysis, 512*1024)
    sealed(analysis, "analysis_hash")
    sample = sampling(functional, analysis["completed_statistics"], request, q)
    cb, cn = saved_certificate(cm, q, evidence["source_run"]["cell"]["propagation_request"] if target else request)
    tb, tn = saved_certificate(tm, q, evidence["source_run"]["cell"]["propagation_request"] if target else request, discrete=True)
    value = Fraction(functional["estimate"])
    grid_error, total = (max(abs(value-v) for v in bounds) for bounds in (tb, cb))
    width, bias, norm = max(cb[1]-cb[0], tb[1]-tb[0]), (tb[0]-cb[1], tb[1]-cb[0]), max(cn, tn)
    absolute_bias, operations = max(map(abs, bias)), cm["operations"]+tm["operations"]+1
    checks = {"resolved_reference": True, "sampler_status": functional["status"] == "SUCCEEDED",
        "sampling_uncertainty": sample["uncertainty_radius"] is not None and sample["uncertainty_radius"] <= q["maximum_sampling_uncertainty"],
        "effective_sample_size": q["method"] != "importance" or sample["effective_sample_size"] >= q["minimum_effective_sample_size"],
        "reference_width": width <= Fraction(q["maximum_reference_width"]),
        "observed_grid_error": grid_error <= Fraction(q["maximum_observed_grid_error"]),
        "time_bias": absolute_bias <= Fraction(q["maximum_time_bias"]),
        "total_observed_functional_error": total <= Fraction(q["maximum_total_observed_functional_error"]),
        "scaled_transition_growth": norm <= Fraction(q["maximum_scaled_transition_norm"]),
        "reference_operations": operations <= q["maximum_reference_operations"]}
    unknown = {"value": None, "status": "NOT_IDENTIFIABLE"}
    expected = {"schema_version": "affine-path-functional-qualification-analysis-v1",
        "scope": "one-realized-path-estimate-vs-declared-affine-continuous-and-finite-grid-functional",
        "status": "PASSED" if all(checks.values()) else "FAILED", "scientific_qualification": False,
        "code_hash": q["code_hash"], "request_hash": fingerprint(request), "model_package_hash": q["model_package_hash"],
        "policy_hash": fingerprint(q), "method": q["method"], "proposal": q["proposal"], "proposal_hash": fingerprint(q["proposal"]),
        "actual_functional_hash": fingerprint(functional), "actual_estimate": functional["estimate"],
        "completed_statistics": analysis["completed_statistics"], "completed_statistics_hash": fingerprint(analysis["completed_statistics"]),
        "target_grid": {"solver": "euler" if q["method"] == "importance" else q["method"], "steps": request["steps"]},
        "checks": checks, "physical_dimension": 4, "auxiliary_dimension": 4 if q["method"] == "reversible-heun" else 0,
        "reference_width_upper": outward(width), "observed_grid_error_upper": outward(grid_error),
        "observed_grid_error_scope": "realized-sampling-and-implementation-roundoff-inseparable",
        "implementation_roundoff": unknown, "propagation_approximation": {"value": None, "status": "NOT_SEPARATELY_IDENTIFIABLE"},
        "signed_time_bias_bounds": [[str(v.numerator), str(v.denominator)] for v in bias],
        "absolute_time_bias_upper": outward(absolute_bias), "total_observed_functional_error_upper": outward(total),
        "total_observed_error_scope": "actual scalar distance; not a stochastic coverage or predictive-distribution bound",
        "scaled_transition_norm_upper": outward(norm),
        "scaled_transition_norm_definition": "max row sum |F_ij| scale_j/scale_i; declared horizon; auxiliaries repeat physical scales",
        "state_scale_units": ["m", "m", "m/s", "m/s"], "reference_operations": operations,
        "path_work_units": request["samples"]*request["steps"], "sampling_error": sample, "model_error": unknown,
        "cost_status": "OWNER_SETTLEMENT_REQUIRED", "maximum_job_seconds": q["maximum_job_seconds"],
        "continuous_certificate_hash": fingerprint(cm), "target_certificate_hash": fingerprint(tm),
        "continuous_certificate": cm, "target_certificate": tm}
    if target:
        expected.update(schema_version="affine-independent-path-output-analysis-v1",
            scope="one-independent-realized-target-with-owner-admitted-saved-affine-law-reference",
            production_policy_hash=fingerprint(production), reference_request_hash=q["request_hash"],
            reference_recomputation="NONE; bounded saved same-law proof reused", reference_operations_scope="settled-source-only",
            maximum_job_seconds=production["maximum_job_seconds"], qualification_evidence_hash=evidence["evidence_hash"],
            qualification_source_attempt_id=evidence["source_attempt"]["attempt_id"], kernel_error_budget=functional["error_budget"])
    require(encoded({k: v for k, v in analysis.items() if k != "analysis_hash"}) == encoded(expected), "all saved numeric/statistical meanings and current classification")
    require(target or expected["status"] == "PASSED", "source must actually pass")
    return expected


def validate_path_qualification(receipt, row):
    try:
        return _validate(receipt, row)
    except (KeyError, TypeError, AttributeError, IndexError, OverflowError, RecursionError) as exc:
        raise ValueError("missing or malformed path qualification evidence") from exc


def _validate(receipt, row):
    bounded(receipt, 8*1024*1024)
    bounded(row, 16*1024*1024, nodes=200000)
    spec, cell, docs = receipt["spec"], receipt["cell"], receipt["documents"]
    evidence = docs["propagation_qualification"]
    bounded(evidence, 2*1024*1024)
    sealed(evidence, "evidence_hash")
    require(evidence["schema_version"] == "managed-affine-independent-path-admission-evidence-v1"
        and evidence["target_spec_hash"] == receipt["spec_hash"] == fingerprint(spec)
        and evidence["target_cell_hash"] == receipt["cell_hash"] == fingerprint(cell)
        and receipt["mode"] == "formal" and receipt["qualification"] == "qualified", "formal owner target identity")
    p, q = evidence["policy"], evidence["qualification_policy"]
    source_cell = evidence["source_run"]["cell"]
    request, source_request = policies(p, q, spec, cell, source_cell)
    require(evidence["target_request_hash"] == fingerprint(request), "current target request")
    pointer = docs["package"]["payload"][PAYLOAD_KEY]
    require(type(pointer) is dict and set(pointer) == {"schema_version", "policy", "qualification_policy", "source_attempt_id",
        "source_artifact_id", "source_authorization_id", "source_authorization_version"}
        and pointer["schema_version"] == "managed-affine-path-qualification-v1"
        and pointer["policy"] == p and pointer["qualification_policy"] == q, "explicit own source pointer")
    prereg = docs["preregistration"]
    for key, frozen in (("path_production_policies", p), ("path_qualification_policies", q)):
        values = prereg[key]
        require(type(values) is list and 0 < len(values) <= 10000 and values.count(frozen) == 1
            and len({fingerprint(v) for v in values}) == len(values), "uniquely frozen policies")
    require(prereg["primary_metrics"] == [METRIC] and evidence["preregistration_hash"] == fingerprint(prereg), "frozen observed metric")
    source = source_chain(evidence, receipt, pointer, q, source_kind="path")
    for owner, owner_cell, config, work, level in (
            (evidence["source_admission"], source_cell, configuration(source_request, q), source_request["samples"]*source_request["steps"]+400001, "restart-only"),
            (receipt, cell, configuration(request, q, p), request["samples"]*request["steps"], "chunk")):
        plan, entry = owner["resource_plan"], owner["registry_entry"]
        sealed(plan, "resource_plan_hash")
        require(encoded(owner_cell["execution"]["config"]) == encoded(config)
            and entry["component_id"] == owner_cell["plugin_id"] and entry["version"] == "1.0.0" and entry["resume_level"] == level
            and plan["registry_entry_hash"] == fingerprint(entry) and owner_cell["execution"]["resource_plan_hash"] == plan["resource_plan_hash"]
            and encoded(plan["counts"]["steps"]) == encoded(work) and plan["counts"]["state_dim"] == 4
            and plan["tensor_bytes"] >= 64*1024*1024, "bounded source/target work and resources")
    sf = source["forecast"]
    source_analysis = sf["path_qualification_analysis"]
    cm, tm = source_analysis["continuous_certificate"], source_analysis["target_certificate"]
    analysis_values(source_analysis, q, source_request, sf["functional"], cm, tm)
    result, metadata = row["result"], row["result_artifact"]
    artifact(result, metadata, spec, cell, resume_level="chunk")
    require(row["artifact_id"] == metadata["artifact_id"] and result["admission_hash"] == receipt["admission_hash"]
        and row["metrics"] == result["metrics"] and row["metric_units"] == result["metric_units"]
        and row["qualification"] == result["qualification"] == "qualified", "current artifact/row binding")
    charges = [e["payload"] for e in row["cost"]["sources"] if e["payload"]["attempt_id"] == row["attempt_id"]]
    require(len(charges) == 1 and charges[0]["settled"] is True and charges[0]["outcome"] == "SUCCEEDED"
        and type(charges[0]["charged_ms"]) is int and type(charges[0]["reserved_ms"]) is int
        and 0 < charges[0]["charged_ms"] <= charges[0]["reserved_ms"] <= Fraction(p["maximum_job_seconds"])*1000, "actual target frozen cost")
    forecast, functional = result["forecast"], result["forecast"]["functional"]
    current = forecast["path_output_analysis"]
    raw = {**functional, "error_budget": current["kernel_error_budget"]}
    expected = analysis_values(current, q, request, raw, cm, tm, target=True, production=p, evidence=evidence)
    require(forecast["current_output_qualification"] == expected["status"]
        and forecast["model_package_hash"] == q["model_package_hash"] and forecast["request_hash"] == fingerprint(request)
        and forecast["horizons"] == request["horizons"], "current independent forecast identity/classification")
    unit = "m" if request["functional"] == "endpoint-x" else "1"
    budget = {**raw["error_budget"],
        "reference": {"value": expected["reference_width_upper"], "units": unit,
            "estimated_by": "outward max of saved continuous and method-specific grid functional interval widths", "status": "BOUNDED"},
        "time_discretization": {"value": expected["absolute_time_bias_upper"], "units": unit,
            "estimated_by": "outward absolute signed grid-minus-continuous expectation bound", "status": "BOUNDED"}}
    require(encoded(functional["error_budget"]) == encoded(budget)
        and encoded(result["metrics"]) == encoded({METRIC: expected["total_observed_functional_error_upper"]})
        and result["metric_units"] == {METRIC: unit}, "current separated errors/observed scalar/units")
    return expected["status"]
