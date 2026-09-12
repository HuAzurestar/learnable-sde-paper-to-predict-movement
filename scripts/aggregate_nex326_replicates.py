"""Aggregate multiple validated NEX326 replicate summaries without issuing a verdict."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import mean, stdev
from typing import Mapping, Sequence


METRICS = (
    "delta_energy_score_d2",
    "delta_hdr90_coverage",
    "delta_cep50_error",
)
OUTPUT_HEADER = (
    "arm_id",
    "subconfig_id",
    "slot",
    "comparison_status",
    "replicate_status",
    "replicate_count",
    "replicate_seeds",
    "assessment",
    *(
        f"{metric}_{suffix}"
        for metric in METRICS
        for suffix in ("mean", "sample_std", "min", "max", "sign_consistency")
    ),
)


class ReplicateAggregateError(ValueError):
    """Replicate manifests or summaries are incomplete, inconsistent, or tampered."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_mapping(path: Path, label: str) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ReplicateAggregateError(f"{label} must contain a JSON object")
    return payload


def _verified_artifact(root: Path, reference: Mapping[str, object], label: str) -> Path:
    relative = reference.get("path")
    if not isinstance(relative, str) or not relative:
        raise ReplicateAggregateError(f"{label} has no path")
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ReplicateAggregateError(f"{label} escapes its declared root") from exc
    if not path.is_file():
        raise ReplicateAggregateError(f"{label} is missing")
    if path.stat().st_size != reference.get("size_bytes"):
        raise ReplicateAggregateError(f"{label} size mismatch")
    if _sha256(path) != reference.get("sha256"):
        raise ReplicateAggregateError(f"{label} SHA-256 mismatch")
    return path


def _sign_consistency(values: Sequence[float]) -> str:
    signs = {0 if value == 0.0 else (1 if value > 0.0 else -1) for value in values}
    if signs == {1}:
        return "all_positive"
    if signs == {-1}:
        return "all_negative"
    if signs == {0}:
        return "all_zero"
    return "mixed"


def aggregate_replicates(
    batch_manifest_path: Path | str,
    summary_paths: Sequence[Path | str],
    output: Path | str,
) -> dict[str, object]:
    batch_file = Path(batch_manifest_path)
    batch_root = batch_file.parent.resolve()
    batch = _load_mapping(batch_file, "multi-seed manifest")
    if batch.get("schema_version") != "nex326-multi-seed-manifest-v1":
        raise ReplicateAggregateError("incompatible multi-seed manifest")
    batch_implementation = batch.get("implementation")
    batch_source_bundle = (
        batch_implementation.get("source_bundle_sha256")
        if isinstance(batch_implementation, Mapping)
        else None
    )
    batch_execution_identity = (
        batch_implementation.get("execution_identity_sha256")
        if isinstance(batch_implementation, Mapping)
        else None
    )
    if batch_implementation is not None and (
        not isinstance(batch_source_bundle, str)
        or len(batch_source_bundle) != 64
        or not isinstance(batch_execution_identity, str)
        or len(batch_execution_identity) != 64
    ):
        raise ReplicateAggregateError("batch has an invalid implementation source bundle")
    seeds = tuple(int(seed) for seed in batch.get("replicate_seeds", []))
    if len(seeds) < 2 or len(seeds) != len(set(seeds)):
        raise ReplicateAggregateError("batch must contain at least two unique replicate seeds")
    entries = batch.get("replicates")
    if not isinstance(entries, list) or len(entries) != len(seeds):
        raise ReplicateAggregateError("batch replicate entries do not match its seed list")
    for entry in entries:
        if not isinstance(entry, Mapping) or not isinstance(entry.get("manifest"), Mapping):
            raise ReplicateAggregateError("batch contains an invalid replicate entry")
        _verified_artifact(batch_root, entry["manifest"], "per-seed manifest")

    if len(summary_paths) != len(seeds):
        raise ReplicateAggregateError("one aggregate summary is required for every seed")
    summaries: dict[int, dict[str, object]] = {}
    comparison_rows: dict[int, list[dict[str, str]]] = {}
    inputs: list[dict[str, object]] = []
    for supplied in summary_paths:
        summary_path = Path(supplied).resolve()
        try:
            summary_path.relative_to(batch_root)
        except ValueError as exc:
            raise ReplicateAggregateError("aggregate summary escapes the batch root") from exc
        summary = _load_mapping(summary_path, "replicate aggregate summary")
        seed = int(summary.get("replicate_seed", -1))
        if seed not in seeds or seed in summaries:
            raise ReplicateAggregateError("aggregate summaries have unexpected or duplicate seeds")
        if (
            summary.get("schema_version") != "nex326-tsde-aggregate-v1"
            or summary.get("spec_version") != batch.get("spec_version")
            or summary.get("protocol_seed") != batch.get("protocol_seed")
            or summary.get("execution_count") != 36
            or summary.get("arm_count") != 22
            or summary.get("dataset_fingerprint") != batch.get("cohort", {}).get("fingerprint")
            or (
                batch_source_bundle is not None
                and summary.get("implementation_source_bundle_sha256")
                != batch_source_bundle
            )
            or (
                batch_execution_identity is not None
                and summary.get("implementation_execution_identity_sha256")
                != batch_execution_identity
            )
        ):
            raise ReplicateAggregateError(f"aggregate summary for seed {seed} is incompatible")
        artifacts = summary.get("artifacts")
        if not isinstance(artifacts, Mapping):
            raise ReplicateAggregateError(f"aggregate summary for seed {seed} lacks artifacts")
        comparison_reference = artifacts.get("nex326_pilot_comparisons.csv")
        if not isinstance(comparison_reference, Mapping):
            raise ReplicateAggregateError(f"aggregate summary for seed {seed} lacks comparisons")
        comparison_path = _verified_artifact(
            summary_path.parent, comparison_reference, f"seed {seed} comparisons"
        )
        with comparison_path.open(encoding="utf-8", newline="") as source:
            rows = list(csv.DictReader(source))
        if len(rows) != 36:
            raise ReplicateAggregateError(f"seed {seed} must contain 36 comparison rows")
        summaries[seed] = summary
        comparison_rows[seed] = rows
        inputs.append(
            {
                "replicate_seed": seed,
                "summary_path": summary_path.relative_to(batch_root).as_posix(),
                "summary_sha256": _sha256(summary_path),
                "comparisons_path": comparison_path.relative_to(batch_root).as_posix(),
                "comparisons_sha256": _sha256(comparison_path),
            }
        )
    if set(summaries) != set(seeds):
        raise ReplicateAggregateError("aggregate summaries do not cover the registered seeds")

    indexed: dict[int, dict[tuple[int, str], dict[str, str]]] = {}
    expected_keys: set[tuple[int, str]] | None = None
    for seed, rows in comparison_rows.items():
        index = {(int(row["arm_id"]), row["subconfig_id"]): row for row in rows}
        if len(index) != 36:
            raise ReplicateAggregateError(f"seed {seed} repeats a comparison execution")
        if expected_keys is None:
            expected_keys = set(index)
        elif set(index) != expected_keys:
            raise ReplicateAggregateError("replicate comparison matrices differ")
        indexed[seed] = index

    output_rows: list[dict[str, object]] = []
    for key in sorted(expected_keys or set()):
        rows = [indexed[seed][key] for seed in seeds]
        comparison_states = {row["comparison_status"] for row in rows}
        references = {
            (row["reference_arm_id"], row["reference_subconfig_id"]) for row in rows
        }
        if len(comparison_states) != 1 or len(references) != 1:
            raise ReplicateAggregateError(f"comparison contract differs across seeds for {key}")
        run_states = {row["run_status"] for row in rows}
        row_out: dict[str, object] = {
            "arm_id": key[0],
            "subconfig_id": key[1],
            "slot": rows[0]["slot"],
            "comparison_status": next(iter(comparison_states)),
            "replicate_status": next(iter(run_states)) if len(run_states) == 1 else "mixed",
            "replicate_count": len(seeds),
            "replicate_seeds": ";".join(str(seed) for seed in seeds),
            "assessment": "not_assessed",
        }
        for metric in METRICS:
            values = [float(row[metric]) for row in rows if row[metric] != ""]
            prefix = f"{metric}_"
            if len(values) == len(seeds):
                row_out.update(
                    {
                        prefix + "mean": mean(values),
                        prefix + "sample_std": stdev(values),
                        prefix + "min": min(values),
                        prefix + "max": max(values),
                        prefix + "sign_consistency": _sign_consistency(values),
                    }
                )
            else:
                row_out.update(
                    {
                        prefix + "mean": "",
                        prefix + "sample_std": "",
                        prefix + "min": "",
                        prefix + "max": "",
                        prefix + "sign_consistency": "not_available",
                    }
                )
        output_rows.append(row_out)

    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    table_path = destination / "nex326_cross_replicate_comparisons.csv"
    with table_path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=OUTPUT_HEADER)
        writer.writeheader()
        writer.writerows(output_rows)
    summary = {
        "schema_version": "nex326-tsde-replicate-aggregate-v1",
        "experiment_id": "NEX326",
        "spec_version": batch["spec_version"],
        "scientific_status": "exploratory_only",
        "assessment": "not_assessed",
        "method": "descriptive_across_replicate_seeds_no_inferential_ci",
        "protocol_seed": batch["protocol_seed"],
        "replicate_seeds": list(seeds),
        "replicate_count": len(seeds),
        "execution_count_per_replicate": 36,
        "dataset_fingerprint": batch["cohort"]["fingerprint"],
        "implementation_source_bundle_sha256": batch_source_bundle,
        "implementation_execution_identity_sha256": batch_execution_identity,
        "batch_manifest_sha256": _sha256(batch_file),
        "comparison_status": dict(Counter(row["comparison_status"] for row in output_rows)),
        "replicate_status": dict(Counter(row["replicate_status"] for row in output_rows)),
        "inputs": sorted(inputs, key=lambda item: int(item["replicate_seed"])),
        "artifacts": {
            table_path.name: {
                "path": table_path.name,
                "sha256": _sha256(table_path),
                "size_bytes": table_path.stat().st_size,
            }
        },
    }
    (destination / "nex326_replicate_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-manifest", type=Path, required=True)
    parser.add_argument("--summaries", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = aggregate_replicates(args.batch_manifest, args.summaries, args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["ReplicateAggregateError", "aggregate_replicates"]
