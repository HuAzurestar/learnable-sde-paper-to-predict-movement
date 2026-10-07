"""Offline validation of PSDE's immutable execution-admission evidence.

The expected bundle hash is the trusted transport boundary. This validates
bindings and recorded checks, not authenticity of arbitrary external reports.
No runtime/provider dependency or raw research-data access is required.
"""

from datetime import datetime
import hashlib
import json
import re

if __package__:
    from .dimensions import comparison_dimensions, canonical
    from .upstream import validate_upstream
    from .admission_selection import selected_settings
    from .analytic_qualification import validate_analytic_qualification
    from .mlmc_qualification import validate_mlmc_qualification
    from .mixture_qualification import validate_mixture_qualification
else:
    from dimensions import comparison_dimensions, canonical
    from upstream import validate_upstream
    from admission_selection import selected_settings
    from analytic_qualification import validate_analytic_qualification
    from mlmc_qualification import validate_mlmc_qualification
    from mixture_qualification import validate_mixture_qualification


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def require(condition, detail):
    if not condition:
        raise ValueError("invalid admission evidence: " + detail)


def event_valid(event):
    return fingerprint({key: value for key, value in event.items() if key != "hash"}) == event["hash"]


def same_source(left, right):
    left_hash = left.get("sha256")
    if isinstance(left_hash, str) and re.fullmatch(r"[0-9a-f]{64}", left_hash) and left_hash == right.get("sha256"):
        return True
    return (left.get("dataset_id") == right.get("dataset_id") and
            (not isinstance(left_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", left_hash) or
             left.get("source_block_id", left.get("block_id")) ==
             right.get("source_block_id", right.get("block_id"))))


def qualification(package, prereg, report, evidence, grant):
    binding = fingerprint({key: value for key, value in package.items() if key != "qualification_hash"})
    require(report["schema_version"] == "pirc25-qualification-v1" and report["status"] == "passed", "qualification status")
    require(package["study_id"] in prereg["study_ids"] and package["study_id"] == grant["study_id"], "qualification source study")
    require(fingerprint(report) == package["qualification_hash"] and report["package_binding"] == binding,
            "qualification package binding")
    require(report["code_hash"] == package["code_hash"] and report["preregistration_hash"] == fingerprint(prereg)
            == package["preregistration_hash"], "qualification code/preregistration binding")
    required = prereg["qualification_checks"]
    require(required and len(required) == len(set(required)) and len(report["checks"]) == len(required), "qualification check set")
    require({c["check_id"] for c in report["checks"]} == set(required), "missing qualification checks")
    artifacts = {item["artifact"]["artifact_id"]: item for item in evidence}
    require(len(artifacts) == len(evidence) == len(required), "qualification evidence count")
    for check in report["checks"]:
        item = artifacts[check["artifact_id"]]
        value, metadata = item["content"], item["artifact"]
        require(metadata["role"] == "qualification" and fingerprint(value) == check["artifact_id"], "qualification artifact hash/role")
        require(metadata["study_id"] == grant["study_id"] and metadata["visibility"] in grant["visibilities"]
                and set(metadata["block_ids"]) <= set(grant["block_ids"]) and "evaluate" in grant["purposes"], "qualification access scope")
        require(value["check_id"] == check["check_id"] and value["outcome"] == "passed"
                and value["package_binding"] == binding and value["code_hash"] == package["code_hash"]
                and value["preregistration_hash"] == fingerprint(prereg), "qualification test outcome/bindings")


def validate_model_permission(model, grant, spec, admitted_at, *, cell=None, receipt=None):
    foreign = model["study_id"] != spec["study_id"]
    settings = (selected_settings(spec, cell, receipt) if "cell_packages" in spec["admission"]
                else spec["admission"])
    expected_id = settings.get("model_authorization_id") if foreign else settings["authorization_id"]
    require(grant.get("authorization_id") == expected_id and expected_id is not None,
            "frozen model grant identity")
    version = settings.get("model_authorization_version" if foreign else "authorization_version")
    require(grant.get("version") == version and
            ("version" not in grant or isinstance(version, str) and bool(version)), "frozen model grant version")
    require(grant.get("protocol_hash") == model["protocol_hash"], "frozen model grant protocol binding")
    require(grant["study_id"] == model["study_id"] and
            (not foreign or spec["study_id"] in grant.get("consumer_study_ids", [])), "frozen model consumer grant")
    require("evaluate" in grant["purposes"] and model.get("visibility", "restricted") in grant["visibilities"],
            "model visibility/purpose permission")
    start, expiry = datetime.fromisoformat(admitted_at), datetime.fromisoformat(grant["expires_at"])
    require(start.tzinfo is not None and expiry.tzinfo is not None and start < expiry, "model grant expired")


def validate_admission(bundle, row):
    try:
        receipt = row["admission"]
        require(receipt["schema_version"] == "pirc25-admission-v1" and receipt["mode"] == "formal"
                and receipt["input_kind"] == "registered-protocol" and receipt["qualification"] == "qualified", "formal admission required")
        require(fingerprint({key: value for key, value in receipt.items() if key != "admission_hash"})
                == receipt["admission_hash"] == row["admission_hash"], "admission content hash")
        spec, cell, docs = receipt["spec"], receipt["cell"], receipt["documents"]
        require(fingerprint(spec) == receipt["spec_hash"] == bundle["spec_hash"] and
                fingerprint(cell) == receipt["cell_hash"] == row["cell_hash"] and cell in spec["cells"], "spec/cell identity")
        require(receipt["attempt_id"] == row["attempt_id"] and receipt["run_id"] == row["run_id"], "attempt/run identity")
        require(all(cell[key] == row[key] for key in ("arm_id", "block_id", "seed")), "matrix identity")
        require(canonical(comparison_dimensions(cell)) == canonical(comparison_dimensions(row)), "matrix dimensions")
        require(all(spec[key] == bundle[key] for key in ("study_id", "code_hash", "data_hash", "protocol_hash")), "bundle input identity")
        protocol, grant, package = docs["protocol"], docs["authorization"], docs["package"]
        settings = selected_settings(spec, cell, receipt)
        require(settings["mode"] == "formal" and protocol["schema_version"] == "pirc25-data-protocol-v1", "protocol version/mode")
        require(fingerprint(protocol) == spec["protocol_hash"] == package["protocol_hash"] == grant["protocol_hash"], "protocol binding")
        require(protocol["study_id"] == grant["study_id"] == spec["study_id"] and
                protocol["protocol_id"] == settings["protocol_id"] and grant["authorization_id"] == settings["authorization_id"], "grant identity")
        version = settings.get("authorization_version")
        require(grant.get("version") == version and
                ("version" not in grant or isinstance(version, str) and bool(version)), "grant version")
        data = [{"dataset_id": b["dataset_id"], "release_id": b["release_id"],
                 "source_block_id": b.get("source_block_id", b["block_id"]), "sha256": b["sha256"],
                 "block_id": b["block_id"], "split_role": b["split_role"]} for b in protocol["blocks"]]
        require(fingerprint(data) == spec["data_hash"] == package["data_hash"] == package["input_hash"], "data identity")
        block = next(b for b in protocol["blocks"] if b["block_id"] == cell["block_id"])
        require(block["split_role"] in {"test", "final-eval"} and settings["purpose"] == "evaluate", "formal test role/purpose")
        require({"execute", "evaluate"} <= set(grant["purposes"]) and grant["test_authorization"] is True
                and cell["block_id"] in grant["block_ids"] and cell.get("visibility", "restricted") in grant["visibilities"], "execution grant scope")
        require(datetime.fromisoformat(receipt["admitted_at"]) < datetime.fromisoformat(grant["expires_at"]), "grant expired before admission")
        require(package["schema_version"] == "pirc25-package-v1" and package["kind"] in
                {"FrozenDynamicsPackage", "PropagationResult", "SwitchingResult"}, "package kind/schema")
        require(fingerprint(package) == settings["package_hash"] and package["qualification"] == "qualified"
                and package["study_id"] == spec["study_id"]
                and package["code_hash"] == spec["code_hash"] and package["plugin_hash"] == receipt["plugin_hash"], "package/code/plugin binding")
        require(package.get("visibility", "restricted") in grant["visibilities"], "package visibility permission")
        require(fingerprint(package["payload"]) == package["output_hash"] and cell["capability"] in package["capabilities"], "package payload/capability")
        require(receipt["execution_kind"] in {"run", "resume"} and receipt["command_hash"] ==
                package["recovery_command_hash" if receipt["execution_kind"] == "resume" else "command_hash"], "execution/recovery command binding")
        require(package["state_order"] == row["state_order"] == ["x", "y", "vx", "vy"] and
                package["units"] == row["units"] == ["m", "m", "m/s", "m/s"], "package/result state/units")
        validate_upstream(receipt)
        if "upstream_hash" in settings or "upstream_hash" in package:
            upstream = docs["upstream"]
            require(fingerprint({k: v for k, v in upstream.items() if k != "manifest_hash"}) == upstream["manifest_hash"]
                    == settings["upstream_hash"] == package["upstream_hash"], "legacy upstream binding")
            require([obj["object_id"] for obj in upstream["objects"]] == settings["upstream_ids"], "legacy upstream dependency set")
        prereg, history = docs["preregistration"], docs["history"]
        require(prereg["schema_version"] == "pirc25-preregistration-v1" and prereg["test_mode"] == "blind", "blind frozen plan required")
        require(fingerprint(prereg) == protocol["preregistration_hash"] == package["preregistration_hash"]
                == bundle["comparison_plan"]["preregistration_hash"] == spec["comparison_plan"]["preregistration_hash"], "preregistration binding")
        binding = fingerprint({k: v for k, v in protocol.items() if k not in {"preregistration_hash", "history_hash", "history_status"}})
        require(binding in prereg["protocol_bindings"] and spec["study_id"] in prereg["study_ids"], "preregistration scope")
        primary = prereg["primary_metrics"]
        require(isinstance(primary, list) and primary and
                all(isinstance(metric, str) and metric.strip() for metric in primary) and
                len(primary) == len(set(primary)) and
                prereg["selection_rule"].strip() and prereg["stopping_rule"].strip() and
                set(row["metrics"]) == set(primary), "preregistered primary metrics must be complete")
        comparison = {"reference": bundle["comparison_plan"]["reference_arm_id"],
                      "candidates": bundle["comparison_plan"]["candidate_arm_ids"]}
        require(comparison in prereg["comparisons"] and bundle["comparison_plan"] == spec["comparison_plan"], "preregistered comparison differs")
        require(fingerprint(history) == protocol["history_hash"] and history["schema_version"] == "pirc25-exposure-history-v1"
                and fingerprint(history["source_evidence"]) == history["source_evidence_hash"] and history["source"].strip(), "historical evidence binding")
        records = history["source_evidence"]["records"]
        require(isinstance(records, list) and records and
                all(isinstance(record, dict) and record.get("status") in {"unexposed", "exposed", "unknown"}
                    for record in records), "historical exposure records")
        matching = [r for r in records if all(r[k] == v for k, v in {
            "dataset_id": block["dataset_id"], "release_id": block["release_id"], "sha256": block["sha256"],
            "source_block_id": block.get("source_block_id", block["block_id"])}.items())]
        require(len(matching) == 1 and matching[0]["status"] == "unexposed", "historical data coverage")
        require(not any(same_source(record, block) and record["status"] in {"exposed", "unknown"}
                        for record in records), "conflicting historical exposure")
        frozen = docs["preregistration_event"]
        require(event_valid(frozen) and frozen["event_kind"] == "MANIFEST" and
                frozen["payload"] == {"object_id": "preregistration-" + fingerprint(prereg), "sha256": fingerprint(prereg)}, "preregistration publication event")
        reads = receipt["input_evidence"]
        require(bool(reads), "missing completed input read")
        for event in reads:
            read = event["payload"]
            require(event_valid(event) and event["event_kind"] == "READ_COMPLETED" and read["allowed"] is True, "completed exposure event")
            require(read["attempt_id"] == row["attempt_id"] and read["run_id"] == row["run_id"]
                    and read["study_id"] == spec["study_id"] and read["block_id"] == cell["block_id"]
                    and read["sha256"] == block["sha256"] and read["authorization_id"] == grant["authorization_id"]
                    and read["protocol_hash"] == spec["protocol_hash"] and read["purpose"] == "evaluate", "input exposure binding")
            # Older unversioned receipts remain readable. Explicit versions
            # always require the exact grant hash and version at the read.
            if "version" in grant or "authorization_hash" in read:
                require(read.get("authorization_version") == grant.get("version") and
                        read.get("authorization_hash") == fingerprint(grant), "input authorization version/hash")
            require(read["preregistration_hash"] == fingerprint(prereg) and read["history_hash"] == fingerprint(history)
                    and read["test_mode"] == "blind" and read["frozen_sequence"] == frozen["sequence"] < event["sequence"], "test freeze preceded exposure")
        qualification(package, prereg, docs["qualification"], docs["qualification_evidence"], grant)
        # An analytic package pointer or a propagation adapter must never
        # silently fall back to the older generic operator pass contract.
        if ("managed_mixture_qualification" in package["payload"] or cell.get("plugin_id") == "affine-mixture-production-chunk"):
            validate_mixture_qualification(receipt, row)
        elif ("managed_mlmc_qualification" in package["payload"] or cell.get("plugin_id") == "affine-mlmc-production-chunk"):
            validate_mlmc_qualification(receipt, row)
        elif ("managed_analytic_qualification" in package["payload"]
                or docs.get("propagation_qualification") is not None
                or cell.get("plugin_id") in {"affine-propagation", "affine-propagation-chunk",
                    "synthetic-propagation", "synthetic-propagation-chunk"}):
            validate_analytic_qualification(receipt, row)
        if package.get("requires_frozen_model"):
            model = docs["frozen_model"]
            require(fingerprint(model) == package["model_hash"] and model["kind"] == "FrozenDynamicsPackage"
                    and model["qualification"] == "qualified" and fingerprint(model["payload"]) == model["output_hash"], "frozen model binding")
            model_protocol, model_prereg = docs["model_protocol"], docs["model_preregistration"]
            model_data = [{"dataset_id": b["dataset_id"], "release_id": b["release_id"],
                "source_block_id": b.get("source_block_id", b["block_id"]), "sha256": b["sha256"],
                "block_id": b["block_id"], "split_role": b["split_role"]} for b in model_protocol["blocks"]]
            require(model_protocol["schema_version"] == "pirc25-data-protocol-v1" and
                    model_protocol["protocol_id"] == settings["model_protocol_id"] and
                    model_protocol["study_id"] == model["study_id"] and fingerprint(model_protocol) == model["protocol_hash"]
                    and fingerprint(model_data) == model["data_hash"], "frozen model source protocol/data binding")
            require(model_protocol["preregistration_hash"] == model["preregistration_hash"] == fingerprint(model_prereg)
                    and fingerprint({k: v for k, v in model_protocol.items() if k not in
                        {"preregistration_hash", "history_hash", "history_status"}}) in model_prereg["protocol_bindings"], "frozen model source preregistration")
            model_grant = docs["model_authorization"]
            validate_model_permission(model, model_grant, spec, receipt["admitted_at"], cell=cell, receipt=receipt)
            qualification(model, docs["model_preregistration"], docs["model_qualification"], docs["model_qualification_evidence"], model_grant)
    except (KeyError, TypeError, StopIteration, AttributeError) as exc:
        raise ValueError("missing or malformed admission evidence") from exc
