"""Aggregate compact NEX326 phase-space receipts and paired contrasts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import mean
from typing import Mapping, Sequence


RECEIPT_SCHEMA = "nex326-phase-space-dsde-receipt-v1"
CONTRAST_SCHEMA = "nex326-phase-space-paired-contrast-v1"
METRICS = (
    "position_energy_score_d2",
    "position_hdr90_coverage",
    "position_cep50_error",
    "velocity_endpoint_rmse",
)
MODEL_HEADER = (
    "benchmark_id",
    "scientific_role",
    "assessment",
    "primary_comparator",
    "replicate_count",
    "replicate_seeds",
    "prediction_samples_per_segment",
    *(f"{metric}_{suffix}" for metric in METRICS for suffix in ("mean", "sample_std")),
    "implementation_source_bundle_sha256",
    "receipt_sha256",
)
CONTRAST_HEADER = (
    "baseline_benchmark_id",
    "candidate_benchmark_id",
    "comparator_role",
    "conclusion",
    "replicate_seeds",
    "prediction_samples_per_segment",
    *(f"delta_{metric}_{suffix}" for metric in METRICS for suffix in ("mean", "candidate_better_seed_count")),
    "contrast_sha256",
)


class PhaseSpaceAggregateError(ValueError):
    """A compact phase-space evidence package is incomplete or inconsistent."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path, label: str) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PhaseSpaceAggregateError(f"{label} must contain a JSON object")
    return payload


def _hash(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise PhaseSpaceAggregateError(f"{label} must be a SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as error:
        raise PhaseSpaceAggregateError(f"{label} must be a SHA-256 digest") from error
    return value


def _finite(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PhaseSpaceAggregateError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise PhaseSpaceAggregateError(f"{label} must be finite")
    return result


def _validated_receipt(path: Path) -> dict[str, object]:
    receipt = _load(path, "phase-space receipt")
    if receipt.get("schema_version") != RECEIPT_SCHEMA:
        raise PhaseSpaceAggregateError("unsupported phase-space receipt schema")
    benchmark_id = receipt.get("benchmark_id")
    if not isinstance(benchmark_id, str) or not benchmark_id:
        raise PhaseSpaceAggregateError("phase-space receipt has no benchmark id")
    seeds = receipt.get("replicate_seeds")
    if (
        not isinstance(seeds, list)
        or len(seeds) < 2
        or len(seeds) != len(set(seeds))
        or any(isinstance(seed, bool) or not isinstance(seed, int) for seed in seeds)
        or receipt.get("replicate_count") != len(seeds)
    ):
        raise PhaseSpaceAggregateError(f"{benchmark_id} has invalid replicate seeds")
    cohort = receipt.get("cohort")
    if not isinstance(cohort, Mapping):
        raise PhaseSpaceAggregateError(f"{benchmark_id} has no cohort identity")
    _hash(cohort.get("fingerprint"), f"{benchmark_id} cohort fingerprint")
    implementation = receipt.get("implementation")
    if not isinstance(implementation, Mapping):
        raise PhaseSpaceAggregateError(f"{benchmark_id} has no implementation identity")
    _hash(
        implementation.get("source_bundle_sha256"),
        f"{benchmark_id} implementation source bundle",
    )
    integrity = receipt.get("integrity")
    if not isinstance(integrity, Mapping):
        raise PhaseSpaceAggregateError(f"{benchmark_id} has no integrity block")
    _hash(integrity.get("manifest_sha256"), f"{benchmark_id} manifest")
    summary = receipt.get("metric_summary")
    if not isinstance(summary, Mapping):
        raise PhaseSpaceAggregateError(f"{benchmark_id} has no metric summary")
    for metric in METRICS:
        values = summary.get(metric)
        if not isinstance(values, Mapping):
            raise PhaseSpaceAggregateError(f"{benchmark_id} lacks {metric}")
        _finite(values.get("mean"), f"{benchmark_id} {metric} mean")
        _finite(values.get("sample_std"), f"{benchmark_id} {metric} sample std")
    return receipt


def _validated_contrast(
    path: Path,
    receipts: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    contrast = _load(path, "phase-space contrast")
    if contrast.get("schema_version") != CONTRAST_SCHEMA:
        raise PhaseSpaceAggregateError("unsupported phase-space contrast schema")
    baseline_id = contrast.get("baseline_benchmark_id")
    candidate_id = contrast.get("candidate_benchmark_id")
    if baseline_id not in receipts or candidate_id not in receipts:
        raise PhaseSpaceAggregateError("contrast references a missing receipt")
    baseline = receipts[str(baseline_id)]
    candidate = receipts[str(candidate_id)]
    common = (
        ("cohort_fingerprint", baseline["cohort"]["fingerprint"]),
        ("replicate_seeds", baseline["replicate_seeds"]),
        (
            "prediction_samples_per_segment",
            baseline["prediction_samples_per_segment"],
        ),
    )
    if any(contrast.get(field) != expected for field, expected in common):
        raise PhaseSpaceAggregateError("contrast identity does not match its receipts")
    if any(
        candidate.get(field) != baseline.get(field)
        for field in ("replicate_seeds", "prediction_samples_per_segment")
    ) or candidate["cohort"]["fingerprint"] != baseline["cohort"]["fingerprint"]:
        raise PhaseSpaceAggregateError("contrast receipts do not share one protocol")
    integrity = contrast.get("integrity")
    if not isinstance(integrity, Mapping) or (
        integrity.get("baseline_manifest_sha256")
        != baseline["integrity"]["manifest_sha256"]
        or integrity.get("candidate_manifest_sha256")
        != candidate["integrity"]["manifest_sha256"]
    ):
        raise PhaseSpaceAggregateError("contrast manifest hashes do not match receipts")
    paired = contrast.get("paired_deltas")
    if not isinstance(paired, list) or [row.get("seed") for row in paired] != baseline[
        "replicate_seeds"
    ]:
        raise PhaseSpaceAggregateError("contrast paired rows do not match replicate seeds")
    delta_summary = contrast.get("delta_summary")
    if not isinstance(delta_summary, Mapping):
        raise PhaseSpaceAggregateError("contrast has no delta summary")
    for metric in METRICS:
        values = [
            _finite(
                row.get("candidate_minus_baseline", {}).get(metric),
                f"contrast {metric} delta",
            )
            for row in paired
        ]
        summary = delta_summary.get(metric)
        if not isinstance(summary, Mapping):
            raise PhaseSpaceAggregateError(f"contrast lacks {metric} summary")
        if not math.isclose(
            _finite(summary.get("mean"), f"contrast {metric} mean"),
            mean(values),
            rel_tol=1e-12,
            abs_tol=1e-12,
        ) or summary.get("candidate_better_seed_count") != sum(
            value < 0.0 for value in values
        ):
            raise PhaseSpaceAggregateError(f"contrast {metric} summary is inconsistent")
    primary = delta_summary["position_energy_score_d2"]
    observed_gain = (
        float(primary["mean"]) < 0.0
        and int(primary["candidate_better_seed_count"]) >= len(paired) // 2 + 1
    )
    expected_conclusion = (
        "observed_primary_metric_gain"
        if observed_gain
        else "no_observed_primary_metric_gain"
    )
    if contrast.get("conclusion") != expected_conclusion:
        raise PhaseSpaceAggregateError("contrast conclusion does not follow its gain rule")
    if contrast.get("comparator_role") == "registered_primary":
        protocol = candidate.get("registered_protocol")
        if not isinstance(protocol, Mapping) or protocol.get("primary_comparator") != baseline_id:
            raise PhaseSpaceAggregateError("registered primary comparator is inconsistent")
    return contrast


def aggregate_phase_space(
    receipt_paths: Sequence[Path | str],
    contrast_paths: Sequence[Path | str],
    output: Path | str,
) -> dict[str, object]:
    if len(receipt_paths) < 2:
        raise PhaseSpaceAggregateError("at least two phase-space receipts are required")
    receipt_files = [Path(path).resolve() for path in receipt_paths]
    contrast_files = [Path(path).resolve() for path in contrast_paths]
    receipts: dict[str, dict[str, object]] = {}
    for path in receipt_files:
        receipt = _validated_receipt(path)
        benchmark_id = str(receipt["benchmark_id"])
        if benchmark_id in receipts:
            raise PhaseSpaceAggregateError("phase-space benchmark receipt is duplicated")
        receipts[benchmark_id] = receipt
    cohort_fingerprints = {
        str(receipt["cohort"]["fingerprint"]) for receipt in receipts.values()
    }
    protocols = {
        (
            tuple(receipt["replicate_seeds"]),
            int(receipt["prediction_samples_per_segment"]),
        )
        for receipt in receipts.values()
    }
    if len(cohort_fingerprints) != 1 or len(protocols) != 1:
        raise PhaseSpaceAggregateError("phase-space receipts do not share one cohort and protocol")
    contrasts: list[dict[str, object]] = []
    seen_contrasts: set[tuple[str, str]] = set()
    for path in contrast_files:
        contrast = _validated_contrast(path, receipts)
        key = (
            str(contrast["baseline_benchmark_id"]),
            str(contrast["candidate_benchmark_id"]),
        )
        if key in seen_contrasts:
            raise PhaseSpaceAggregateError("phase-space contrast is duplicated")
        seen_contrasts.add(key)
        contrasts.append(contrast)

    model_rows: list[dict[str, object]] = []
    for path, receipt in sorted(
        zip(receipt_files, receipts.values()), key=lambda item: str(item[1]["benchmark_id"])
    ):
        protocol = receipt.get("registered_protocol")
        row: dict[str, object] = {
            "benchmark_id": receipt["benchmark_id"],
            "scientific_role": receipt["scientific_role"],
            "assessment": receipt["assessment"],
            "primary_comparator": (
                protocol.get("primary_comparator", "")
                if isinstance(protocol, Mapping)
                else ""
            ),
            "replicate_count": receipt["replicate_count"],
            "replicate_seeds": ";".join(str(seed) for seed in receipt["replicate_seeds"]),
            "prediction_samples_per_segment": receipt["prediction_samples_per_segment"],
            "implementation_source_bundle_sha256": receipt["implementation"][
                "source_bundle_sha256"
            ],
            "receipt_sha256": _sha256(path),
        }
        for metric in METRICS:
            row[f"{metric}_mean"] = receipt["metric_summary"][metric]["mean"]
            row[f"{metric}_sample_std"] = receipt["metric_summary"][metric][
                "sample_std"
            ]
        model_rows.append(row)

    contrast_rows: list[dict[str, object]] = []
    for path, contrast in sorted(
        zip(contrast_files, contrasts),
        key=lambda item: (
            str(item[1]["baseline_benchmark_id"]),
            str(item[1]["candidate_benchmark_id"]),
        ),
    ):
        row = {
            "baseline_benchmark_id": contrast["baseline_benchmark_id"],
            "candidate_benchmark_id": contrast["candidate_benchmark_id"],
            "comparator_role": contrast.get("comparator_role", "legacy_unregistered"),
            "conclusion": contrast["conclusion"],
            "replicate_seeds": ";".join(str(seed) for seed in contrast["replicate_seeds"]),
            "prediction_samples_per_segment": contrast[
                "prediction_samples_per_segment"
            ],
            "contrast_sha256": _sha256(path),
        }
        for metric in METRICS:
            summary = contrast["delta_summary"][metric]
            row[f"delta_{metric}_mean"] = summary["mean"]
            row[f"delta_{metric}_candidate_better_seed_count"] = summary[
                "candidate_better_seed_count"
            ]
        contrast_rows.append(row)

    destination = Path(output)
    model_path = destination / "nex326_phase_space_models.csv"
    contrast_path = destination / "nex326_phase_space_contrasts.csv"
    summary_path = destination / "nex326_phase_space_summary.json"
    if any(path.exists() for path in (model_path, contrast_path, summary_path)):
        raise PhaseSpaceAggregateError("one or more phase-space aggregate outputs exist")
    destination.mkdir(parents=True, exist_ok=True)
    for path, header, rows in (
        (model_path, MODEL_HEADER, model_rows),
        (contrast_path, CONTRAST_HEADER, contrast_rows),
    ):
        with path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)
    best = min(model_rows, key=lambda row: float(row["position_energy_score_d2_mean"]))
    summary = {
        "schema_version": "nex326-tsde-phase-space-aggregate-v1",
        "experiment_id": "NEX326",
        "scientific_status": "exploratory_only",
        "assessment": "not_assessed",
        "method": "descriptive_compact_receipt_and_paired_contrast_aggregation",
        "cohort_fingerprint": next(iter(cohort_fingerprints)),
        "replicate_seeds": list(next(iter(protocols))[0]),
        "prediction_samples_per_segment": next(iter(protocols))[1],
        "model_count": len(model_rows),
        "contrast_count": len(contrast_rows),
        "descriptive_lowest_energy_score_benchmark": best["benchmark_id"],
        "caveat": "Sampling-seed repeats share one fitted cohort and evaluation set; no inferential or scientific verdict is issued.",
        "inputs": {
            "receipts": [
                {"name": path.name, "sha256": _sha256(path)}
                for path in sorted(receipt_files)
            ],
            "contrasts": [
                {"name": path.name, "sha256": _sha256(path)}
                for path in sorted(contrast_files)
            ],
        },
        "artifacts": {
            path.name: {
                "path": path.name,
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
            }
            for path in (model_path, contrast_path)
        },
    }
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipts", type=Path, nargs="+", required=True)
    parser.add_argument("--contrasts", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = aggregate_phase_space(args.receipts, args.contrasts, args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["PhaseSpaceAggregateError", "aggregate_phase_space"]
