"""Independent, bounded stdlib reader of managed affine analytic receipts.

The trusted expected bundle hash is essential. This checks saved enclosures,
bindings, recorded worker/cost order and current output, not the truth of an
arbitrary self-rehashed journal. No runtime, raw inputs, matrix/CDF replay,
store, grants, execution or scientific/model qualification is created here.
"""

from datetime import datetime
from fractions import Fraction
import hashlib
import json
import math


METRIC = "absolute_error_upper_vs_declared_affine_law"
ALGORITHM = {"id": "dyadic-affine-enclosure-v1", "fraction_bits": 160,
    "integer_bits": 4096, "temporary_bits": 16384, "operations": 200_000,
    "certificate_bytes": 128*1024, "taylor_terms": 32, "doublings": 60,
    "cdf_terms": 256, "arctan_terms": 40}


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False).encode()


def fingerprint(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def require(condition, detail):
    if not condition:
        raise ValueError("invalid admission evidence: analytic qualification " + detail)


def bounded(document, byte_limit, *, nodes=100_000, depth_limit=32, string_limit=65536):
    remaining = nodes
    def visit(value, depth):
        nonlocal remaining
        remaining -= 1
        require(remaining >= 0 and depth <= depth_limit, "structural quota")
        if type(value) is dict:
            require(len(value) <= remaining and all(type(k) is str and len(k) <= 128 for k in value), "object quota")
            for child in value.values():
                visit(child, depth+1)
        elif type(value) is list:
            require(len(value) <= remaining, "array quota")
            for child in value:
                visit(child, depth+1)
        elif type(value) is str:
            require(len(value) <= string_limit, "string quota")
        else:
            require(type(value) in (int, float, bool, type(None)), "JSON scalar")
            if type(value) is int:
                require(value.bit_length() <= 4096, "integer quota")
            if type(value) is float:
                require(math.isfinite(value), "finite scalar")
    visit(document, 0)
    require(len(encoded(document)) <= byte_limit, "byte quota")


def interval(document):
    require(type(document) is list and len(document) == 2, "interval shape")
    result = []
    for pair in document:
        require(type(pair) is list and len(pair) == 2
            and all(type(v) is str and 0 < len(v) <= 1235 for v in pair), "rational quota/shape")
        numerator, denominator = map(int, pair)
        require(pair == [str(numerator), str(denominator)] and 0 < denominator <= 1 << 160
            and not denominator & (denominator-1) and numerator.bit_length() <= 4096, "canonical dyadic rational")
        value = Fraction(numerator, denominator)
        require(pair == [str(value.numerator), str(value.denominator)], "reduced rational")
        result.append(value)
    require(result[0] <= result[1], "ordered interval")
    return tuple(result)


def outward(value):
    result = float(value)
    require(math.isfinite(result), "finite outward value")
    if Fraction(result) < value:
        result = math.nextafter(result, math.inf)
    require(math.isfinite(result), "finite rounded upper bound")
    return result


def finite(value, *, positive=False):
    return type(value) in (int, float) and math.isfinite(value) and (not positive or value > 0)


def sealed(document, key):
    require(document[key] == fingerprint({k: v for k, v in document.items() if k != key}), key + " content binding")


def event(document, kind):
    sealed(document, "hash")
    require(document["event_kind"] == kind and type(document["sequence"]) is int
        and document["sequence"] > 0, "event kind/sequence")
    timestamp(document["created_at"])
    return document["sequence"]


def timestamp(value):
    result = datetime.fromisoformat(value)
    require(result.tzinfo is not None and result.utcoffset() is not None, "aware timestamp")
    return result


def artifact(result, metadata, spec, cell, *, resume_level="restart-only"):
    bounded(result, 512*1024)
    require(metadata["artifact_id"] == metadata["sha256"] == fingerprint(result)
        and type(metadata["size_bytes"]) is int and metadata["size_bytes"] == len(encoded(result))
        and metadata["study_id"] == spec["study_id"] and metadata["block_ids"] == [cell["block_id"]]
        and metadata["role"] == "result" and metadata["media_type"] == "application/json", "actual result artifact")
    require(result["schema_version"] == "pirc25-result-v1" and result["status"] == "SUCCEEDED"
        and result["spec_hash"] == fingerprint(spec) and result["cell_hash"] == fingerprint(cell)
        and result["protocol_hash"] == spec["protocol_hash"] and result["input_hash"] == spec["data_hash"]
        and result["state_order"] == ["x", "y", "vx", "vy"] and result["units"] == ["m", "m", "m/s", "m/s"]
        and result["time_unit"] == "s" and result["resume_level"] == resume_level, "result input/schema")
    require(result["output_hash"] == fingerprint({k: result[k] for k in ("metrics", "forecast", "fit", "source_schema")}),
        "actual output content hash")


def policy_values(policy, spec, cell):
    required = {"schema_version", "request_hash", "model_package_hash", "code_hash", "method",
        "maximum_reference_width", "maximum_functional_roundoff", "maximum_time_bias",
        "maximum_scaled_transition_norm", "state_scales", "maximum_operations", "maximum_job_seconds"}
    require(type(policy) is dict and set(policy) == required and policy["schema_version"] == "affine-analytic-qualification-policy-v1",
        "complete frozen policy")
    request, model = cell["propagation_request"], cell["frozen_dynamics"]
    method = cell["execution"]["config"]["method"]
    require(cell["plugin_id"] == "affine-propagation" and method in {"exact", "gaussian"}
        and policy["method"] == method and policy["request_hash"] == fingerprint(request)
        and policy["model_package_hash"] == fingerprint(model) == request["model_package_hash"]
        and policy["code_hash"] == spec["code_hash"], "policy source/model/request/method")
    require(model["schema_version"] == "frozen-affine-dynamics-v1" and model["family"] == "affine-oracle"
        and model["frozen"] is True and model["qualification"] == {"scope": "oracle-fixture", "scientific_qualification": False},
        "declared synthetic law, not scientific model qualification")
    require(all(finite(policy[k], positive=True) for k in ("maximum_reference_width", "maximum_functional_roundoff",
        "maximum_time_bias", "maximum_scaled_transition_norm", "maximum_job_seconds"))
        and policy["maximum_job_seconds"] <= 1800
        and type(policy["maximum_operations"]) is int and 1 <= policy["maximum_operations"] <= 400_001
        and type(policy["state_scales"]) is list and len(policy["state_scales"]) == 4
        and all(finite(v, positive=True) for v in policy["state_scales"]), "frozen finite policy caps")
    require(type(request["steps"]) is int and 1 <= request["steps"] <= 8192
        and request["functional"] in {"endpoint-x", "endpoint-halfspace"}
        and request["arm_id"] == cell["arm_id"], "supported endpoint grid/family")
    return request, method


def certificate(document, policy, *, discrete=False, request=None):
    bounded(document, 128*1024, nodes=2048, depth_limit=10, string_limit=1235)
    require(document["schema_version"] == ("affine-discrete-certificate-v1" if discrete else "affine-reference-certificate-v1")
        and document["scope"] == ("declared-affine-finite-grid-Gaussian-law" if discrete else "declared-affine-Gaussian-endpoint-law")
        and document["scientific_qualification"] is False and document["status"] == "BOUNDED"
        and document["algorithm"] == ALGORITHM
        and all(document[k] == policy[k] for k in ("request_hash", "model_package_hash", "code_hash"))
        and type(document["operations"]) is int and 0 < document["operations"] <= 200_000, "bounded component certificate")
    if discrete:
        require(document["grid"] == {"solver": "euler", "steps": request["steps"],
            "time_step": "exact-horizon-rational/steps", "noise": "independent-centered-Gaussian-increments",
            "roundoff_scope": "mathematical-recurrence-only"}, "finite Euler grid")
    matrix = document["transition_bounds"]["F"]
    require(type(matrix) is list and len(matrix) == 4
        and all(type(row) is list and len(row) == 4 for row in matrix), "physical transition shape")
    scales = list(map(Fraction, policy["state_scales"]))
    norm = max(sum(max(map(abs, interval(v)))*scales[j]/scales[i] for j, v in enumerate(row))
        for i, row in enumerate(matrix))
    return interval(document["functional_bounds"]), norm


def analysis_values(analysis, policy, request, method, estimate):
    sealed(analysis, "analysis_hash")
    require(analysis["schema_version"] == "affine-analytic-qualification-analysis-v1"
        and analysis["scientific_qualification"] is False and analysis["policy_hash"] == fingerprint(policy)
        and analysis["method"] == method
        and all(analysis[k] == policy[k] for k in ("code_hash", "request_hash", "model_package_hash")), "analysis frozen identity")
    cm = analysis["continuous_certificate"]
    tm = cm if method == "exact" else analysis["target_certificate"]
    cb, cn = certificate(cm, policy)
    if method == "exact":
        require(analysis["target_certificate"] is None and analysis["target_grid"] is None, "exact target identity")
        tb, tn = cb, cn
    else:
        require(analysis["target_grid"] == {"solver": "euler", "steps": request["steps"]}, "target grid")
        tb, tn = certificate(tm, policy, discrete=True, request=request)
    require(analysis["continuous_certificate_hash"] == fingerprint(cm)
        and analysis["target_certificate_hash"] == fingerprint(tm), "component hashes")
    bias = interval(analysis["signed_time_bias_bounds"])
    require(bias == ((Fraction(0), Fraction(0)) if method == "exact" else (tb[0]-cb[1], tb[1]-cb[0])), "signed grid bias")
    width, error = cb[1]-cb[0], max(abs(Fraction(estimate)-v) for v in tb)
    absolute_bias, norm = max(map(abs, bias)), max(cn, tn)
    operations = cm["operations"]+(tm["operations"] if method != "exact" else 0)+1
    checks = {"resolved_reference": True, "reference_width": width <= Fraction(policy["maximum_reference_width"]),
        "functional_roundoff": error <= Fraction(policy["maximum_functional_roundoff"]),
        "time_bias": absolute_bias <= Fraction(policy["maximum_time_bias"]),
        "scaled_transition_growth": norm <= Fraction(policy["maximum_scaled_transition_norm"]),
        "arithmetic_operations": operations <= policy["maximum_operations"]}
    require(analysis["status"] == "PASSED" and analysis["checks"] == checks
        and all(type(v) is bool for v in analysis["checks"].values()) and all(checks.values()), "actual numerical checks")
    expected = {"reference_width_upper": outward(width), "functional_roundoff_upper": outward(error),
        "absolute_time_bias_upper": outward(absolute_bias), "scaled_transition_norm_upper": outward(norm),
        "operations": operations, "sampling_error": {"status": "NOT_APPLICABLE", "value": 0},
        "model_error": {"status": "NOT_IDENTIFIABLE", "value": None}, "cost_status": "OWNER_SETTLEMENT_REQUIRED",
        "maximum_job_seconds": policy["maximum_job_seconds"]}
    require(all(analysis.get(k) == v for k, v in expected.items()), "recomputed saved-enclosure values")
    return cb, tb, bias


def source_chain(evidence, receipt, pointer, policy, *, source_kind="analytic"):
    attempt, run, result = (evidence[k] for k in ("source_attempt", "source_run", "source_result"))
    admission, metadata, spec, cell = (evidence["source_admission"], evidence["source_artifact"],
        evidence["source_admission"]["spec"], evidence["source_run"]["cell"])
    target_spec, target_cell = receipt["spec"], receipt["cell"]
    sealed(run, "run_id")
    sealed(admission, "admission_hash")
    require(attempt["state"] == "SUCCEEDED" and attempt["error_code"] is None
        and attempt["attempt_id"] == pointer["source_attempt_id"] == admission["attempt_id"]
        and attempt["run_id"] == run["run_id"] == admission["run_id"]
        and attempt["artifact_id"] == pointer["source_artifact_id"] == metadata["artifact_id"]
        and attempt["artifact_manifest_hash"] == fingerprint(metadata), "completed source identity")
    require(run["spec_hash"] == admission["spec_hash"] == fingerprint(spec)
        and run["cell_hash"] == admission["cell_hash"] == fingerprint(cell)
        and run["study_id"] == spec["study_id"] and admission["cell"] == cell and cell in spec["cells"]
        and admission["mode"] == "pilot" and admission["qualification"] == result["qualification"] == "fixture"
        and result["admission_hash"] == admission["admission_hash"], "source pilot receipt/result")
    require(source_kind in {"analytic", "mlmc", "mixture", "path", "cubature"}, "explicit source kind")
    require(spec["runtime_binding"] == target_spec["runtime_binding"] and spec["code_hash"] == target_spec["code_hash"]
        and cell["arm_id"] == target_cell["arm_id"] and cell["frozen_dynamics"] == target_cell["frozen_dynamics"],
        "same source/model/arm/root")
    if source_kind == "analytic":
        require(cell["plugin_id"] == "affine-propagation-qualification" and cell["execution_role"] == "qualification"
            and cell["propagation_request"] == target_cell["propagation_request"] and cell["affine_qualification_policy"] == policy
            and cell["execution"]["config"]["method"] == policy["method"], "analytic source/request/policy")
    elif source_kind == "cubature":
        require(cell["plugin_id"] == "affine-cubature-qualification" and cell["execution_role"] == "qualification"
            and cell["propagation_request"] == target_cell["propagation_request"]
            and cell["cubature_qualification_policy"] == policy
            and cell["execution"]["config"]["method"] == "cubature"
            and cell["execution"]["config"]["qualification_policy_hash"] == fingerprint(policy)
            and cell["execution"]["config"]["work_steps"] == 16*cell["propagation_request"]["steps"]+policy["maximum_operations"],
            "own cubature source/request/policy/resource work")
    elif source_kind == "mlmc":
        require(cell["plugin_id"] == "affine-mlmc-qualification-chunk" and cell["execution_role"] == "pilot"
            and cell["affine_mlmc_reference_policy"] == policy
            and cell["execution"]["config"]["method"] == "mlmc-pilot", "MLMC source pilot/policy")
    elif source_kind == "path":
        require(cell["plugin_id"] == "affine-path-qualification" and cell["execution_role"] == "qualification"
            and cell["path_qualification_policy"] == policy
            and cell["execution"]["config"]["method"] == policy["method"], "own path source/policy")
    else:
        require(cell["plugin_id"] == "affine-mixture-qualification" and cell["execution_role"] == "qualification"
            and cell["propagation_request"] == target_cell["propagation_request"]
            and cell["mixture_policy"] == target_cell["mixture_policy"]
            and cell["mixture_qualification_policy"] == policy
            and cell["execution"]["config"]["method"] == "mixture", "mixture source/request/policies")
    def arm(registered):
        rows = [a for a in registered["arms"] if a["arm_id"] == cell["arm_id"]]
        require(len(rows) == 1, "unique original family arm")
        return rows[0]
    require(arm(spec) == arm(target_spec), "same cumulative arm family")
    artifact(result, metadata, spec, cell, resume_level="chunk" if source_kind == "mlmc" else "restart-only")
    grant = evidence["authorization"]
    require(grant["authorization_id"] == pointer["source_authorization_id"]
        and grant.get("version") == pointer["source_authorization_version"]
        and grant["study_id"] == spec["study_id"] and grant["protocol_hash"] == spec["protocol_hash"]
        and (spec["study_id"] == target_spec["study_id"] or target_spec["study_id"] in grant.get("consumer_study_ids", []))
        and {"evaluate", "export"} <= set(grant["purposes"])
        and metadata["visibility"] in grant["visibilities"] and set(metadata["block_ids"]) <= set(grant["block_ids"])
        and timestamp(receipt["admitted_at"]) < timestamp(grant["expires_at"]), "source evaluate/export consumer permission")
    protocol = admission["documents"]["protocol"]
    blocks = [b for b in protocol["blocks"] if b["block_id"] == cell["block_id"]]
    require(fingerprint(protocol) == spec["protocol_hash"] and protocol["study_id"] == spec["study_id"]
        and len(blocks) == 1 and blocks[0]["split_role"] in {"train", "validation"}, "source never held-out input")
    plan, entry = admission["resource_plan"], admission["registry_entry"]
    sealed(plan, "resource_plan_hash")
    require(entry["component_id"] == cell["plugin_id"] and plan["registry_entry_hash"] == fingerprint(entry)
        and cell["execution"]["resource_plan_hash"] == plan["resource_plan_hash"]
        and plan["counts"]["state_dim"] == 4 and plan["tensor_bytes"] >= 64*1024*1024, "source numerical resource contract")
    events = [evidence[k] for k in ("reservation_event", "worker_event", "stop_event", "settlement_event",
        "admission_event", "completion_event")]
    sequences = [event(e, k) for e, k in zip(events, ("RESERVE", "WORKER_STARTED", "WORKER_TREE_STOPPED", "SETTLE", "ADMISSION", "ATTEMPT"))]
    reserve, worker, stop, settle, admitted, completed = [e["payload"] for e in events]
    reservation_id = fingerprint([spec["runtime_binding"]["store_id"], attempt["attempt_id"]])
    require(all(e["attempt_id"] == attempt["attempt_id"] for e in (reserve, worker, stop, settle))
        and all(e["reservation_id"] == reservation_id for e in (reserve, worker, stop, settle))
        and all(reserve[k] == settle[k] for k in ("run_id", "study_id", "arm_id", "reserved_ms", "worker_slot"))
        and all(settle[k] == v for k, v in {"run_id": run["run_id"], "study_id": spec["study_id"],
            "arm_id": cell["arm_id"], "settled": True, "outcome": "SUCCEEDED"}.items())
        and type(settle["charged_ms"]) is int and type(settle["reserved_ms"]) is int
        and 0 < settle["charged_ms"] <= settle["reserved_ms"] <= Fraction(policy["maximum_job_seconds"])*1000
        and settle["charged_ms"] == settle["monotonic_elapsed_ms"] == stop["observed_elapsed_ms"]
        and stop["confirmation"] == "native-job-or-process-group-no-running-descendants", "settled measured native worker cost")
    require(admitted == {"attempt_id": attempt["attempt_id"], "run_id": run["run_id"], "admission_hash": admission["admission_hash"]}
        and completed == attempt and sequences[0] < sequences[1] < sequences[2] < sequences[3] < sequences[5]
        and sequences[4] < sequences[1]
        and all(sequences[5] < read["sequence"] for read in receipt["input_evidence"]), "source completed before held-out exposure")
    reads = admission["input_evidence"]
    require(bool(reads), "source completed training read")
    for read in reads:
        sequence = event(read, "READ_COMPLETED")
        value = read["payload"]
        require(value["allowed"] is True and value["attempt_id"] == attempt["attempt_id"]
            and value["run_id"] == run["run_id"] and value["study_id"] == spec["study_id"]
            and value["block_id"] == cell["block_id"] and value["sha256"] == blocks[0]["sha256"]
            and value["protocol_hash"] == spec["protocol_hash"] and sequence < sequences[4], "source read binding/order")
    return result


def validate_analytic_qualification(receipt, row):
    try:
        _validate(receipt, row)
    except (KeyError, TypeError, AttributeError, IndexError, OverflowError, RecursionError) as exc:
        raise ValueError("missing or malformed analytic qualification evidence") from exc


def _validate(receipt, row):
    spec, cell, docs = receipt["spec"], receipt["cell"], receipt["documents"]
    evidence = docs["propagation_qualification"]
    bounded(evidence, 2*1024*1024)
    sealed(evidence, "evidence_hash")
    require(evidence["schema_version"] == "managed-affine-analytic-admission-evidence-v1"
        and evidence["target_spec_hash"] == receipt["spec_hash"] and evidence["target_cell_hash"] == receipt["cell_hash"],
        "evidence target identity")
    pointer = docs["package"]["payload"]["managed_analytic_qualification"]
    require(type(pointer) is dict and set(pointer) == {"schema_version", "policy", "source_attempt_id",
        "source_artifact_id", "source_authorization_id", "source_authorization_version"}
        and pointer["schema_version"] == "managed-affine-analytic-qualification-v1"
        and pointer["policy"] == evidence["policy"], "explicit frozen source pointer")
    policy = evidence["policy"]
    request, method = policy_values(policy, spec, cell)
    prereg = docs["preregistration"]
    policies = prereg["propagation_qualification_policies"]
    require(type(policies) is list and 0 < len(policies) <= 10000 and policies.count(policy) == 1
        and len({fingerprint(p) for p in policies}) == len(policies) and prereg["primary_metrics"] == [METRIC]
        and evidence["preregistration_hash"] == fingerprint(prereg), "frozen policy and primary metric")
    source = source_chain(evidence, receipt, pointer, policy)
    analysis = source["forecast"]["qualification_analysis"]
    original = source["forecast"]["functional"]["estimate"]
    require(finite(original), "finite original analytic scalar")
    cb, tb, bias = analysis_values(analysis, policy, request, method, original)
    result, metadata = row["result"], row["result_artifact"]
    artifact(result, metadata, spec, cell)
    require(row["artifact_id"] == metadata["artifact_id"] and result["admission_hash"] == receipt["admission_hash"]
        and row["metrics"] == result["metrics"] and row["metric_units"] == result["metric_units"]
        and row["qualification"] == result["qualification"] == "qualified", "target row/artifact/admission")
    functional, forecast = result["forecast"]["functional"], result["forecast"]
    estimate = functional["estimate"]
    require(finite(estimate) and functional["kind"] == forecast["kind"] == "analytic"
        and functional["request_hash"] == forecast["request_hash"] == fingerprint(request)
        and functional["estimator_id"] == ("affine-exact-v1" if method == "exact" else "gaussian-discrete-v1")
        and functional["sample_count"] == 0 and functional["standard_error"] == 0
        and forecast["model_package_hash"] == policy["model_package_hash"] and forecast["horizons"] == request["horizons"],
        "current deterministic analytic output")
    roundoff = max(abs(Fraction(estimate)-v) for v in tb)
    require(roundoff <= Fraction(policy["maximum_functional_roundoff"]), "current output roundoff cap")
    components = {"reference_width_upper": outward(cb[1]-cb[0]), "implementation_roundoff_upper": outward(roundoff),
        "time_bias_absolute_upper": outward(max(map(abs, bias))), "signed_time_bias_bounds": analysis["signed_time_bias_bounds"],
        "model_error": {"value": None, "status": "NOT_IDENTIFIABLE"}, "scope": "declared-affine-law-only",
        "qualification_evidence_hash": evidence["evidence_hash"],
        "qualification_source_attempt_id": evidence["source_attempt"]["attempt_id"], "policy_hash": fingerprint(policy)}
    unit = "m" if request["functional"] == "endpoint-x" else "1"
    require(result["metrics"] == {METRIC: outward(max(abs(Fraction(estimate)-v) for v in cb))}
        and result["metric_units"] == {METRIC: unit} and forecast["qualified_error_components"] == components,
        "current error upper and provenance")
    budget = functional["error_budget"]
    for key, value in (("reference", components["reference_width_upper"]), ("time_discretization", components["time_bias_absolute_upper"])):
        require(budget[key]["value"] == value and budget[key]["status"] == "BOUNDED" and budget[key]["units"] == unit,
            "separated bounded error component")
    require(budget["model"]["value"] is None and budget["model"]["status"] == "NOT_IDENTIFIABLE", "unknown model error remains unknown")
