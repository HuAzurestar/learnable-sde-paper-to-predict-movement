"""Offline per-attempt resource proof; no native observer or runtime imports.

The caller authenticates the expected bundle transport hash. Event hashes prove
internal source consistency, not authenticity of an arbitrary fabricated bundle.
Legacy absence is unavailable, never zero. RSS peaks are never additive.
"""
import hashlib
import json
import re


DURATION = "worker-validation-method-reference-qualification-pipeline"
MEMORY = "current-process-lifetime-through-observation"
POLICY = {"schema_version": "pirc27-propagation-resource-policy-v1", "required": True,
          "duration_scope": DURATION, "memory_scope": MEMORY}
POINTS = {"SUCCEEDED": "job-payload-before-encoding", "FAILED": "observer-call",
          "CHECKPOINTED": "checkpoint-save-before-ack"}
REASONS = {"NOT_RECORDED", "NOT_LAUNCHED", "UNCONFIRMED_STOP", "UNSETTLED_COST",
           "MISSING_OBSERVATION", "INVALID_OBSERVATION"}
PLUGINS = {"affine-propagation", "affine-propagation-chunk", "synthetic-propagation",
    "synthetic-propagation-chunk", "affine-propagation-qualification", "affine-mlmc-qualification-chunk",
    "affine-mlmc-production-chunk", "affine-mixture-qualification", "affine-mixture-production-chunk",
    "affine-mixture-chunk", "synthetic-mixture-chunk", "affine-path-qualification",
    "affine-path-production-chunk", "affine-cubature", "affine-cubature-qualification",
    "affine-halfspace-calibration"}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def fingerprint(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError("invalid resource evidence: " + message)


def event(value, kind, attempt):
    require(type(value) is dict and value["event_kind"] == kind
            and type(value["sequence"]) is int and value["sequence"] > 0
            and value["payload"]["attempt_id"] == attempt
            and value["hash"] == fingerprint({k: v for k, v in value.items() if k != "hash"}),
            "source event hash/kind/attempt/sequence")
    return value["payload"]


def packet(value, spec, cell, attempt):
    fixed = {"schema_version": "pirc27-propagation-resource-observation-v1",
        "study_id": spec["study_id"], "spec_hash": fingerprint(spec), "cell_hash": fingerprint(cell),
        "code_hash": spec["code_hash"], "attempt_id": attempt,
        "policy_hash": fingerprint(cell["resource_observation_policy"]), "includes_previous_attempts": False}
    require(type(value) is dict and set(value) == set(fixed) | {"execution_state", "resumed", "duration", "memory"}
            and canonical({k: value[k] for k in fixed}) == canonical(fixed), "packet source/schema")
    require(type(attempt) is str and re.fullmatch(r"[0-9a-f]{32}", attempt) is not None,
            "native attempt identity")
    require(canonical(cell["resource_observation_policy"]) == canonical(POLICY)
            and cell["resource_class"] == "cpu" and cell["plugin_id"] in PLUGINS
            and type(cell["propagation_request"]) is dict,
            "frozen observation policy")
    require(value["execution_state"] in POINTS and type(value["resumed"]) is bool, "packet disposition")
    duration = value["duration"]
    require(set(duration) == {"wall_ns", "cpu_ns", "units", "scope", "cpu_scope"}
            and duration["units"] == "ns" and duration["scope"] == DURATION
            and duration["cpu_scope"] == "current-process-all-threads"
            and type(duration["wall_ns"]) is int and 0 < duration["wall_ns"] < 1 << 63
            and type(duration["cpu_ns"]) is int and 0 <= duration["cpu_ns"] < 1 << 63,
            "pipeline duration scope/units")
    memory = value["memory"]
    fixed_memory = {"observer_schema": "pirc26-process-resource-observation-v1",
        "point": POINTS[value["execution_state"]], "scope": MEMORY, "units": "bytes",
        "includes_children": False, "includes_previous_attempts": False, "is_phase_isolated": False}
    require(set(memory) == set(fixed_memory) | {"status", "platform", "resident_counter", "peak_resident_bytes", "reason"}
            and canonical({k: memory[k] for k in fixed_memory}) == canonical(fixed_memory), "memory scope/schema")
    platform = memory["platform"]
    require(type(platform) is str and re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", platform) is not None, "native platform")
    counter = ("windows.PROCESS_MEMORY_COUNTERS_EX.PeakWorkingSetSize" if platform == "win32" else
               "linux.getrusage.RUSAGE_SELF.ru_maxrss" if platform.startswith("linux") else None)
    if memory["status"] == "MEASURED":
        require(counter is not None and memory["resident_counter"] == counter and memory["reason"] is None
                and type(memory["peak_resident_bytes"]) is int and 0 < memory["peak_resident_bytes"] < 1 << 63,
                "native resident peak")
    else:
        require(memory["status"] == "UNAVAILABLE" and memory["peak_resident_bytes"] is None
                and memory["resident_counter"] is None and memory["reason"] ==
                ("NATIVE_COUNTER_UNAVAILABLE" if counter else "UNSUPPORTED_PLATFORM"), "unknown RSS is null")
    require(len(canonical(value)) <= 16384, "bounded observation")


def validate_resources(row, bundle):
    try:
        _validate(row, bundle)
    except (KeyError, TypeError, AttributeError, OverflowError) as exc:
        raise ValueError("malformed resource evidence") from exc


def _validate(row, bundle):
    cell = row.get("registered_cell", {})
    spec = bundle.get("registered_spec")
    # Row-level fields are not the authority for opting out. Otherwise removing
    # both registered_cell and resource_usage would launder a new registered
    # measurement obligation into the intentionally permissive legacy path.
    source_required = type(spec) is dict and any(
        "resource_observation_policy" in c and fingerprint(c) == row["cell_hash"]
        for c in spec.get("cells", []))
    required = source_required or "resource_observation_policy" in cell
    if not required:
        require("resource_usage" not in row, "unregistered observation")
        return
    require(fingerprint(spec) == bundle["spec_hash"] and fingerprint(cell) == row["cell_hash"]
            and sum(canonical(c) == canonical(cell) for c in spec["cells"]) == 1
            and all(spec[k] == bundle[k] for k in ("study_id", "code_hash")), "registered observation source")
    usage = row["resource_usage"]
    require(set(usage) == {"schema_version", "peak_aggregation", "attempts"}
            and usage["schema_version"] == "pirc27-resource-history-v1"
            and usage["peak_aggregation"] == "not-additive;not-a-phase-delta;not-a-tree-peak", "history scope")
    history = row["history"]
    ids = [a["attempt_id"] for a in history]
    require(len(ids) == len(set(ids)) and [a["attempt_id"] for a in usage["attempts"]] == ids,
            "complete ordered all-attempt history")
    costs = {e["payload"]["attempt_id"]: e for e in row["cost"]["sources"]}
    for source, attempt in zip(usage["attempts"], history):
        require(set(source) == {"attempt_id", "status", "reason", "artifact", "packet", "publication_event",
                "worker_stop_event", "settlement_event", "resume_event"}, "history entry schema")
        aid = attempt["attempt_id"]
        resume = source["resume_event"]
        if resume is not None:
            resumed = event(resume, "RESUME", aid)
            require(resumed["parent_attempt_id"] in ids[:ids.index(aid)]
                    and resumed["resume_level"] == "chunk", "original earlier checkpoint parent")
        publication = source["publication_event"]
        if publication is None:
            require(source["status"] == "UNAVAILABLE" and source["reason"] == "NOT_RECORDED"
                    and all(source[k] is None for k in ("artifact", "packet", "worker_stop_event", "settlement_event")),
                    "unpublished resource is unknown")
            continue
        payload = event(publication, "PROPAGATION_RESOURCE_RECORDED", aid)
        require(attempt["state"] in {"SUCCEEDED", "FAILED", "INTERRUPTED", "TIMEOUT", "BUDGET_EXHAUSTED",
                "PREFLIGHT_FAILED", "CANCELLED"}, "resource publication requires a terminal attempt")
        binding = {"schema_version": "pirc27-resource-record-v1", "attempt_id": aid,
            "run_id": row["run_id"], "spec_hash": bundle["spec_hash"], "cell_hash": row["cell_hash"],
            "code_hash": bundle["code_hash"], "policy_hash": fingerprint(cell["resource_observation_policy"]),
            "attempt_state": attempt["state"]}
        require(set(payload) == set(binding) | {"result_artifact_id", "status", "reason", "artifact_id",
                "packet_hash", "worker_stop_event_hash", "settlement_event_hash"}
                and canonical({k: payload[k] for k in binding}) == canonical(binding)
                and payload["status"] == source["status"] and payload["reason"] == source["reason"],
                "publication source/disposition")
        if aid == row["attempt_id"]:
            require(payload["result_artifact_id"] == row["artifact_id"], "selected result artifact")
        if attempt["state"] != "SUCCEEDED":
            require(payload["result_artifact_id"] is None, "unsuccessful attempt has no result")
        stop, settled = source["worker_stop_event"], source["settlement_event"]
        for key, value, kind in (("worker_stop_event_hash", stop, "WORKER_TREE_STOPPED"),
                                 ("settlement_event_hash", settled, "SETTLE")):
            require(payload[key] == (value["hash"] if value else None), "stop/settlement reference")
            if value:
                event(value, kind, aid)
                require(value["sequence"] < publication["sequence"], "stop/cost before publication")
        if stop:
            require(stop["payload"]["confirmation"] == "native-job-or-process-group-no-running-descendants", "native tree stop")
        if settled:
            require(canonical(settled) == canonical(costs[aid]) and settled["payload"]["settled"] is True
                    and stop is not None and stop["sequence"] < settled["sequence"]
                    and stop["payload"]["reservation_id"] == settled["payload"]["reservation_id"], "original settled cost")
        if source["status"] == "UNAVAILABLE":
            require(source["reason"] in REASONS - {"NOT_RECORDED"} and source["artifact"] is None
                    and source["packet"] is None and payload["artifact_id"] is None and payload["packet_hash"] is None,
                    "unknown observation remains null")
            expected = {"NOT_LAUNCHED": (False, False), "UNCONFIRMED_STOP": (False, False),
                        "UNSETTLED_COST": (True, False), "MISSING_OBSERVATION": (True, True),
                        "INVALID_OBSERVATION": (True, True)}[source["reason"]]
            require((stop is not None, settled is not None) == expected, "unavailable reason/source disposition")
            continue
        require(source["status"] == "RECORDED" and source["reason"] is None and settled is not None,
                "measurement requires native stop and settled cost")
        value, metadata = source["packet"], source["artifact"]
        packet(value, spec, cell, aid)
        require(metadata["role"] == "propagation-resource-observation" and metadata["study_id"] == bundle["study_id"]
                and metadata["block_ids"] == [row["block_id"]] and type(metadata["size_bytes"]) is int
                and metadata["size_bytes"] == len(canonical(value))
                and fingerprint(value) == metadata["artifact_id"] == metadata["sha256"]
                == payload["artifact_id"] == payload["packet_hash"], "resource artifact bytes/scope")
        require(value["resumed"] is (resume is not None), "resume source marker")
        if resume:
            require(resume["sequence"] < stop["sequence"], "resume before native stop")
        if attempt["state"] == "SUCCEEDED":
            require(value["execution_state"] == "SUCCEEDED", "successful observation state")
        elif attempt["error_code"] == "CHECKPOINT_SAVED":
            require(value["execution_state"] == "CHECKPOINTED", "checkpoint observation state")
