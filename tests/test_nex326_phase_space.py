from __future__ import annotations

import csv
import hashlib
import json

import pytest

from scripts.aggregate_nex326_phase_space import (
    PhaseSpaceAggregateError,
    aggregate_phase_space,
)


METRICS = (
    "position_energy_score_d2",
    "position_hdr90_coverage",
    "position_cep50_error",
    "velocity_endpoint_rmse",
)


def _receipt(benchmark_id: str, manifest: str, energy: float, comparator: str = ""):
    metric_summary = {
        metric: {
            "mean": energy if metric == "position_energy_score_d2" else 1.0,
            "sample_std": 0.1,
        }
        for metric in METRICS
    }
    return {
        "schema_version": "nex326-phase-space-dsde-receipt-v1",
        "benchmark_id": benchmark_id,
        "scientific_role": "supplemental_exploratory_benchmark",
        "assessment": "not_assessed",
        "replicate_seeds": [11, 22, 33],
        "replicate_count": 3,
        "prediction_samples_per_segment": 64,
        "cohort": {"fingerprint": "f" * 64},
        "implementation": {"source_bundle_sha256": "a" * 64},
        "registered_protocol": {"primary_comparator": comparator},
        "metric_summary": metric_summary,
        "integrity": {"manifest_sha256": manifest},
    }


def _contrast(baseline_manifest: str, candidate_manifest: str):
    paired = []
    values = (-0.3, -0.2, 0.1)
    for seed, value in zip((11, 22, 33), values):
        paired.append(
            {
                "seed": seed,
                "candidate_minus_baseline": {
                    metric: value for metric in METRICS
                },
            }
        )
    return {
        "schema_version": "nex326-phase-space-paired-contrast-v1",
        "baseline_benchmark_id": "baseline",
        "candidate_benchmark_id": "candidate",
        "cohort_fingerprint": "f" * 64,
        "replicate_seeds": [11, 22, 33],
        "prediction_samples_per_segment": 64,
        "comparator_role": "registered_primary",
        "conclusion": "observed_primary_metric_gain",
        "paired_deltas": paired,
        "delta_summary": {
            metric: {
                "mean": sum(values) / 3,
                "candidate_better_seed_count": 2,
                "seed_count": 3,
            }
            for metric in METRICS
        },
        "integrity": {
            "baseline_manifest_sha256": baseline_manifest,
            "candidate_manifest_sha256": candidate_manifest,
        },
    }


def _uncertainty(contrast_path):
    values = {
        metric: {
            "candidate_minus_baseline": (-0.3 - 0.2 + 0.1) / 3,
            "ci_low": -0.4,
            "ci_high": 0.1,
            "interval_excludes_zero": False,
            "bootstrap_fraction_below_zero": 0.9,
        }
        for metric in (
            "position_energy_score_d2",
            "position_cep50_error",
            "velocity_endpoint_rmse",
        )
    }
    return {
        "schema_version": "nex326-phase-space-segment-bootstrap-v1",
        "analysis_id": "fixture-segment-bootstrap",
        "baseline_benchmark_id": "baseline",
        "candidate_benchmark_id": "candidate",
        "cohort_fingerprint": "f" * 64,
        "replicate_seeds": [11, 22, 33],
        "prediction_samples_per_segment": 64,
        "bootstrap_unit": "paired_evaluation_segment",
        "evaluation_segment_count": 28,
        "bootstrap_iterations": 1000,
        "bootstrap_seed": 17,
        "confidence_level": 0.95,
        "uncertainty_scope": "heldout_segment_sampling_only",
        "uncertainty": values,
        "integrity": {
            "protocol_sha256": "e" * 64,
            "baseline_manifest_sha256": "b" * 64,
            "candidate_manifest_sha256": "c" * 64,
            "contrast_sha256": hashlib.sha256(contrast_path.read_bytes()).hexdigest(),
        },
    }


def test_phase_space_aggregate_is_hash_bound_and_exploratory(tmp_path):
    baseline_manifest = "b" * 64
    candidate_manifest = "c" * 64
    baseline_path = tmp_path / "baseline-receipt.json"
    candidate_path = tmp_path / "candidate-receipt.json"
    contrast_path = tmp_path / "contrast.json"
    baseline_path.write_text(
        json.dumps(_receipt("baseline", baseline_manifest, 10.0)), encoding="utf-8"
    )
    candidate_path.write_text(
        json.dumps(
            _receipt("candidate", candidate_manifest, 9.9, comparator="baseline")
        ),
        encoding="utf-8",
    )
    contrast_path.write_text(
        json.dumps(_contrast(baseline_manifest, candidate_manifest)),
        encoding="utf-8",
    )
    uncertainty_path = tmp_path / "uncertainty.json"
    uncertainty_path.write_text(
        json.dumps(_uncertainty(contrast_path)), encoding="utf-8"
    )

    output = tmp_path / "aggregate"
    summary = aggregate_phase_space(
        [baseline_path, candidate_path],
        [contrast_path],
        output,
        uncertainty_paths=[uncertainty_path],
    )
    assert summary["scientific_status"] == "exploratory_only"
    assert summary["assessment"] == "not_assessed"
    assert summary["model_count"] == 2
    assert summary["contrast_count"] == 1
    assert summary["uncertainty_analysis_count"] == 1
    assert summary["descriptive_lowest_energy_score_benchmark"] == "candidate"
    with (output / "nex326_phase_space_models.csv").open(
        encoding="utf-8", newline=""
    ) as source:
        models = list(csv.DictReader(source))
    assert [row["benchmark_id"] for row in models] == ["baseline", "candidate"]
    with (output / "nex326_phase_space_uncertainty.csv").open(
        encoding="utf-8", newline=""
    ) as source:
        uncertainty_rows = list(csv.DictReader(source))
    assert len(uncertainty_rows) == 3
    assert {row["analysis_id"] for row in uncertainty_rows} == {
        "fixture-segment-bootstrap"
    }
    for reference in summary["artifacts"].values():
        artifact = output / reference["path"]
        assert artifact.stat().st_size == reference["size_bytes"]
        assert hashlib.sha256(artifact.read_bytes()).hexdigest() == reference["sha256"]


def test_phase_space_aggregate_rejects_contrast_hash_mismatch(tmp_path):
    baseline_manifest = "b" * 64
    candidate_manifest = "c" * 64
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    contrast_path = tmp_path / "contrast.json"
    baseline_path.write_text(
        json.dumps(_receipt("baseline", baseline_manifest, 10.0)), encoding="utf-8"
    )
    candidate_path.write_text(
        json.dumps(
            _receipt("candidate", candidate_manifest, 9.9, comparator="baseline")
        ),
        encoding="utf-8",
    )
    contrast = _contrast(baseline_manifest, candidate_manifest)
    contrast["integrity"]["candidate_manifest_sha256"] = "d" * 64
    contrast_path.write_text(json.dumps(contrast), encoding="utf-8")

    with pytest.raises(PhaseSpaceAggregateError, match="manifest hashes"):
        aggregate_phase_space(
            [baseline_path, candidate_path], [contrast_path], tmp_path / "aggregate"
        )


def test_phase_space_aggregate_recomputes_contrast_summary(tmp_path):
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    contrast_path = tmp_path / "contrast.json"
    baseline_path.write_text(
        json.dumps(_receipt("baseline", "b" * 64, 10.0)), encoding="utf-8"
    )
    candidate_path.write_text(
        json.dumps(_receipt("candidate", "c" * 64, 9.9, comparator="baseline")),
        encoding="utf-8",
    )
    contrast = _contrast("b" * 64, "c" * 64)
    contrast["delta_summary"]["position_energy_score_d2"]["mean"] = -99.0
    contrast_path.write_text(json.dumps(contrast), encoding="utf-8")

    with pytest.raises(PhaseSpaceAggregateError, match="summary is inconsistent"):
        aggregate_phase_space(
            [baseline_path, candidate_path], [contrast_path], tmp_path / "aggregate"
        )
