"""Regenerate NEX326 process/status tables and a test plot from RunRecords only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import random
from collections import Counter, defaultdict
from numbers import Real
from pathlib import Path
from statistics import median
from typing import Iterable, Mapping, Sequence


SCHEMA_VERSION = "nex326-run-record-v2"
SPEC_VERSION = "nex326-process-v2"
EXPECTED_ARMS = set(range(1, 23))
EXPECTED_EXECUTIONS = {
    1: {"full"},
    2: {"pointwise"},
    3: {"single_gaussian"},
    4: {"gmm_kernel"},
    5: {"explicit_decomp"},
    6: {"dt30", "dt60", "dt120", "dt300", "dt600"},
    7: {"full"},
    8: {"qmle"},
    9: {"mixed", "pure_es"},
    10: {"d2_mc", "d2_closed"},
    11: {"full"},
    12: {"scratch"},
    13: {"animal_pretrain"},
    14: {"reptile"},
    15: {"drift_only", "two_step"},
    16: {"full"},
    17: {"uncond", "is_day", "weather", "terrain"},
    18: {"full"},
    19: {"em", "euler"},
    20: {"full"},
    21: {"mc", "crn"},
    22: {"doob", "sb", "soft_endpoint"},
}
FULL_ANCHORS = {1, 7, 11, 16, 18, 20}
GROUP_COUNTS = {"model": 8, "algorithm": 4, "learning": 5, "inference": 5}
BOOTSTRAP_ITERATIONS = 1000
BOOTSTRAP_SEED = 20260814
COMPARISON_REFERENCE_BY_ARM = {
    1: (1, "full"),
    2: (1, "full"),
    3: (1, "full"),
    4: (1, "full"),
    5: (1, "full"),
    6: (6, "dt60"),
    7: (7, "full"),
    8: (7, "full"),
    9: (7, "full"),
    10: (10, "d2_mc"),
    11: (11, "full"),
    12: (11, "full"),
    13: (11, "full"),
    14: (11, "full"),
    15: (11, "full"),
    16: (16, "full"),
    17: (16, "full"),
    18: (18, "full"),
    19: (18, "full"),
    20: (20, "full"),
    21: (20, "full"),
    22: None,
}
STAGES = (
    "load_versioned_data",
    "build_transition_samples",
    "adapt_features",
    "initialize_model",
    "train",
    "checkpoint",
    "inference",
    "metrics",
    "mechanism_gates",
    "run_record",
    "tsde_ready",
)
REQUIRED_RECORD_FIELDS = {
    "schema_version",
    "experiment_id",
    "spec_version",
    "run_id",
    "result_id",
    "arm_id",
    "subconfig_id",
    "group",
    "lineage",
    "implementation_status",
    "run_status",
    "verdict",
    "dataset",
    "config",
    "runtime",
    "seed",
    "replicate_seed",
    "stages",
    "artifacts",
    "metrics",
    "mechanism_gates",
}
VERDICTS = {
    "not_assessed",
    "retain",
    "redundant",
    "harmful",
    "inconclusive",
    "unavailable",
}
SUCCESS_ARTIFACTS = {"checkpoint", "predictions", "metrics", "mechanism"}
SUCCESS_METRICS = {"energy_score_d2", "hdr90_coverage", "cep50_error"}
PROCESS_HEADER = (
    "arm_id",
    "subconfig_id",
    "group",
    "slot",
    "idea_ids",
    "lineage_role",
    "lineage_confidence",
    "implementation_status",
    "run_status",
    "verdict",
    "dataset_id",
    "requested_prediction_samples",
    "effective_prediction_samples",
    "replicate_seed",
    "result_id",
    "energy_score_d2",
    "hdr90_coverage",
    "cep50_error",
    "mechanism_statistic",
    "mechanism_value",
    "mechanism_threshold",
    "mechanism_passed",
)
STATUS_HEADER = (
    "arm_id",
    "execution_count",
    "implementation_status",
    "run_status",
    "verdict",
    "mechanism_status",
    "subconfigs",
    "idea_ids",
)
COMPARISON_HEADER = (
    "arm_id",
    "subconfig_id",
    "slot",
    "run_status",
    "verdict",
    "comparison_status",
    "reference_arm_id",
    "reference_subconfig_id",
    "assessment",
    "energy_score_d2",
    "reference_energy_score_d2",
    "delta_energy_score_d2",
    "relative_delta_energy_score_pct",
    "hdr90_coverage",
    "reference_hdr90_coverage",
    "delta_hdr90_coverage",
    "delta_hdr90_abs_error_from_90",
    "cep50_error",
    "reference_cep50_error",
    "delta_cep50_error",
    "relative_delta_cep50_error_pct",
    "bootstrap_status",
    "bootstrap_unit",
    "bootstrap_iterations",
    "paired_segment_count",
    "delta_energy_score_d2_ci95_low",
    "delta_energy_score_d2_ci95_high",
    "delta_hdr90_coverage_ci95_low",
    "delta_hdr90_coverage_ci95_high",
    "delta_cep50_error_ci95_low",
    "delta_cep50_error_ci95_high",
)


class AggregateError(ValueError):
    """RunRecords are incomplete, ambiguous, or incompatible."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_directory_artifacts(root: Path, record: Mapping[str, object]) -> None:
    artifacts = record.get("artifacts")
    if not isinstance(artifacts, Mapping) or not artifacts:
        raise AggregateError("directory RunRecord lacks artifact references")
    resolved_root = root.resolve()
    for name, reference in artifacts.items():
        if not isinstance(reference, Mapping):
            raise AggregateError(f"artifact {name} has an invalid reference")
        relative = reference.get("path")
        if not isinstance(relative, str) or not relative:
            raise AggregateError(f"artifact {name} has no path")
        artifact_path = (root / relative).resolve()
        try:
            artifact_path.relative_to(resolved_root)
        except ValueError as exc:
            raise AggregateError(f"artifact {name} escapes the records root") from exc
        if not artifact_path.is_file():
            raise AggregateError(f"artifact {name} is missing: {relative}")
        if artifact_path.stat().st_size != reference.get("size_bytes"):
            raise AggregateError(f"artifact {name} size mismatch: {relative}")
        if _sha256(artifact_path) != reference.get("sha256"):
            raise AggregateError(f"artifact {name} SHA-256 mismatch: {relative}")


def load_records(source: Path | str) -> list[dict[str, object]]:
    path = Path(source)
    if path.is_dir():
        record_paths = sorted(path.glob("*/run_record.json"))
        if not record_paths:
            raise AggregateError(f"no run_record.json files under {path}")
        records = [json.loads(item.read_text(encoding="utf-8")) for item in record_paths]
        for record in records:
            _verify_directory_artifacts(path, record)
        return records
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "records" in payload:
        payload = payload["records"]
    if not isinstance(payload, list):
        raise AggregateError("record fixture must contain a JSON list or {records: [...]} object")
    return [dict(item) for item in payload]


def validate_records(records: Sequence[Mapping[str, object]]) -> None:
    if not records:
        raise AggregateError("no NEX326 records supplied")
    keys: set[tuple[int, str]] = set()
    anchor_ids: set[int] = set()
    anchor_configs: set[str] = set()
    protocol_seeds: set[int] = set()
    replicate_seeds: set[int] = set()
    dataset_identities: set[tuple[object, object]] = set()
    implementation_bundles: set[str] = set()
    execution_identities: set[str] = set()
    implementation_presence: list[bool] = []
    for record in records:
        missing = REQUIRED_RECORD_FIELDS - record.keys()
        if missing:
            raise AggregateError(f"RunRecord missing required fields: {sorted(missing)}")
        if record.get("schema_version") != SCHEMA_VERSION:
            raise AggregateError("incompatible RunRecord schema")
        if record.get("experiment_id") != "NEX326" or record.get("spec_version") != SPEC_VERSION:
            raise AggregateError("incompatible experiment identity")
        arm_id = int(record["arm_id"])
        subconfig_id = str(record["subconfig_id"])
        key = (arm_id, subconfig_id)
        if key in keys:
            raise AggregateError(f"duplicate execution {key}")
        keys.add(key)
        if record.get("implementation_status") != "implemented":
            raise AggregateError(f"arm {arm_id} is not implemented")
        implementation = record.get("implementation")
        implementation_presence.append(implementation is not None)
        if implementation is not None:
            if not isinstance(implementation, Mapping):
                raise AggregateError(f"arm {arm_id} has an invalid implementation identity")
            source_bundle = implementation.get("source_bundle_sha256")
            execution_identity = implementation.get("execution_identity_sha256")
            if (
                not isinstance(source_bundle, str)
                or len(source_bundle) != 64
                or any(character not in "0123456789abcdef" for character in source_bundle)
                or not isinstance(execution_identity, str)
                or len(execution_identity) != 64
                or any(
                    character not in "0123456789abcdef"
                    for character in execution_identity
                )
            ):
                raise AggregateError(f"arm {arm_id} has an invalid execution identity")
            implementation_bundles.add(source_bundle)
            execution_identities.add(execution_identity)
        replicate_seed = record.get("replicate_seed")
        if (
            isinstance(replicate_seed, bool)
            or not isinstance(replicate_seed, int)
            or not 0 <= replicate_seed < 2**32
        ):
            raise AggregateError(f"arm {arm_id} has an invalid replicate seed")
        replicate_seeds.add(replicate_seed)
        protocol_seed = record.get("seed")
        if isinstance(protocol_seed, bool) or not isinstance(protocol_seed, int):
            raise AggregateError(f"arm {arm_id} has an invalid protocol seed")
        protocol_seeds.add(protocol_seed)
        dataset = record.get("dataset")
        if not isinstance(dataset, Mapping) or not dataset.get("dataset_id"):
            raise AggregateError(f"arm {arm_id} lacks a dataset identity")
        dataset_identities.add((dataset.get("dataset_id"), dataset.get("fingerprint")))
        run_status = record.get("run_status")
        if run_status not in {"succeeded", "data_unavailable", "failed"}:
            raise AggregateError(f"arm {arm_id} has invalid run status")
        verdict = record.get("verdict")
        if verdict not in VERDICTS:
            raise AggregateError(f"arm {arm_id} has invalid verdict")
        lineage = record.get("lineage")
        if not isinstance(lineage, Mapping) or not lineage.get("idea_ids") or not lineage.get("sources"):
            raise AggregateError(f"arm {arm_id} lacks auditable lineage")
        metrics = record.get("metrics")
        runtime = record.get("runtime")
        artifacts = record.get("artifacts")
        stages = record.get("stages")
        if not isinstance(metrics, Mapping):
            raise AggregateError(f"arm {arm_id} lacks metrics")
        if not isinstance(runtime, Mapping):
            raise AggregateError(f"arm {arm_id} lacks runtime metadata")
        requested_samples = runtime.get("requested_prediction_samples")
        effective_samples = runtime.get("effective_prediction_samples")
        if (
            isinstance(requested_samples, bool)
            or not isinstance(requested_samples, int)
            or requested_samples <= 0
        ):
            raise AggregateError(f"arm {arm_id} has invalid requested prediction samples")
        if run_status != "succeeded" and effective_samples is not None:
            raise AggregateError(
                f"non-successful arm {arm_id} cannot claim effective prediction samples"
            )
        if not isinstance(artifacts, Mapping) or not artifacts:
            raise AggregateError(f"arm {arm_id} lacks artifact references")
        if (
            not isinstance(stages, list)
            or not all(isinstance(stage, Mapping) for stage in stages)
            or [stage.get("name") for stage in stages] != list(STAGES)
        ):
            raise AggregateError(f"arm {arm_id} has an invalid stage sequence")
        if run_status == "succeeded":
            if (
                isinstance(effective_samples, bool)
                or not isinstance(effective_samples, int)
                or effective_samples < requested_samples
            ):
                raise AggregateError(f"arm {arm_id} has invalid effective prediction samples")
            if verdict == "unavailable":
                raise AggregateError(f"successful arm {arm_id} cannot be unavailable")
            if not SUCCESS_METRICS <= metrics.keys():
                raise AggregateError(f"successful arm {arm_id} lacks registered metrics")
            if not SUCCESS_ARTIFACTS <= artifacts.keys():
                raise AggregateError(f"successful arm {arm_id} lacks required artifacts")
            if any(stage.get("status") != "completed" for stage in stages):
                raise AggregateError(f"successful arm {arm_id} has incomplete stages")
        elif run_status == "data_unavailable":
            failure = record.get("failure")
            if verdict != "unavailable":
                raise AggregateError(f"data_unavailable arm {arm_id} requires unavailable verdict")
            if not isinstance(failure, Mapping) or not failure.get("reason"):
                raise AggregateError(f"data_unavailable arm {arm_id} lacks a reason")
            if "availability" not in artifacts:
                raise AggregateError(f"data_unavailable arm {arm_id} lacks availability artifact")
        gates = record.get("mechanism_gates")
        if not isinstance(gates, list) or not gates:
            raise AggregateError(f"arm {arm_id} lacks recomputable mechanism statistics")
        for gate in gates:
            if not isinstance(gate, Mapping) or not {
                "statistic",
                "value",
                "threshold",
                "operator",
                "passed",
                "sample_size",
            } <= gate.keys():
                raise AggregateError(f"arm {arm_id} mechanism gate is only a label/boolean")
            if (
                isinstance(gate["value"], bool)
                or not isinstance(gate["value"], Real)
                or isinstance(gate["threshold"], bool)
                or not isinstance(gate["threshold"], Real)
                or not isinstance(gate["passed"], bool)
                or isinstance(gate["sample_size"], bool)
                or not isinstance(gate["sample_size"], int)
                or gate["sample_size"] < 0
            ):
                raise AggregateError(f"arm {arm_id} mechanism gate has invalid statistic values")
        if record.get("is_full_anchor"):
            anchor_ids.add(arm_id)
            anchor_configs.add(json.dumps(record.get("config"), sort_keys=True, separators=(",", ":")))
            if record.get("full_config_id") != "NEX326-FULL-v2":
                raise AggregateError(f"arm {arm_id} references a different Full configuration")
    arms = {arm_id for arm_id, _ in keys}
    if arms != EXPECTED_ARMS:
        # This explicitly rejects the historical same-name eight-arm result.
        raise AggregateError(
            f"NEX326 requires arms 1..22; observed {len(arms)}: {sorted(arms)}"
        )
    expected_keys = {
        (arm_id, subconfig_id)
        for arm_id, subconfig_ids in EXPECTED_EXECUTIONS.items()
        for subconfig_id in subconfig_ids
    }
    if keys != expected_keys:
        missing = sorted(expected_keys - keys)
        unexpected = sorted(keys - expected_keys)
        raise AggregateError(
            "NEX326 requires the exact 36-execution matrix; "
            f"missing={missing}, unexpected={unexpected}"
        )
    arm_groups: dict[int, set[str]] = defaultdict(set)
    for record in records:
        arm_groups[int(record["arm_id"])].add(str(record["group"]))
    if any(len(groups) != 1 for groups in arm_groups.values()):
        raise AggregateError("one arm cannot appear in multiple groups")
    observed_counts = Counter(next(iter(groups)) for groups in arm_groups.values())
    if dict(observed_counts) != GROUP_COUNTS:
        raise AggregateError(f"group counts must be {GROUP_COUNTS}, got {dict(observed_counts)}")
    if anchor_ids != FULL_ANCHORS or len(anchor_configs) != 1:
        raise AggregateError("the six Full slot anchors are missing or do not share one configuration")
    if len(replicate_seeds) != 1:
        raise AggregateError("one aggregate may contain exactly one replicate seed")
    if len(protocol_seeds) != 1:
        raise AggregateError("one aggregate may contain exactly one protocol seed")
    if len(dataset_identities) != 1:
        raise AggregateError("one aggregate may contain exactly one dataset identity")
    if any(implementation_presence) and not all(implementation_presence):
        raise AggregateError("RunRecords mix missing and present implementation identities")
    if len(implementation_bundles) > 1:
        raise AggregateError("RunRecords contain multiple implementation source bundles")
    if len(execution_identities) > 1:
        raise AggregateError("RunRecords contain multiple execution identities")


def _write_process(records: Sequence[Mapping[str, object]], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=PROCESS_HEADER)
        writer.writeheader()
        for record in sorted(records, key=lambda item: (int(item["arm_id"]), str(item["subconfig_id"]))):
            lineage = record["lineage"]
            metrics = record["metrics"]
            gate = record["mechanism_gates"][0]
            writer.writerow(
                {
                    "arm_id": record["arm_id"],
                    "subconfig_id": record["subconfig_id"],
                    "group": record["group"],
                    "slot": record.get("slot", ""),
                    "idea_ids": ";".join(lineage["idea_ids"]),
                    "lineage_role": lineage["role"],
                    "lineage_confidence": lineage["confidence"],
                    "implementation_status": record["implementation_status"],
                    "run_status": record["run_status"],
                    "verdict": record["verdict"],
                    "dataset_id": record["dataset"]["dataset_id"],
                    "requested_prediction_samples": record["runtime"][
                        "requested_prediction_samples"
                    ],
                    "effective_prediction_samples": record["runtime"][
                        "effective_prediction_samples"
                    ]
                    or "",
                    "replicate_seed": record["replicate_seed"],
                    "result_id": record["result_id"],
                    "energy_score_d2": metrics.get("energy_score_d2", ""),
                    "hdr90_coverage": metrics.get("hdr90_coverage", ""),
                    "cep50_error": metrics.get("cep50_error", ""),
                    "mechanism_statistic": gate["statistic"],
                    "mechanism_value": gate["value"],
                    "mechanism_threshold": gate["threshold"],
                    "mechanism_passed": gate.get("passed", ""),
                }
            )


def _collapse(values: Iterable[str]) -> str:
    counts = Counter(values)
    return next(iter(counts)) if len(counts) == 1 else "mixed:" + ";".join(f"{key}={counts[key]}" for key in sorted(counts))


def _mechanism_status(record: Mapping[str, object]) -> str:
    if record["run_status"] != "succeeded":
        return "not_run"
    return "passed" if all(gate["passed"] for gate in record["mechanism_gates"]) else "failed"


def _write_status(records: Sequence[Mapping[str, object]], path: Path) -> None:
    grouped: dict[int, list[Mapping[str, object]]] = defaultdict(list)
    for record in records:
        grouped[int(record["arm_id"])].append(record)
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=STATUS_HEADER)
        writer.writeheader()
        for arm_id in range(1, 23):
            arm_records = grouped[arm_id]
            writer.writerow(
                {
                    "arm_id": arm_id,
                    "execution_count": len(arm_records),
                    "implementation_status": _collapse(str(item["implementation_status"]) for item in arm_records),
                    "run_status": _collapse(str(item["run_status"]) for item in arm_records),
                    "verdict": _collapse(str(item["verdict"]) for item in arm_records),
                    "mechanism_status": _collapse(
                        _mechanism_status(item) for item in arm_records
                    ),
                    "subconfigs": ";".join(sorted(str(item["subconfig_id"]) for item in arm_records)),
                    "idea_ids": ";".join(sorted({idea for item in arm_records for idea in item["lineage"]["idea_ids"]})),
                }
            )


def _relative_delta(value: float, reference: float) -> float | str:
    if reference == 0.0:
        return ""
    return 100.0 * (value - reference) / abs(reference)


def _comparison_rows(
    records: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    by_execution = {
        (int(record["arm_id"]), str(record["subconfig_id"])): record
        for record in records
    }
    rows: list[dict[str, object]] = []
    for record in sorted(
        records, key=lambda item: (int(item["arm_id"]), str(item["subconfig_id"]))
    ):
        arm_id = int(record["arm_id"])
        subconfig_id = str(record["subconfig_id"])
        key = (arm_id, subconfig_id)
        reference_key = COMPARISON_REFERENCE_BY_ARM[arm_id]
        reference = by_execution.get(reference_key) if reference_key is not None else None
        if record["run_status"] != "succeeded":
            comparison_status = "data_unavailable"
        elif key == (17, "terrain"):
            comparison_status = "requires_coverage_matched_reference"
        elif reference_key is None:
            comparison_status = "no_registered_reference"
        elif reference is None or reference["run_status"] != "succeeded":
            comparison_status = "reference_unavailable"
        elif key == reference_key:
            comparison_status = "reference"
        else:
            comparison_status = "exploratory_point_estimate"

        metrics = record["metrics"]
        reference_metrics = reference["metrics"] if reference is not None else {}
        comparable = comparison_status in {"reference", "exploratory_point_estimate"}

        def metric(name: str) -> float | str:
            return float(metrics[name]) if name in metrics else ""

        def reference_metric(name: str) -> float | str:
            return float(reference_metrics[name]) if name in reference_metrics else ""

        energy = metric("energy_score_d2")
        reference_energy = reference_metric("energy_score_d2")
        coverage = metric("hdr90_coverage")
        reference_coverage = reference_metric("hdr90_coverage")
        cep50 = metric("cep50_error")
        reference_cep50 = reference_metric("cep50_error")
        rows.append(
            {
                "arm_id": arm_id,
                "subconfig_id": subconfig_id,
                "slot": record.get("slot", ""),
                "run_status": record["run_status"],
                "verdict": record["verdict"],
                "comparison_status": comparison_status,
                "reference_arm_id": reference_key[0] if reference_key is not None else "",
                "reference_subconfig_id": (
                    reference_key[1] if reference_key is not None else ""
                ),
                "assessment": "not_assessed",
                "energy_score_d2": energy,
                "reference_energy_score_d2": reference_energy,
                "delta_energy_score_d2": (
                    energy - reference_energy if comparable else ""
                ),
                "relative_delta_energy_score_pct": (
                    _relative_delta(energy, reference_energy) if comparable else ""
                ),
                "hdr90_coverage": coverage,
                "reference_hdr90_coverage": reference_coverage,
                "delta_hdr90_coverage": coverage - reference_coverage if comparable else "",
                "delta_hdr90_abs_error_from_90": (
                    abs(coverage - 0.9) - abs(reference_coverage - 0.9)
                    if comparable
                    else ""
                ),
                "cep50_error": cep50,
                "reference_cep50_error": reference_cep50,
                "delta_cep50_error": cep50 - reference_cep50 if comparable else "",
                "relative_delta_cep50_error_pct": (
                    _relative_delta(cep50, reference_cep50) if comparable else ""
                ),
                "bootstrap_status": "",
                "bootstrap_unit": "",
                "bootstrap_iterations": "",
                "paired_segment_count": "",
                "delta_energy_score_d2_ci95_low": "",
                "delta_energy_score_d2_ci95_high": "",
                "delta_hdr90_coverage_ci95_low": "",
                "delta_hdr90_coverage_ci95_high": "",
                "delta_cep50_error_ci95_low": "",
                "delta_cep50_error_ci95_high": "",
            }
        )
    return rows


def _quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _prediction_statistics(
    records_root: Path, record: Mapping[str, object]
) -> dict[str, dict[str, object]]:
    reference = record["artifacts"]["predictions"]
    path = (records_root / reference["path"]).resolve()
    try:
        path.relative_to(records_root.resolve())
    except ValueError as exc:
        raise AggregateError("prediction artifact escapes records root") from exc
    payload = json.loads(path.read_text(encoding="utf-8"))
    predictions = payload.get("predictions")
    if not isinstance(predictions, list) or not predictions:
        raise AggregateError(f"arm {record['arm_id']} prediction artifact is empty")
    use_empirical_energy = record["config"].get("score", "d2_mc") != "d2_closed"
    statistics: dict[str, dict[str, object]] = {}
    for prediction in predictions:
        segment_id = str(prediction["segment_id"])
        target = tuple(float(value) for value in prediction["target"])
        samples = [tuple(float(value) for value in sample) for sample in prediction["samples"]]
        if not samples:
            raise AggregateError(f"arm {record['arm_id']} has an empty prediction sample")
        center = tuple(sum(sample[axis] for sample in samples) / len(samples) for axis in (0, 1))
        radii = [math.dist(sample, center) for sample in samples]
        target_radius = math.dist(target, center)
        empirical_energy = None
        if use_empirical_energy:
            first = sum(math.dist(sample, target) for sample in samples) / len(samples)
            second = sum(
                math.dist(sample, samples[index - 1])
                for index, sample in enumerate(samples)
            ) / len(samples)
            empirical_energy = first - 0.5 * second
        if segment_id in statistics:
            raise AggregateError(f"arm {record['arm_id']} repeats segment {segment_id}")
        statistics[segment_id] = {
            "target": target,
            "energy": empirical_energy,
            "coverage": float(target_radius <= _quantile(radii, 0.9)),
            "cep50": target_radius,
        }
    aggregate_checks = {
        "hdr90_coverage": sum(float(item["coverage"]) for item in statistics.values())
        / len(statistics),
        "cep50_error": median(float(item["cep50"]) for item in statistics.values()),
    }
    if use_empirical_energy:
        aggregate_checks["energy_score_d2"] = sum(
            float(item["energy"]) for item in statistics.values()
        ) / len(statistics)
    for metric_name, recomputed in aggregate_checks.items():
        recorded = float(record["metrics"][metric_name])
        if not math.isclose(recomputed, recorded, rel_tol=1e-10, abs_tol=1e-10):
            raise AggregateError(
                f"arm {record['arm_id']} predictions do not reproduce {metric_name}"
            )
    return statistics


def _bootstrap_interval(values: Sequence[float]) -> tuple[float, float]:
    return _quantile(values, 0.025), _quantile(values, 0.975)


def _attach_bootstrap_uncertainty(
    rows: list[dict[str, object]],
    records: Sequence[Mapping[str, object]],
    records_root: Path | None,
) -> Counter[str]:
    by_execution = {
        (int(record["arm_id"]), str(record["subconfig_id"])): record
        for record in records
    }
    cache: dict[tuple[int, str], dict[str, dict[str, object]]] = {}
    status = Counter()
    for row in rows:
        comparison_status = str(row["comparison_status"])
        if comparison_status == "reference":
            row["bootstrap_status"] = "reference"
        elif comparison_status != "exploratory_point_estimate":
            row["bootstrap_status"] = "not_applicable"
        elif records_root is None:
            row["bootstrap_status"] = "predictions_not_loaded"
        else:
            key = (int(row["arm_id"]), str(row["subconfig_id"]))
            reference_key = (
                int(row["reference_arm_id"]), str(row["reference_subconfig_id"])
            )
            for execution_key in (key, reference_key):
                if execution_key not in cache:
                    cache[execution_key] = _prediction_statistics(
                        records_root, by_execution[execution_key]
                    )
            current = cache[key]
            reference = cache[reference_key]
            if set(current) != set(reference) or any(
                current[name]["target"] != reference[name]["target"] for name in current
            ):
                row["bootstrap_status"] = "segment_alignment_failed"
                status[str(row["bootstrap_status"])] += 1
                continue
            segment_ids = sorted(current)
            rng_seed = BOOTSTRAP_SEED + int(
                hashlib.sha256(f"{key}:{reference_key}".encode()).hexdigest()[:8], 16
            )
            rng = random.Random(rng_seed)
            energy_deltas: list[float] = []
            coverage_deltas: list[float] = []
            cep50_deltas: list[float] = []
            energy_available = all(
                current[name]["energy"] is not None
                and reference[name]["energy"] is not None
                for name in segment_ids
            )
            for _ in range(BOOTSTRAP_ITERATIONS):
                selected = [rng.choice(segment_ids) for _ in segment_ids]
                coverage_deltas.append(
                    sum(float(current[name]["coverage"]) for name in selected) / len(selected)
                    - sum(float(reference[name]["coverage"]) for name in selected)
                    / len(selected)
                )
                cep50_deltas.append(
                    median(float(current[name]["cep50"]) for name in selected)
                    - median(float(reference[name]["cep50"]) for name in selected)
                )
                if energy_available:
                    energy_deltas.append(
                        sum(float(current[name]["energy"]) for name in selected) / len(selected)
                        - sum(float(reference[name]["energy"]) for name in selected)
                        / len(selected)
                    )
            row["bootstrap_status"] = (
                "complete" if energy_available else "partial_closed_energy_not_resampled"
            )
            row["bootstrap_unit"] = "paired_evaluation_segment"
            row["bootstrap_iterations"] = BOOTSTRAP_ITERATIONS
            row["paired_segment_count"] = len(segment_ids)
            if energy_deltas:
                (
                    row["delta_energy_score_d2_ci95_low"],
                    row["delta_energy_score_d2_ci95_high"],
                ) = _bootstrap_interval(energy_deltas)
            (
                row["delta_hdr90_coverage_ci95_low"],
                row["delta_hdr90_coverage_ci95_high"],
            ) = _bootstrap_interval(coverage_deltas)
            (
                row["delta_cep50_error_ci95_low"],
                row["delta_cep50_error_ci95_high"],
            ) = _bootstrap_interval(cep50_deltas)
        status[str(row["bootstrap_status"])] += 1
    return status


def _write_comparisons(
    records: Sequence[Mapping[str, object]], path: Path, records_root: Path | None
) -> tuple[Counter[str], Counter[str]]:
    rows = _comparison_rows(records)
    uncertainty_status = _attach_bootstrap_uncertainty(rows, records, records_root)
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=COMPARISON_HEADER)
        writer.writeheader()
        writer.writerows(rows)
    return (
        Counter(str(row["comparison_status"]) for row in rows),
        uncertainty_status,
    )


def _output_reference(path: Path) -> dict[str, object]:
    return {
        "path": path.name,
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
    }


def _write_svg(records: Sequence[Mapping[str, object]], path: Path) -> None:
    points = [
        (int(record["arm_id"]), float(record["metrics"]["energy_score_d2"]))
        for record in records
        if record["run_status"] == "succeeded" and "energy_score_d2" in record["metrics"]
    ]
    width, height, margin = 920, 420, 50
    if points:
        values = [value for _, value in points]
        low, high = min(values), max(values)
        span = max(high - low, 1e-9)
    else:
        low, span = 0.0, 1.0
    circles = []
    for arm_id, value in points:
        x = margin + (arm_id - 1) / 21 * (width - 2 * margin)
        y = height - margin - (value - low) / span * (height - 2 * margin)
        circles.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="#2563eb"><title>arm {arm_id}: energy={html.escape(f"{value:.6g}")}</title></circle>'
        )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        '<rect width="100%" height="100%" fill="white"/>'
        f'<line x1="{margin}" y1="{height-margin}" x2="{width-margin}" y2="{height-margin}" stroke="#111827"/>'
        f'<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height-margin}" stroke="#111827"/>'
        '<text x="460" y="405" text-anchor="middle" font-family="sans-serif" font-size="13">NEX326 arm</text>'
        '<text x="16" y="210" transform="rotate(-90 16 210)" text-anchor="middle" font-family="sans-serif" font-size="13">energy score (lower is better)</text>'
        + "".join(circles)
        + "</svg>"
    )
    path.write_text(svg, encoding="utf-8")


def aggregate(
    records: Sequence[Mapping[str, object]],
    output: Path | str,
    *,
    records_root: Path | str | None = None,
) -> dict[str, object]:
    validate_records(records)
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    process_path = destination / "nex326_process.csv"
    status_path = destination / "nex326_status.csv"
    comparison_path = destination / "nex326_pilot_comparisons.csv"
    plot_path = destination / "nex326_test_plot.svg"
    _write_process(records, process_path)
    _write_status(records, status_path)
    comparison_status, uncertainty_status = _write_comparisons(
        records,
        comparison_path,
        Path(records_root) if records_root is not None else None,
    )
    _write_svg(records, plot_path)
    summary = {
        "schema_version": "nex326-tsde-aggregate-v1",
        "spec_version": SPEC_VERSION,
        "arm_count": 22,
        "execution_count": len(records),
        "protocol_seed": next(iter({int(item["seed"]) for item in records})),
        "replicate_seed": next(iter({int(item["replicate_seed"]) for item in records})),
        "dataset_id": next(
            iter({str(item["dataset"].get("dataset_id")) for item in records})
        ),
        "dataset_fingerprint": next(
            iter({item["dataset"].get("fingerprint") for item in records})
        ),
        "implementation_status": dict(Counter(str(item["implementation_status"]) for item in records)),
        "implementation_source_bundle_sha256": next(
            iter(
                {
                    item["implementation"]["source_bundle_sha256"]
                    for item in records
                    if item.get("implementation")
                }
            ),
            None,
        ),
        "implementation_execution_identity_sha256": next(
            iter(
                {
                    item["implementation"]["execution_identity_sha256"]
                    for item in records
                    if item.get("implementation")
                }
            ),
            None,
        ),
        "run_status": dict(Counter(str(item["run_status"]) for item in records)),
        "verdict": dict(Counter(str(item["verdict"]) for item in records)),
        "mechanism_status": dict(Counter(_mechanism_status(item) for item in records)),
        "requested_prediction_samples": sorted(
            {int(item["runtime"]["requested_prediction_samples"]) for item in records}
        ),
        "effective_prediction_samples": dict(
            Counter(
                "not_run"
                if item["runtime"]["effective_prediction_samples"] is None
                else str(item["runtime"]["effective_prediction_samples"])
                for item in records
            )
        ),
        "comparison": {
            "scientific_status": "exploratory_only",
            "assessment": "not_assessed",
            "method": "registered_reference_point_estimates",
            "uncertainty_method": "paired_evaluation_segment_bootstrap_only",
            "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "status": dict(comparison_status),
            "uncertainty_status": dict(uncertainty_status),
        },
        "artifacts": {
            path.name: _output_reference(path)
            for path in (process_path, status_path, comparison_path, plot_path)
        },
    }
    (destination / "nex326_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = aggregate(
        load_records(args.records),
        args.output,
        records_root=args.records if args.records.is_dir() else None,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
