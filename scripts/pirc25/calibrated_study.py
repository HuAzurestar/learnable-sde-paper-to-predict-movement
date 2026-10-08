"""Independent complete table/source/cost validation, including missing slots.

This reads saved proofs only. It neither computes calibration references nor
turns preparation into method qualification or independent observations.
"""

from itertools import product
from math import ceil

if __package__:
    from .analytic_qualification import artifact, bounded, encoded, event, finite, fingerprint, sealed, timestamp
    from .probability_calibration import geometry, policy_values, same, validate_saved_calibration
    from .costs import validate_cost
    from .calibration_lineage import validate_lineage
else:
    from analytic_qualification import artifact, bounded, encoded, event, finite, fingerprint, sealed, timestamp
    from probability_calibration import geometry, policy_values, same, validate_saved_calibration
    from costs import validate_cost
    from calibration_lineage import validate_lineage


ENTRY_FIELDS = {"schema_version", "functional_id", "model_family_id", "model_package_hash", "horizon",
    "input_case_id", "model_configuration_id", "status", "reason", "geometry", "source_pointer",
    "source_evidence_hash", "consumer_study_id", "geometry_hash", "binding_hash"}
FAILURES = {"FAILED", "INTERRUPTED", "TIMEOUT", "BUDGET_EXHAUSTED", "PREFLIGHT_FAILED", "CANCELLED"}
KINDS = {"RESERVE", "WORKER_STARTED", "WORKER_TREE_STOPPED", "WORKER_STOP_CONFIRMED", "SETTLE", "ADMISSION", "ATTEMPT"}


def require(condition, detail):
    if not condition:
        raise ValueError("invalid complete calibration evidence: " + detail)


def require_original_event_order(events):
    require(type(events) is list and bool(events) and all(type(e) is dict for e in events), "original event array")
    sequences = [e["sequence"] for e in events]
    require(all(type(s) is int and s > 0 for s in sequences)
        and all(left < right for left, right in zip(sequences, sequences[1:])),
        "strict original append order without duplicated events")


def table_values(spec):
    axes = spec["propagation_design"]["axis_manifest"]
    table = axes["calibrations"]
    bounded(axes, 32*1024*1024, nodes=2000000, depth_limit=30, string_limit=16384)
    require(type(table) is list and 0 < len(table) <= 10000
        and axes["state_names"] == ["x", "y", "vx", "vy"], "bounded four-state geometry table")
    for axis in ("models", "functionals", "horizons", "methods", "seeds"):
        require(type(axes[axis]) is list and 0 < len(axes[axis]) <= 64, "bounded nonempty axis")
    cases = axes.get("input_cases", [])
    require(type(cases) is list and len(cases) <= 64, "bounded input cases")
    selected = [f for f in axes["functionals"] if f.get("target_probability") is not None]
    count = len(axes["models"])*len(selected)*len(axes["horizons"])*(len(cases) or 1)
    require(count == len(table), "complete geometry slot cardinality")
    lookup = {}
    slots = product(axes["models"], selected, axes["horizons"], cases or [None])
    for entry, (model, functional, horizon, case) in zip(table, slots):
        bounded(entry, 2*8192, nodes=512, depth_limit=8, string_limit=256)
        sealed(entry, "binding_hash")
        key = [model["family_id"], model.get("configuration_id"), fingerprint(model["package"]),
            functional["functional_id"], horizon, case["instance_id"] if case is not None else None]
        actual = [entry[k] for k in ("model_family_id", "model_configuration_id", "model_package_hash",
            "functional_id", "horizon", "input_case_id")]
        require(set(entry) == ENTRY_FIELDS and entry["schema_version"] == "propagation-study-calibration-v1"
            and same(key, actual) and fingerprint(key) not in lookup
            and finite(entry["horizon"], positive=True)
            and type(entry["reason"]) is str and 0 < len(entry["reason"]) <= 256
            and entry["status"] in {"CALIBRATED", "FAILED", "UNAVAILABLE"}, "canonical unique ordered geometry slot")
        lookup[fingerprint(key)] = entry
        pointer = entry["source_pointer"]
        if entry["status"] == "UNAVAILABLE":
            require(all(entry[k] is None for k in ("source_pointer", "geometry", "source_evidence_hash",
                "consumer_study_id", "geometry_hash")), "unavailable is not zero-cost calibrated success")
        else:
            require(type(pointer) is dict and set(pointer) == {"schema_version", "policy", "source_attempt_id",
                "source_artifact_id", "source_authorization_id", "source_authorization_version"}
                and pointer["schema_version"] == "managed-affine-halfspace-calibration-v1"
                and pointer["policy"]["model_package_hash"] == entry["model_package_hash"]
                and finite(functional["target_probability"])
                and pointer["policy"]["target_probability"] == functional["target_probability"]
                and pointer["policy"]["code_hash"] == spec["code_hash"], "explicit frozen source/policy")
        if entry["status"] == "FAILED":
            require(all(entry[k] is None for k in ("geometry", "source_evidence_hash", "consumer_study_id", "geometry_hash")),
                "failed slot must not invent a region")
        elif entry["status"] == "CALIBRATED":
            require(entry["consumer_study_id"] == spec["study_id"] and entry["geometry_hash"] == fingerprint(entry["geometry"]),
                "successful geometry consumer/content binding")
    # Check the whole ordered model/method/functional/horizon/seed/case product,
    # not only successful/calibrated rows. Unavailable slots remain registered.
    full_count = len(axes["models"])*len(axes["methods"])*len(axes["functionals"])*len(axes["horizons"])*len(axes["seeds"])*(len(cases) or 1)
    require(0 < full_count <= 10000 and len(spec["cells"]) == full_count
        and spec["propagation_design"]["expected_cells"] == full_count, "complete registered matrix cardinality")
    matrix = product(axes["models"], axes["methods"], axes["functionals"], axes["horizons"], axes["seeds"], cases or [None])
    for cell, (model, method, functional, horizon, seed, case) in zip(spec["cells"], matrix):
        request = cell["propagation_request"]
        arms = [arm for arm in spec["arms"] if arm["arm_id"] == cell["arm_id"]]
        require(len(arms) == 1 and arms[0]["model_family_id"] == model["family_id"]
            and arms[0]["method_family_id"] == method["method"] and arms[0]["objective_id"] == functional["kind"]
            and cell["functional_id"] == functional["functional_id"]
            and same(cell["seed"], seed) and same(cell["horizon"], horizon)
            and request["model_package_hash"] == fingerprint(model["package"])
            and same(cell["frozen_dynamics"], model["package"]), "matrix axis/model/arm identity")
        initial = case if case is not None else model
        origin, cutoff = (case["origin"], case["history_cutoff"]) if case is not None else (axes["origin"], axes["history_cutoff"])
        key = [model["family_id"], model.get("configuration_id"), fingerprint(model["package"]),
            functional["functional_id"], horizon, case["instance_id"] if case is not None else None]
        entry = lookup.get(fingerprint(key))
        actual_functional = {k: v for k, v in functional.items() if k != "target_probability"}
        if entry is not None:
            require(same(cell["calibration_binding"], entry), "every target retains its complete table entry")
            if entry["status"] == "CALIBRATED":
                actual_functional["threshold"] = entry["geometry"]["threshold"]
                require(same(geometry(model["package"], request, entry["geometry"]["causal_input_hash"]), entry["geometry"]),
                    "same actual event across methods and seeds")
            else:
                disposition = cell.get("execution_disposition", {})
                require(disposition.get("status") in {"INELIGIBLE", "NOT_IMPLEMENTED"} and "execution" not in cell,
                    "failed/unavailable geometry cannot execute another easier event")
        else:
            require("calibration_binding" not in cell, "orphan target table binding")
        paired = {"model_package_hash": fingerprint(model["package"]), "initial_mean": initial["initial_mean"],
            "initial_covariance": initial["initial_covariance"], "origin": origin, "history_cutoff": cutoff,
            "horizon": horizon, "functional": actual_functional, "seed": seed}
        if entry is not None:
            paired["calibration_binding_hash"] = entry["binding_hash"]
        if case is not None:
            binding = {"schema_version": "propagation-input-binding-v1", "case": case,
                "policy": axes["input_policy"], "qualification": "declared-only-not-scientific"}
            paired["input_binding_hash"] = fingerprint(binding)
            require(cell["instance_id"] == case["instance_id"] and cell["block_id"] == case["block_id"], "input case identity")
        else:
            require(cell["block_id"] == model["family_id"], "synthetic source block identity")
        require(request["coupling_id"] == "paired-"+fingerprint(paired)
            and request["request_id"] == "cell-"+fingerprint({"paired": paired, "method": method, "arm": cell["arm_id"]}),
            "frozen paired physical request and method configuration")
    return table


def source_values(record, spec, exported_at):
    bounded(record, 8*1024*1024, nodes=100000, depth_limit=32, string_limit=16384)
    sealed(record, "record_hash")
    require_original_event_order(record["events"])
    validate_lineage(record, spec, exported_at)
    require(record["schema_version"] == "calibration-source-export-record-v1"
        and record["scientific_qualification"] is False and record["method_qualification"] is False,
        "source record is preparation, not method qualification")
    pointer, source, cell, run, attempt = (record[k] for k in
        ("pointer", "source_spec", "source_cell", "source_run", "selected_attempt"))
    require(record["pointer_hash"] == fingerprint(pointer) and same(source["runtime_binding"], spec["runtime_binding"])
        and source["code_hash"] == spec["code_hash"] and run["study_id"] == source["study_id"]
        and run["spec_hash"] == fingerprint(source) and run["cell_hash"] == fingerprint(cell)
        and same(run["cell"], cell) and sum(same(c, cell) for c in source["cells"]) == 1
        and cell["plugin_id"] == "affine-halfspace-calibration" and cell["visibility"] == "synthetic"
        and attempt["attempt_id"] == pointer["source_attempt_id"] and attempt["run_id"] == run["run_id"]
        and attempt["artifact_id"] == pointer["source_artifact_id"], "original source identity")
    sealed(run, "run_id")
    policy_values(pointer["policy"], cell["frozen_dynamics"], cell["propagation_request"], source["code_hash"])
    require(same(pointer["policy"], cell["probability_calibration_policy"]), "original registered source policy")
    grant = record["authorization"]
    require(grant["authorization_id"] == pointer["source_authorization_id"]
        and grant.get("version") == pointer["source_authorization_version"]
        and (pointer["source_authorization_version"] is None or type(pointer["source_authorization_version"]) is str)
        and grant["study_id"] == source["study_id"] and grant["protocol_hash"] == source["protocol_hash"]
        and (source["study_id"] == spec["study_id"] or spec["study_id"] in grant.get("consumer_study_ids", []))
        and {"evaluate", "export"} <= set(grant["purposes"])
        and {c["block_id"] for c in source["cells"]} <= set(grant["block_ids"])
        and record["visibility"] in grant["visibilities"] and timestamp(exported_at) < timestamp(grant["expires_at"]),
        "recorded source export permission covers complete source matrix and consumer")
    receipt, result, metadata = (record[k] for k in ("source_admission", "source_result", "source_artifact"))
    if receipt is not None:
        sealed(receipt, "admission_hash")
        require(receipt["mode"] == "pilot" and same(receipt["spec"], source) and same(receipt["cell"], cell)
            and receipt["attempt_id"] == attempt["attempt_id"] and receipt["run_id"] == run["run_id"], "source pilot admission")
    if metadata is not None:
        require(result is not None and metadata["artifact_id"] == metadata["sha256"] == fingerprint(result)
            == attempt["artifact_id"] and attempt["artifact_manifest_hash"] == fingerprint(metadata)
            and metadata["size_bytes"] == len(encoded(result)) and metadata["study_id"] == source["study_id"]
            and metadata["block_ids"] == [cell["block_id"]] and metadata["role"] == "result"
            and result["source_schema"] == "affine-halfspace-calibration-source-v1"
            and result["spec_hash"] == fingerprint(source) and result["cell_hash"] == fingerprint(cell), "actual saved source artifact")
    else:
        require(result is None and attempt["artifact_id"] is None, "absent result is not an invented artifact")
    history = record["history"]
    require(type(history) is list and 0 < len(history) <= 10000
        and len({a["attempt_id"] for a in history}) == len(history)
        and sum(same(a, attempt) for a in history) == 1
        and all(a["run_id"] == run["run_id"] for a in history), "complete original run attempt history")
    attempts = {a["attempt_id"]: a for a in history}
    for saved_event in record["events"]:
        require(saved_event["event_kind"] in KINDS and saved_event["payload"]["attempt_id"] in attempts,
            "owned original source event")
        event(saved_event, saved_event["event_kind"])
    for saved_attempt in history:
        registrations = [e for e in record["events"] if e["event_kind"] == "ATTEMPT"
            and e["payload"]["attempt_id"] == saved_attempt["attempt_id"] and e["payload"]["state"] == "REGISTERED"]
        completions = [e for e in record["events"] if e["event_kind"] == "ATTEMPT" and same(e["payload"], saved_attempt)]
        require(len(registrations) == len(completions) == 1
            and registrations[0]["sequence"] <= completions[0]["sequence"]
            and same(registrations[0]["payload"]["parent_attempt_id"], saved_attempt["parent_attempt_id"])
            and same(registrations[0]["payload"]["reason"], saved_attempt["reason"])
            and timestamp(completions[0]["created_at"]) <= timestamp(exported_at),
            "every original attempt retains its authoritative latest disposition")
        parent = saved_attempt["parent_attempt_id"]
        require(parent is None or parent in attempts and attempts[parent]["state"] in FAILURES
            and type(saved_attempt["reason"]) is str and bool(saved_attempt["reason"]), "explicit original failed retry parent")
        if parent is not None:
            parent_done = next(e for e in record["events"] if e["event_kind"] == "ATTEMPT" and same(e["payload"], attempts[parent]))
            require(parent_done["sequence"] < registrations[0]["sequence"], "original retry sequence")
    require(len(history) <= 3 and sum(a["parent_attempt_id"] is None for a in history) == 1,
        "one original source and at most two explicit retries")
    row = {"attempt_id": attempt["attempt_id"], "history": history, "run_id": run["run_id"],
        "arm_id": cell["arm_id"], "cost": record["cost"]}
    validate_cost(row, {"study_id": source["study_id"]}, set())
    # Cost sources must be the latest original RESERVE/SETTLE for every attempt,
    # not a selected subset or a rehashed cheaper replacement event.
    latest = {}
    for saved_event in record["events"]:
        if saved_event["event_kind"] in {"RESERVE", "SETTLE"}:
            latest[saved_event["payload"]["reservation_id"]] = saved_event
    require(same(list(latest.values()), record["cost"]["sources"]), "all original cost events, including failures")
    for saved_event in record["cost"]["sources"]:
        value = saved_event["payload"]
        require(value["reservation_id"] == fingerprint([source["runtime_binding"]["store_id"], value["attempt_id"]]),
            "original store/attempt reservation identity")
        owned = [e for e in record["events"] if e["payload"].get("attempt_id") == value["attempt_id"]]
        reserves = [e for e in owned if e["event_kind"] == "RESERVE"]
        workers = [e for e in owned if e["event_kind"] == "WORKER_STARTED"]
        stops = [e for e in owned if e["event_kind"] == "WORKER_TREE_STOPPED"]
        require(len(reserves) == 1 and value["reserved_ms"] == reserves[0]["payload"]["reserved_ms"]
            == ceil(pointer["policy"]["maximum_job_seconds"]*1000)
            and reserves[0]["sequence"] <= saved_event["sequence"], "original frozen reservation cap")
        if workers and value["settled"]:
            require(len(workers) == 1 and reserves[0]["sequence"] < workers[0]["sequence"], "one funded original worker")
            if value["monotonic_elapsed_ms"] is not None:
                require(len(stops) == 1 and workers[0]["sequence"] < stops[0]["sequence"] < saved_event["sequence"]
                    and stops[0]["payload"]["observed_elapsed_ms"] == value["monotonic_elapsed_ms"],
                    "all-attempt charge equals native whole-tree stop measurement")
            else:
                require(any(e["event_kind"] == "WORKER_STOP_CONFIRMED" and workers[0]["sequence"] < e["sequence"] < saved_event["sequence"]
                    for e in owned), "unknown cost retains original stop attestation and full reservation charge")
    proof = record["proof"]
    if proof is not None:
        validate_saved_calibration(proof, pointer, consumer_study_id=spec["study_id"])
        require(record["outcome"] == "calibrated-preparation-not-method-qualification"
            and same(proof["source_attempt"], attempt) and same(proof["source_result"], result)
            and same(proof["source_admission"], receipt) and same(proof["authorization"], grant), "successful owner record binding")
    elif attempt["state"] == "SUCCEEDED":
        analysis = result["forecast"]["probability_calibration_analysis"]
        sealed(analysis, "analysis_hash")
        require(record["outcome"] == "recorded-numerical-analysis-failure" and analysis["status"] == "FAILED"
            and analysis["scientific_qualification"] is False and analysis["method_qualification"] is False
            and analysis["admission_status"] == "NOT_ADMITTED", "actual saved numerical failure, not a cheaper event")
    else:
        require(attempt["state"] in FAILURES and record["outcome"] == "recorded-execution-failure-"+attempt["state"],
            "actual terminal execution failure without promotion")


def cost_values(records):
    sources = {}
    for record in records:
        store_id = record["source_spec"]["runtime_binding"]["store_id"]
        by_attempt = {e["payload"]["attempt_id"]: e for e in record["cost"]["sources"]}
        for attempt in record["history"]:
            key = (store_id, attempt["attempt_id"])
            saved = by_attempt.get(attempt["attempt_id"])
            value = saved["payload"] if saved is not None else None
            source = {"source_id": fingerprint(list(key)), "store_id": store_id, "attempt_id": attempt["attempt_id"],
                "state": attempt["state"], "event_hash": saved["hash"] if saved is not None else None,
                "charged_ms": value["charged_ms"] if value is not None and value["settled"] else None,
                "reserved_ms": (value["reserved_ms"] if not value["settled"] else 0) if value is not None else None,
                "measured_ms": value["monotonic_elapsed_ms"] if value is not None and value["settled"] else None,
                "status": ("MEASURED" if value["monotonic_elapsed_ms"] is not None else "UPPER_BOUND")
                    if value is not None and value["settled"] else "RESERVED" if value is not None else "UNAVAILABLE"}
            require(key not in sources or same(sources[key], source), "conflicting original source costs")
            sources[key] = source
    values = list(sources.values())
    def total(field):
        return sum(v[field] for v in values) if values and all(v[field] is not None for v in values) else None
    return {"unit": "slot-ms", "scope": "unique-calibration-source-attempts-including-failures-not-per-target-cell",
        "unique_attempts": len(values), "charged_ms": total("charged_ms"), "reserved_ms": total("reserved_ms"),
        "measured_ms": total("measured_ms"), "sources": values}


def validate_calibration_table(bundle):
    try:
        return _validate(bundle)
    except (KeyError, TypeError, AttributeError, IndexError, OverflowError, RecursionError, ValueError) as exc:
        raise ValueError("missing or malformed complete calibration evidence: " + str(exc)) from exc


def _validate(bundle):
    spec = bundle.get("registered_spec") or {}
    axes = spec.get("propagation_design", {}).get("axis_manifest", {})
    declared = bool(axes.get("calibrations")) or any(f.get("target_probability") is not None for f in axes.get("functionals", []))
    header = bundle.get("probability_calibration")
    if not declared and header is None:
        require(not any("calibration_binding" in (c.get("registered_cell") or {})
            or "probability_calibration" in (c.get("admission") or {}).get("documents", {}) for c in bundle["cells"]),
            "orphan embedded preparation proof")
        return None
    require(declared and header is not None and fingerprint(spec) == bundle["spec_hash"], "complete bound table source")
    table = table_values(spec)
    bounded(header, 48*1024*1024, nodes=1000000, depth_limit=35, string_limit=16384)
    sealed(header, "evidence_hash")
    require(set(header) == {"schema_version", "table_hash", "slots", "sources", "cost", "evidence_hash"}
        and header["schema_version"] == "propagation-calibration-table-evidence-v1"
        and header["table_hash"] == fingerprint(table), "complete table content hash")
    expected_slots = [{"binding_hash": entry["binding_hash"], "status": entry["status"], "reason": entry["reason"],
        "pointer_hash": fingerprint(entry["source_pointer"]) if entry["source_pointer"] is not None else None} for entry in table]
    require(same(header["slots"], expected_slots), "no missing/failed slot can be dropped")
    records = {record["pointer_hash"]: record for record in header["sources"]}
    expected_refs = {slot["pointer_hash"] for slot in expected_slots if slot["pointer_hash"] is not None}
    require(len(records) == len(header["sources"]) and records.keys() == expected_refs, "exact original source set")
    for record in header["sources"]:
        source_values(record, spec, bundle["recorded_at"])
    for entry in table:
        if entry["source_pointer"] is None:
            continue
        record = records[fingerprint(entry["source_pointer"])]
        require(same(record["pointer"], entry["source_pointer"])
            and record["source_cell"]["propagation_request"]["horizons"] == [entry["horizon"]], "actual source slot horizon")
        proof = record["proof"]
        require((entry["status"] == "CALIBRATED") == (proof is not None), "actual source disposition")
        if proof is not None:
            require(entry["source_evidence_hash"] == proof["evidence_hash"]
                and entry["geometry_hash"] == proof["geometry_hash"] and same(entry["geometry"], proof["geometry"]), "actual successful owner table binding")
    require(same(header["cost"], cost_values(header["sources"])), "deduplicated all-attempt calibration cost")
    from_visibility = {record["visibility"] for record in header["sources"]}
    require(("restricted" not in from_visibility or bundle["visibility"] == "restricted")
        and ("public" not in from_visibility or bundle["visibility"] in {"public", "restricted"}), "bundle cannot narrow source visibility")
    rows = {row["cell_hash"]: row for row in bundle["cells"]}
    require(len(rows) == len(spec["cells"]) and rows.keys() == {fingerprint(c) for c in spec["cells"]}, "complete matrix retains every target")
    for cell in spec["cells"]:
        row = rows[fingerprint(cell)]
        require(same(row["registered_cell"], cell), "actual registered target identity")
        if row["status"] == "SUCCEEDED" and "calibration_binding" in cell:
            receipt = row["admission"]
            sealed(receipt, "admission_hash")
            require(same(receipt["spec"], spec) and same(receipt["cell"], cell), "target receipt source")
            entry = cell["calibration_binding"]
            proof = receipt["documents"]["probability_calibration"]
            require(same(proof, records[fingerprint(entry["source_pointer"])]["proof"]), "actual target retains the same original preparation")
            result = row["result"]
            artifact(result, row["result_artifact"], spec, cell, resume_level=result["resume_level"])
            require(result["admission_hash"] == receipt["admission_hash"] == row["admission_hash"]
                and result["forecast"]["model_package_hash"] == fingerprint(cell["frozen_dynamics"])
                and result["forecast"]["request_hash"] == fingerprint(cell["propagation_request"])
                and same(result["forecast"]["horizons"], cell["propagation_request"]["horizons"]), "actual target output law/event")
    return header["cost"]
