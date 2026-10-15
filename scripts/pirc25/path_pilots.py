"""Stdlib saved pilot verification, not production/scientific admission.

No runtime import, sampler, matrix/CDF replay, threshold change or authority.
An externally trusted owner bundle hash is still required for authenticity.
"""
from fractions import Fraction

if __package__:
    from .analytic_qualification import artifact, bounded, encoded, event, fingerprint, finite, sealed, timestamp
    from .path_qualification import METHODS, configuration, require, _saved_analysis_values
    from .admission_selection import selected_settings
    from .costs import validate_cost
    from .resource_usage import validate_resources
else:
    from analytic_qualification import artifact, bounded, encoded, event, fingerprint, finite, sealed, timestamp
    from path_qualification import METHODS, configuration, require, _saved_analysis_values
    from admission_selection import selected_settings
    from costs import validate_cost
    from resource_usage import validate_resources


def _policy(q, request, model, spec, cell):
    bounded(q, 8192, nodes=100, depth_limit=3)
    bounded(request, 64*1024, nodes=2048, depth_limit=10)
    bounded(model, 64*1024, nodes=2048, depth_limit=10)
    keys = {"schema_version", "request_hash", "model_package_hash", "code_hash", "method", "proposal", "state_scales",
        "maximum_reference_width", "maximum_observed_grid_error", "maximum_time_bias",
        "maximum_total_observed_functional_error", "maximum_sampling_uncertainty", "minimum_effective_sample_size",
        "maximum_scaled_transition_norm", "maximum_reference_operations", "maximum_job_seconds"}
    require(type(q) is dict and set(q) == keys
        and q["schema_version"] == "affine-path-functional-qualification-policy-v1"
        and q["request_hash"] == fingerprint(request) and q["code_hash"] == spec["code_hash"]
        and q["model_package_hash"] == fingerprint(model) == request["model_package_hash"], "pilot policy source binding")
    require(model["schema_version"] == "frozen-affine-dynamics-v1" and model["family"] == "affine-oracle"
        and model["frozen"] is True and model["qualification"] == {"scope": "oracle-fixture", "scientific_qualification": False},
        "synthetic law only")
    require(type(request["samples"]) is int and 2 <= request["samples"] <= 1000000
        and type(request["steps"]) is int and 1 <= request["steps"] <= 8192
        and type(request["chunk_size"]) is int and 1 <= request["chunk_size"] <= 1000000
        and type(request["seed"]) is int and request["seed"] == cell["seed"] >= 0
        and finite(request["tolerance"], positive=True) and request["arm_id"] == cell["arm_id"]
        and request["functional"] in {"endpoint-x", "endpoint-halfspace"}
        and type(request["horizons"]) is list and len(request["horizons"]) == 1
        and finite(request["horizons"][0], positive=True)
        and request["samples"]*request["steps"]+400001 <= 1000000, "bounded pilot endpoint request")
    method = q["method"]
    require(type(method) is str and method in METHODS and type(q["proposal"]) is list and len(q["proposal"]) == 2
        and all(finite(v) for v in q["proposal"])
        and (method == "importance" and request["functional"] == "endpoint-halfspace"
            or method != "importance" and q["proposal"] == [0., 0.])
        and type(q["state_scales"]) is list and len(q["state_scales"]) == 4
        and all(finite(v, positive=True) for v in q["state_scales"]), "pilot solver/proposal/scales")
    caps = ("maximum_reference_width", "maximum_observed_grid_error", "maximum_time_bias",
        "maximum_total_observed_functional_error", "maximum_sampling_uncertainty", "minimum_effective_sample_size",
        "maximum_scaled_transition_norm", "maximum_job_seconds")
    require(all(finite(q[k], positive=True) for k in caps) and q["maximum_job_seconds"] <= 1800
        and 2 <= q["minimum_effective_sample_size"] <= request["samples"]
        and q["maximum_total_observed_functional_error"] <= request["tolerance"]
        and type(q["maximum_reference_operations"]) is int and 1 <= q["maximum_reference_operations"] <= 400001,
        "frozen pilot caps, not a production exception")
    arms = [a for a in spec["arms"] if a["arm_id"] == cell["arm_id"]]
    require(len(arms) == 1 and arms[0]["method_family_id"] == method
        and cell["plugin_id"] == "affine-path-qualification" and cell["execution_role"] == "qualification"
        and cell["visibility"] == "synthetic" and encoded(cell["execution"]["config"]) == encoded(configuration(request, q)),
        "own original-arm pilot config/role")


def _execution(proof, receipt, row, q, spec, cell):
    bounded(proof, 2*1024*1024)
    sealed(proof, "proof_hash")
    keys = ("reservation_event", "worker_event", "stop_event", "settlement_event", "admission_event", "completion_event")
    require(set(proof) == {"schema_version", "proof_hash", "attempt", "run", *keys}
        and proof["schema_version"] == "owned-path-pilot-execution-v1", "complete native pilot proof")
    attempt, run = proof["attempt"], proof["run"]
    sealed(run, "run_id")
    require(attempt["state"] == row["status"] == "SUCCEEDED" and attempt["error_code"] is None
        and attempt["attempt_id"] == row["attempt_id"] == receipt["attempt_id"]
        and attempt["run_id"] == row["run_id"] == receipt["run_id"] == run["run_id"]
        and attempt["artifact_id"] == row["artifact_id"] == row["result_artifact"]["artifact_id"]
        and attempt["artifact_manifest_hash"] == fingerprint(row["result_artifact"])
        and run["spec_hash"] == fingerprint(spec) and run["cell_hash"] == fingerprint(cell)
        and run["cell"] == cell and run["study_id"] == spec["study_id"], "actual completed pilot identity")
    events = [proof[k] for k in keys]
    sequences = [event(e, k) for e, k in zip(events,
        ("RESERVE", "WORKER_STARTED", "WORKER_TREE_STOPPED", "SETTLE", "ADMISSION", "ATTEMPT"))]
    reserve, worker, stop, settle, admitted, completed = [e["payload"] for e in events]
    reservation = fingerprint([spec["runtime_binding"]["store_id"], attempt["attempt_id"]])
    require(all(e["attempt_id"] == attempt["attempt_id"] and e["reservation_id"] == reservation
        for e in (reserve, worker, stop, settle))
        and all(reserve[k] == settle[k] for k in ("run_id", "study_id", "arm_id", "reserved_ms", "worker_slot"))
        and all(settle[k] == v for k, v in {"run_id": run["run_id"], "study_id": spec["study_id"],
            "arm_id": cell["arm_id"], "settled": True, "outcome": "SUCCEEDED"}.items())
        and type(settle["charged_ms"]) is int and type(settle["reserved_ms"]) is int
        and type(settle["monotonic_elapsed_ms"]) is int and type(stop["observed_elapsed_ms"]) is int
        and settle["settled"] is True
        and 0 < settle["charged_ms"] <= settle["reserved_ms"] <= Fraction(q["maximum_job_seconds"])*1000
        and settle["charged_ms"] == settle["monotonic_elapsed_ms"] == stop["observed_elapsed_ms"]
        and stop["confirmation"] == "native-job-or-process-group-no-running-descendants"
        and completed == attempt and admitted == {"attempt_id": attempt["attempt_id"], "run_id": run["run_id"],
            "admission_hash": receipt["admission_hash"]}
        and sequences[0] < sequences[1] < sequences[2] < sequences[3] < sequences[5]
        and sequences[4] < sequences[1], "native whole-stop/settled pilot job")
    charges = [e for e in row["cost"]["sources"] if e["payload"]["attempt_id"] == attempt["attempt_id"]]
    require(charges == [proof["settlement_event"]], "selected cost source matches actual whole-job proof")
    reads = receipt["input_evidence"]
    settings = selected_settings(spec, cell, receipt)
    require(bool(reads), "completed pilot input read")
    for read in reads:
        sequence = event(read, "READ_COMPLETED")
        value = read["payload"]
        grant = receipt["documents"]["authorization"]
        blocks = [b for b in receipt["documents"]["protocol"]["blocks"] if b["block_id"] == cell["block_id"]]
        require(len(blocks) == 1 and value["allowed"] is True and value["attempt_id"] == attempt["attempt_id"]
            and value["run_id"] == run["run_id"] and value["study_id"] == spec["study_id"]
            and value["block_id"] == cell["block_id"] and value["sha256"] == blocks[0]["sha256"]
            and value["protocol_hash"] == spec["protocol_hash"] and value["authorization_id"] == grant["authorization_id"]
            and value["purpose"] == settings["purpose"] and value["purpose"] in grant["purposes"]
            and sequence < sequences[4], "pilot exposure source/order")
        if "version" in grant or "authorization_hash" in value:
            require(value.get("authorization_version") == grant.get("version")
                and value.get("authorization_hash") == fingerprint(grant), "pilot read grant version/hash")


def validate_path_pilot(receipt, row):
    try:
        return _validate(receipt, row)
    except (KeyError, TypeError, AttributeError, IndexError, OverflowError, RecursionError) as exc:
        raise ValueError("missing or malformed saved path pilot evidence") from exc


def _validate(receipt, row):
    bounded(receipt, 8*1024*1024)
    bounded(row, 16*1024*1024, nodes=200000)
    sealed(receipt, "admission_hash")
    spec, cell = receipt["spec"], receipt["cell"]
    require(receipt["spec_hash"] == fingerprint(spec) and receipt["cell_hash"] == fingerprint(cell) == row["cell_hash"]
        and receipt["cell"] == row["registered_cell"] and cell in spec["cells"]
        and receipt["mode"] == "pilot" and receipt["qualification"] == row["qualification"] == "fixture"
        and row["admission_hash"] == receipt["admission_hash"]
        and all(cell[k] == row[k] for k in ("arm_id", "block_id", "seed")), "bound non-admitting pilot receipt")
    request, q, model = cell["propagation_request"], cell["path_qualification_policy"], cell["frozen_dynamics"]
    _policy(q, request, model, spec, cell)
    docs = receipt["documents"]
    protocol, grant, package = docs["protocol"], docs["authorization"], docs["package"]
    settings = selected_settings(spec, cell, receipt)
    blocks = [b for b in protocol["blocks"] if b["block_id"] == cell["block_id"]]
    require(settings["mode"] == "pilot" and len(blocks) == 1 and blocks[0]["split_role"] in {"train", "validation"}
        and settings["purpose"] == {"train": "fit", "validation": "validate"}[blocks[0]["split_role"]]
        and fingerprint(protocol) == spec["protocol_hash"] == package["protocol_hash"] == grant["protocol_hash"]
        and protocol["study_id"] == grant["study_id"] == package["study_id"] == spec["study_id"]
        and fingerprint(package) == settings["package_hash"] and package["code_hash"] == spec["code_hash"]
        and grant["authorization_id"] == settings["authorization_id"]
        and grant.get("version") == settings.get("authorization_version")
        and {"execute", settings["purpose"]} <= set(grant["purposes"])
        and cell["block_id"] in grant["block_ids"] and cell["visibility"] in grant["visibilities"]
        and timestamp(receipt["admitted_at"]) < timestamp(grant["expires_at"]), "pilot input/package/permission, never held-out")
    plan, entry = receipt["resource_plan"], receipt["registry_entry"]
    sealed(plan, "resource_plan_hash")
    require(entry["component_id"] == cell["plugin_id"] and entry["version"] == "1.0.0"
        and entry["resume_level"] == "restart-only" and plan["registry_entry_hash"] == fingerprint(entry)
        and cell["execution"]["resource_plan_hash"] == plan["resource_plan_hash"]
        and plan["counts"]["state_dim"] == 4 and plan["counts"]["steps"] == request["samples"]*request["steps"]+400001
        and plan["tensor_bytes"] >= 64*1024*1024, "bounded original pilot resource contract")
    result, metadata = row["result"], row["result_artifact"]
    artifact(result, metadata, spec, cell)
    require(result["admission_hash"] == receipt["admission_hash"] and result["qualification"] == "fixture"
        and encoded(result["metrics"]) == encoded(row["metrics"])
        and result["metric_units"] == row["metric_units"], "actual pilot artifact/row, no promotion")
    context = {**spec, "registered_spec": spec, "spec_hash": fingerprint(spec)}
    validate_cost(row, context, set())
    validate_resources(row, context)
    _execution(row["path_pilot_execution"], receipt, row, q, spec, cell)
    forecast = result["forecast"]
    require(forecast["model_package_hash"] == q["model_package_hash"]
        and forecast["request_hash"] == fingerprint(request) and forecast["horizons"] == request["horizons"], "actual pilot forecast")
    analysis = forecast["path_qualification_analysis"]
    expected = _saved_analysis_values(analysis, q, request, forecast["functional"],
        analysis["continuous_certificate"], analysis["target_certificate"])
    return expected["status"]
