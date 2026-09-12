from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.aggregate_nex326 import aggregate, load_records
from scripts.aggregate_nex326_replicates import ReplicateAggregateError, aggregate_replicates


FIXTURE = Path(__file__).parent / "fixtures" / "nex326_run_records.json"


def _reference(path: Path, root: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "size_bytes": path.stat().st_size,
    }


def _replicate_inputs(tmp_path: Path):
    seeds = (101, 202, 303)
    entries = []
    summaries = []
    fingerprint = "f" * 64
    for replicate_index, seed in enumerate(seeds):
        records = load_records(FIXTURE)
        for record in records:
            record["replicate_seed"] = seed
            record["dataset"]["fingerprint"] = fingerprint
            record["metrics"]["energy_score_d2"] += replicate_index * 0.1
        records_root = tmp_path / f"seed-{seed}"
        records_root.mkdir()
        manifest_path = records_root / "manifest.json"
        manifest_path.write_text(json.dumps({"replicate_seed": seed}), encoding="utf-8")
        entries.append(
            {
                "replicate_seed": seed,
                "record_count": 36,
                "manifest": _reference(manifest_path, tmp_path),
            }
        )
        aggregate_root = tmp_path / f"aggregate-seed-{seed}"
        aggregate(records, aggregate_root)
        summaries.append(aggregate_root / "nex326_summary.json")
    batch = {
        "schema_version": "nex326-multi-seed-manifest-v1",
        "spec_version": "nex326-process-v2",
        "protocol_seed": 20260814,
        "replicate_seeds": list(seeds),
        "cohort": {"fingerprint": fingerprint},
        "replicates": entries,
    }
    batch_path = tmp_path / "multi_seed_manifest.json"
    batch_path.write_text(json.dumps(batch), encoding="utf-8")
    return batch_path, summaries


def test_cross_replicate_aggregate_is_descriptive_and_hash_bound(tmp_path):
    batch_path, summaries = _replicate_inputs(tmp_path)
    output = tmp_path / "combined"
    summary = aggregate_replicates(batch_path, summaries, output)

    assert summary["replicate_seeds"] == [101, 202, 303]
    assert summary["replicate_count"] == 3
    assert summary["assessment"] == "not_assessed"
    assert summary["method"] == "descriptive_across_replicate_seeds_no_inferential_ci"
    assert summary["comparison_status"] == {
        "reference": 8,
        "exploratory_point_estimate": 24,
        "requires_coverage_matched_reference": 1,
        "no_registered_reference": 3,
    }
    reference = summary["artifacts"]["nex326_cross_replicate_comparisons.csv"]
    table = output / reference["path"]
    assert hashlib.sha256(table.read_bytes()).hexdigest() == reference["sha256"]


def test_cross_replicate_aggregate_rejects_tampered_input(tmp_path):
    batch_path, summaries = _replicate_inputs(tmp_path)
    comparison = summaries[0].parent / "nex326_pilot_comparisons.csv"
    comparison.write_text("tampered", encoding="utf-8")
    with pytest.raises(ReplicateAggregateError, match="size mismatch|SHA-256 mismatch"):
        aggregate_replicates(batch_path, summaries, tmp_path / "combined")
