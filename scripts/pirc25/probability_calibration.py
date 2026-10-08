"""Independent bounded reader of paid spatial-probability preparation proofs.

This checks saved intervals, the actual rounded event and native settlement.
It never evaluates an exponential/CDF/inverse CDF, opens a runtime or grants
permission. A trusted transport hash is still required by the calling CLI.
Preparation proof is deliberately separate from a method's qualification.
"""

from fractions import Fraction

if __package__:
    from .analytic_qualification import (ALGORITHM, artifact, bounded, encoded,
        event, finite, fingerprint, interval, outward, sealed, timestamp)
else:
    from analytic_qualification import (ALGORITHM, artifact, bounded, encoded,
        event, finite, fingerprint, interval, outward, sealed, timestamp)


def require(condition, detail):
    if not condition:
        raise ValueError("invalid probability calibration evidence: " + detail)


def same(left, right):
    return fingerprint(left) == fingerprint(right)


def policy_values(policy, model, template, code_hash):
    required = {"schema_version", "source_request_hash", "model_package_hash", "code_hash",
        "target_probability", "maximum_relative_probability_error", "maximum_relative_probability_width",
        "maximum_operations", "maximum_job_seconds"}
    require(type(policy) is dict and set(policy) == required
        and policy["schema_version"] == "affine-halfspace-calibration-policy-v1", "complete policy")
    require(policy["source_request_hash"] == fingerprint(template)
        and policy["model_package_hash"] == fingerprint(model) == template["model_package_hash"]
        and policy["code_hash"] == code_hash, "policy source/model/code binding")
    require(model["schema_version"] == "frozen-affine-dynamics-v1" and model["family"] == "affine-oracle"
        and model["frozen"] is True
        and same(model["qualification"], {"scope": "oracle-fixture", "scientific_qualification": False}),
        "declared synthetic law only")
    require(all(finite(policy[k], positive=True) for k in ("target_probability",
        "maximum_relative_probability_error", "maximum_relative_probability_width", "maximum_job_seconds"))
        and 1e-8 <= policy["target_probability"] <= .1
        and policy["maximum_relative_probability_error"] <= 1
        and policy["maximum_relative_probability_width"] <= 1
        and policy["maximum_job_seconds"] <= 1800
        and type(policy["maximum_operations"]) is int and 1 <= policy["maximum_operations"] <= 200000,
        "original finite policy caps")
    require(template["functional"] == "endpoint-halfspace"
        and finite(template["threshold"]) and template["threshold"] == 0
        and type(template["normal"]) is list and len(template["normal"]) == 4
        and all(finite(v) for v in template["normal"]) and any(template["normal"])
        and template["normal"][2:] == [0., 0.]
        and type(template["horizons"]) is list and len(template["horizons"]) == 1
        and finite(template["horizons"][0], positive=True), "zero-template spatial event")


def certificate(document, *, code_hash, model_hash, request_hash, units):
    bounded(document, 128*1024, nodes=2048, depth_limit=10, string_limit=1235)
    require(set(document) == {"schema_version", "algorithm", "code_hash", "model_package_hash", "request_hash",
        "scope", "scientific_qualification", "status", "doublings", "operations", "units",
        "functional_bounds", "mean_bounds", "covariance_bounds", "transition_bounds"}
        and document["schema_version"] == "affine-reference-certificate-v1"
        and same(document["algorithm"], ALGORITHM)
        and document["scope"] == "declared-affine-Gaussian-endpoint-law"
        and document["scientific_qualification"] is False and document["status"] == "BOUNDED"
        and document["code_hash"] == code_hash and document["model_package_hash"] == model_hash
        and document["request_hash"] == request_hash and document["units"] == units
        and type(document["operations"]) is int and 0 < document["operations"] <= 200000
        and type(document["doublings"]) is int and 0 <= document["doublings"] <= 60,
        "saved certificate identity/quota")
    def vector(values):
        require(type(values) is list and len(values) == 4, "four-state interval vector")
        for value in values:
            interval(value)
    def matrix(values):
        require(type(values) is list and len(values) == 4, "four-state interval matrix")
        for value in values:
            vector(value)
    vector(document["mean_bounds"])
    matrix(document["covariance_bounds"])
    transition = document["transition_bounds"]
    require(set(transition) == {"F", "offset", "covariance"}, "complete saved transition")
    matrix(transition["F"])
    matrix(transition["covariance"])
    vector(transition["offset"])
    return interval(document["functional_bounds"])


def analysis_values(analysis, policy, model, template):
    bounded(analysis, 128*1024, nodes=6000, depth_limit=12, string_limit=1235)
    sealed(analysis, "analysis_hash")
    require(set(analysis) == {"schema_version", "scope", "policy_hash", "policy", "code_hash", "model_package_hash",
        "source_request_hash", "target_probability", "normal", "threshold_units", "threshold", "calibrated_request_hash",
        "scientific_qualification", "method_qualification", "cost_status", "admission_status",
        "maximum_quantile_bisections", "executed_quantile_bisections", "quantile_bounds", "quantile_endpoint_tail_bounds",
        "ideal_threshold_bounds", "normalized_ideal_threshold_bounds", "threshold_scale", "maximum_job_seconds",
        "moment_certificate", "moment_certificate_hash", "projected_mean_bounds", "normalized_projected_variance_bounds",
        "probability_certificate", "probability_certificate_hash", "relative_probability_error_upper",
        "relative_probability_width_upper", "checks", "operation_counts", "reference_arithmetic_operations", "status", "analysis_hash"}
        and analysis["schema_version"] == "affine-halfspace-calibration-analysis-v2"
        and analysis["scope"] == "declared-affine-Gaussian-spatial-endpoint-law-for-one-template"
        and analysis["policy_hash"] == fingerprint(policy) and same(analysis["policy"], policy)
        and all(analysis[k] == policy[k] for k in ("code_hash", "model_package_hash", "source_request_hash"))
        and same(analysis["normal"], template["normal"])
        and finite(analysis["target_probability"]) and analysis["target_probability"] == policy["target_probability"]
        and analysis["threshold_units"] == "m" and analysis["scientific_qualification"] is False
        and analysis["method_qualification"] is False and analysis["admission_status"] == "NOT_ADMITTED"
        and analysis["cost_status"] == "OWNER_SETTLEMENT_REQUIRED"
        and finite(analysis["maximum_job_seconds"]) and analysis["maximum_job_seconds"] == policy["maximum_job_seconds"]
        and analysis["status"] == "PASSED", "complete successful saved analysis, not qualification")
    require(type(analysis["threshold"]) is float and finite(analysis["threshold"]), "actual finite float threshold")
    actual = {**template, "threshold": analysis["threshold"]}
    require(analysis["calibrated_request_hash"] == fingerprint(actual), "actual rounded request")
    cm, pm = analysis["moment_certificate"], analysis["probability_certificate"]
    certificate(cm, code_hash=policy["code_hash"], model_hash=fingerprint(model),
        request_hash=fingerprint({**template, "functional": "endpoint-x"}), units="m")
    probability = certificate(pm, code_hash=policy["code_hash"], model_hash=fingerprint(model),
        request_hash=fingerprint(actual), units="1")
    require(analysis["moment_certificate_hash"] == fingerprint(cm)
        and analysis["probability_certificate_hash"] == fingerprint(pm)
        and same(cm["functional_bounds"], cm["mean_bounds"][0])
        and all(same(cm[k], pm[k]) for k in ("mean_bounds", "covariance_bounds", "transition_bounds", "doublings")),
        "saved component hashes/moment law")
    counts = analysis["operation_counts"]
    require(type(counts) is dict and set(counts) == {"moments", "projection_and_quantile", "actual_threshold_reference"}
        and all(type(v) is int and v > 0 for v in counts.values())
        and counts["moments"] == cm["operations"] and counts["actual_threshold_reference"] == pm["operations"]
        and type(analysis["reference_arithmetic_operations"]) is int
        and sum(counts.values()) == analysis["reference_arithmetic_operations"] <= policy["maximum_operations"],
        "single original operation quota")
    require(type(analysis["maximum_quantile_bisections"]) is int
        and type(analysis["executed_quantile_bisections"]) is int
        and analysis["maximum_quantile_bisections"] == analysis["executed_quantile_bisections"] == 48,
        "fixed quantile search")
    quantile = interval(analysis["quantile_bounds"])
    tails = analysis["quantile_endpoint_tail_bounds"]
    require(type(tails) is list and len(tails) == 2, "two saved quantile endpoints")
    left, right = map(interval, tails)
    target = Fraction(policy["target_probability"])
    require(0 <= quantile[0] < quantile[1] <= 8 and quantile[1]-quantile[0] == Fraction(8, 2**48)
        and 0 <= left[0] <= left[1] <= 1 and 0 <= right[0] <= right[1] <= 1
        and left[0] >= target >= right[1], "saved probability bracket")
    normalized, ideal = interval(analysis["normalized_ideal_threshold_bounds"]), interval(analysis["ideal_threshold_bounds"])
    scale = max(abs(Fraction(v)) for v in template["normal"])
    require(finite(analysis["threshold_scale"]) and Fraction(analysis["threshold_scale"]) == scale, "exact normal scale")
    grid = 1 << 160
    scale_lo = Fraction((scale.numerator*grid)//scale.denominator, grid)
    scale_hi = Fraction(-((-scale.numerator*grid)//scale.denominator), grid)
    products = [x*y for x in normalized for y in (scale_lo, scale_hi)]
    lo, hi = min(products), max(products)
    saved = (Fraction((lo.numerator*grid)//lo.denominator, grid),
        Fraction(-((-hi.numerator*grid)//hi.denominator), grid))
    candidate = (normalized[0]+normalized[1])/2*scale
    require(max(candidate.numerator.bit_length(), candidate.denominator.bit_length()) <= 16384
        and ideal == saved and float(candidate) == analysis["threshold"], "saved normalized candidate and physical envelope")
    interval(analysis["projected_mean_bounds"])
    variance = interval(analysis["normalized_projected_variance_bounds"])
    require(0 <= probability[0] <= probability[1] <= 1, "probability unit interval")
    error = max(abs(v-target) for v in probability)/target
    width = (probability[1]-probability[0])/target
    checks = {"positive_projected_variance": variance[0] > 0, "resolved_probability": True,
        "relative_probability_error": error <= Fraction(policy["maximum_relative_probability_error"]),
        "relative_probability_width": width <= Fraction(policy["maximum_relative_probability_width"])}
    require(same(analysis["checks"], checks) and all(checks.values())
        and type(analysis["relative_probability_error_upper"]) is float
        and type(analysis["relative_probability_width_upper"]) is float
        and analysis["relative_probability_error_upper"] == outward(error)
        and analysis["relative_probability_width_upper"] == outward(width), "recomputed saved-interval diagnostics")
    return actual


def geometry(model, request, causal_hash):
    require(type(request["closed"]) is bool, "typed physical event closure")
    return {"schema_version": "affine-halfspace-geometry-v1", "model_package_hash": fingerprint(model),
        "initial_mean": request["initial_mean"], "initial_covariance": request["initial_covariance"],
        "origin": request["origin"], "history_cutoff": request["history_cutoff"], "horizon": request["horizons"][0],
        "functional": request["functional"], "functional_version": request["functional_version"],
        "normal": request["normal"], "threshold": request["threshold"], "closed": request["closed"],
        "state_order": ["x", "y", "vx", "vy"], "units": ["m", "m", "m/s", "m/s"], "time_unit": "s",
        "coordinate_system": request["region_coordinate_system"], "threshold_units": "m", "causal_input_hash": causal_hash}


def validate_saved_calibration(evidence, pointer, *, consumer_study_id):
    try:
        return _validate_saved(evidence, pointer, consumer_study_id)
    except (KeyError, TypeError, AttributeError, IndexError, OverflowError, RecursionError, ValueError) as exc:
        raise ValueError("missing or malformed probability calibration evidence: " + str(exc)) from exc


def _validate_saved(evidence, pointer, consumer):
    bounded(evidence, 2*1024*1024, nodes=25000, depth_limit=30, string_limit=16384)
    sealed(evidence, "evidence_hash")
    require(set(evidence) == {"schema_version", "consumer_study_id", "policy", "geometry", "geometry_hash",
        "source_attempt", "source_run", "source_artifact", "source_result", "source_admission", "authorization",
        "reservation_event", "worker_event", "stop_event", "settlement_event", "admission_event", "completion_event",
        "source_cost", "scientific_qualification", "method_qualification", "admission_status", "cost_status", "evidence_hash"}
        and evidence["schema_version"] == "managed-affine-halfspace-calibration-evidence-v1"
        and evidence["consumer_study_id"] == consumer and evidence["scientific_qualification"] is False
        and evidence["method_qualification"] is False and evidence["admission_status"] == "NOT_ADMITTED"
        and evidence["cost_status"] == "OWNER_SETTLED", "preparation identity and non-qualification flags")
    bounded(pointer, 8192, nodes=512, depth_limit=8, string_limit=256)
    require(type(pointer) is dict and set(pointer) == {"schema_version", "policy", "source_attempt_id",
        "source_artifact_id", "source_authorization_id", "source_authorization_version"}
        and pointer["schema_version"] == "managed-affine-halfspace-calibration-v1"
        and same(pointer["policy"], evidence["policy"]), "explicit source pointer")
    attempt, run, receipt, result, metadata = (evidence[k] for k in
        ("source_attempt", "source_run", "source_admission", "source_result", "source_artifact"))
    spec, cell = receipt["spec"], run["cell"]
    sealed(run, "run_id")
    sealed(receipt, "admission_hash")
    require(attempt["state"] == "SUCCEEDED" and attempt["error_code"] is None
        and attempt["attempt_id"] == pointer["source_attempt_id"] == receipt["attempt_id"]
        and attempt["run_id"] == run["run_id"] == receipt["run_id"]
        and attempt["artifact_id"] == pointer["source_artifact_id"] == metadata["artifact_id"]
        and attempt["artifact_manifest_hash"] == fingerprint(metadata), "completed source identity")
    require(run["spec_hash"] == receipt["spec_hash"] == fingerprint(spec)
        and run["cell_hash"] == receipt["cell_hash"] == fingerprint(cell)
        and run["study_id"] == spec["study_id"] and same(receipt["cell"], cell)
        and sum(same(c, cell) for c in spec["cells"]) == 1
        and receipt["mode"] == "pilot" and receipt["qualification"] == result["qualification"] == "fixture"
        and result["admission_hash"] == receipt["admission_hash"]
        and cell["plugin_id"] == "affine-halfspace-calibration" and cell["visibility"] == "synthetic",
        "original synthetic pilot, not formal or method source")
    policy, model, template = evidence["policy"], cell["frozen_dynamics"], cell["propagation_request"]
    policy_values(policy, model, template, spec["code_hash"])
    require(same(cell["probability_calibration_policy"], policy), "source registered policy")
    artifact(result, metadata, spec, cell)
    forecast = result["forecast"]
    require(result["source_schema"] == "affine-halfspace-calibration-source-v1"
        and forecast["kind"] == "probability-calibration" and "functional" not in forecast
        and forecast["model_package_hash"] == fingerprint(model)
        and forecast["source_request_hash"] == fingerprint(template)
        and same(forecast["horizons"], template["horizons"]), "actual source output")
    actual = analysis_values(forecast["probability_calibration_analysis"], policy, model, template)
    require(same(result["metrics"], {"reference_arithmetic_operations":
        forecast["probability_calibration_analysis"]["reference_arithmetic_operations"]})
        and result["metric_units"] == {"reference_arithmetic_operations": "operations"}, "actual source work metric")
    grant = evidence["authorization"]
    require(grant["authorization_id"] == pointer["source_authorization_id"]
        and grant.get("version") == pointer["source_authorization_version"]
        and (pointer["source_authorization_version"] is None or
            type(pointer["source_authorization_version"]) is str and 0 < len(pointer["source_authorization_version"]) <= 128)
        and grant["study_id"] == spec["study_id"] and grant["protocol_hash"] == spec["protocol_hash"]
        and (consumer == spec["study_id"] or consumer in grant.get("consumer_study_ids", []))
        and "evaluate" in grant["purposes"] and metadata["visibility"] in grant["visibilities"]
        and set(metadata["block_ids"]) <= set(grant["block_ids"]), "selected source consumer permission")
    timestamp(grant["expires_at"])
    protocol = receipt["documents"]["protocol"]
    blocks = [b for b in protocol["blocks"] if b["block_id"] == cell["block_id"]]
    require(fingerprint(protocol) == spec["protocol_hash"] and protocol["study_id"] == spec["study_id"]
        and len(blocks) == 1 and blocks[0]["split_role"] in {"train", "validation"}, "source never held-out")
    plan, entry = receipt["resource_plan"], receipt["registry_entry"]
    sealed(plan, "resource_plan_hash")
    require(entry["component_id"] == cell["plugin_id"] and plan["registry_entry_hash"] == fingerprint(entry)
        and cell["execution"]["resource_plan_hash"] == plan["resource_plan_hash"]
        and type(plan["counts"]["state_dim"]) is int and plan["counts"]["state_dim"] == 4
        and plan["counts"]["paths"] == 0 and plan["counts"]["steps"] == policy["maximum_operations"]
        and plan["tensor_bytes"] >= 64*1024*1024, "original numerical resource contract")
    keys = ("reservation_event", "worker_event", "stop_event", "settlement_event", "admission_event", "completion_event")
    kinds = ("RESERVE", "WORKER_STARTED", "WORKER_TREE_STOPPED", "SETTLE", "ADMISSION", "ATTEMPT")
    sequences = [event(evidence[k], kind) for k, kind in zip(keys, kinds)]
    reserve, worker, stop, settle, admitted, completed = [evidence[k]["payload"] for k in keys]
    source_id = fingerprint([spec["runtime_binding"]["store_id"], attempt["attempt_id"]])
    require(all(p["attempt_id"] == attempt["attempt_id"] and p["reservation_id"] == source_id
        for p in (reserve, worker, stop, settle))
        and all(same(reserve[k], settle[k]) for k in ("run_id", "study_id", "arm_id", "reserved_ms", "worker_slot"))
        and settle["run_id"] == run["run_id"] and settle["study_id"] == spec["study_id"]
        and settle["arm_id"] == cell["arm_id"] and settle["settled"] is True and settle["outcome"] == "SUCCEEDED"
        and type(settle["charged_ms"]) is int and type(settle["reserved_ms"]) is int
        and type(stop["observed_elapsed_ms"]) is int and type(settle["monotonic_elapsed_ms"]) is int
        and 0 < settle["charged_ms"] == settle["monotonic_elapsed_ms"] == stop["observed_elapsed_ms"]
        <= settle["reserved_ms"] <= Fraction(policy["maximum_job_seconds"])*1000
        and stop["confirmation"] == "native-job-or-process-group-no-running-descendants",
        "settled native measured source cost")
    require(same(admitted, {"attempt_id": attempt["attempt_id"], "run_id": run["run_id"], "admission_hash": receipt["admission_hash"]})
        and same(completed, attempt) and sequences[0] < sequences[1] < sequences[2] < sequences[3] < sequences[5]
        and sequences[4] < sequences[1], "original source event order")
    reads = receipt["input_evidence"]
    require(type(reads) is list and bool(reads), "source completed input read")
    for read in reads:
        sequence = event(read, "READ_COMPLETED")
        value = read["payload"]
        require(value["allowed"] is True and value["attempt_id"] == attempt["attempt_id"]
            and value["run_id"] == run["run_id"] and value["study_id"] == spec["study_id"]
            and value["block_id"] == cell["block_id"] and value["sha256"] == blocks[0]["sha256"]
            and value["protocol_hash"] == spec["protocol_hash"] and sequence < sequences[4], "original source read identity/order")
    if "input_binding" in cell:
        binding = cell["input_binding"]
        sealed(binding, "binding_hash")
        case = binding["case"]
        require(binding["schema_version"] == "propagation-input-binding-v1"
            and binding["qualification"] == "declared-only-not-scientific" and case["source_kind"] == "synthetic-recipe"
            and case["block_id"] == cell["block_id"] and case["instance_id"] == cell["instance_id"]
            and all(same(case[k], template[k]) for k in ("initial_mean", "initial_covariance", "origin", "history_cutoff")),
            "synthetic source law binding, not private-prefix or independence qualification")
        causal = binding["binding_hash"]
    else:
        causal = fingerprint({"schema_version": "declared-affine-initial-law-v1", "model_package_hash": fingerprint(model),
            **{k: template[k] for k in ("initial_mean", "initial_covariance", "origin", "history_cutoff")},
            "provenance": "fixed-synthetic-law-not-source-independence"})
    require(same(evidence["geometry"], geometry(model, actual, causal))
        and evidence["geometry_hash"] == fingerprint(evidence["geometry"]), "actual calibrated physical event")
    cost = {"source_id": source_id, "store_id": spec["runtime_binding"]["store_id"],
        "attempt_id": attempt["attempt_id"], "charged_ms": settle["charged_ms"]}
    require(same(evidence["source_cost"], cost), "original cost identity and amount")
    return {"evidence_hash": evidence["evidence_hash"], "geometry_hash": evidence["geometry_hash"],
        "source_cost": cost, "settlement_hash": evidence["settlement_event"]["hash"]}


def summarize_calibration_sources(verified):
    """Deduplicate validated sources globally, not per consumer/method/seed.

The caller supplies only outputs of validate_saved_calibration. This is a
preparation cost summary, not a cell-error aggregate or independent n.
"""
    require(type(verified) is list and len(verified) <= 10000, "bounded verified source list")
    sources = {}
    for item in verified:
        cost = item["source_cost"]
        key = (cost["store_id"], cost["attempt_id"])
        if key in sources:
            require(same(sources[key]["source_cost"], cost)
                and sources[key]["settlement_hash"] == item["settlement_hash"], "conflicting original source cost")
        else:
            sources[key] = item
    return {"unit": "slot-ms", "scope": "unique-verified-calibration-attempts-not-per-cell-or-seed",
        "charged_ms": sum(item["source_cost"]["charged_ms"] for item in sources.values()) if sources else None,
        "unique_sources": len(sources), "source_costs": [item["source_cost"] for item in sources.values()]}


def validate_calibrated_admission(receipt, row):
    """Additional check only; existing formal method qualification still runs."""
    try:
        spec, cell, docs = receipt["spec"], receipt["cell"], receipt["documents"]
        axes = spec.get("propagation_design", {}).get("axis_manifest", {})
        functionals = axes.get("functionals", [])
        bounded(functionals, 65536, nodes=10000, depth_limit=10, string_limit=256)
        declared = any(f.get("functional_id") == cell.get("functional_id")
            and f.get("target_probability") is not None for f in functionals)
        if not declared and "calibration_binding" not in cell and "probability_calibration" not in docs:
            return None
        require(declared and "calibration_binding" in cell and "probability_calibration" in docs,
            "stripped or orphan calibration proof")
        table = axes["calibrations"]
        bounded(table, 32*1024*1024, nodes=2000000, depth_limit=30, string_limit=16384)
        prereg = docs["preregistration"]
        require(type(table) is list and 0 < len(table) <= 10000
            and same(table, prereg["probability_calibration_bindings"])
            and prereg["probability_calibration_bindings_hash"] == fingerprint(table), "full frozen preregistration table")
        entry = cell["calibration_binding"]
        sealed(entry, "binding_hash")
        require(sum(same(entry, item) for item in table) == 1 and entry["status"] == "CALIBRATED"
            and entry["consumer_study_id"] == spec["study_id"], "unique calibrated table binding")
        proof = docs["probability_calibration"]
        verified = validate_saved_calibration(proof, entry["source_pointer"], consumer_study_id=spec["study_id"])
        require(entry["source_evidence_hash"] == verified["evidence_hash"]
            and entry["geometry_hash"] == verified["geometry_hash"] and same(entry["geometry"], proof["geometry"])
            and same(spec["runtime_binding"], proof["source_admission"]["spec"]["runtime_binding"])
            and spec["code_hash"] == proof["policy"]["code_hash"], "same source/root/code/region")
        grant = proof["authorization"]
        require({"evaluate", "export"} <= set(grant["purposes"])
            and timestamp(receipt["admitted_at"]) < timestamp(grant["expires_at"]), "source evaluate/export permission at target admission")
        require(all(proof["completion_event"]["sequence"] < read["sequence"] for read in receipt["input_evidence"]),
            "calibration completed before target exposure")
        request, model = cell["propagation_request"], cell["frozen_dynamics"]
        require(same(geometry(model, request, proof["geometry"]["causal_input_hash"]), proof["geometry"]),
            "target mathematical law and physical event, not data permission")
        result = row["result"]
        artifact(result, row["result_artifact"], spec, cell, resume_level=result["resume_level"])
        forecast = result["forecast"]
        require(forecast["model_package_hash"] == fingerprint(model) and forecast["request_hash"] == fingerprint(request)
            and same(forecast["horizons"], request["horizons"]), "actual target output geometry binding")
        return verified
    except (KeyError, TypeError, AttributeError, IndexError, OverflowError, RecursionError, ValueError) as exc:
        raise ValueError("missing or malformed probability calibration admission: " + str(exc)) from exc
