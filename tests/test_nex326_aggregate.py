from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import pytest

from scripts.aggregate_nex326 import AggregateError, aggregate, load_records


FIXTURE = Path(__file__).parent / "fixtures" / "nex326_run_records.json"


def test_tsde_regenerates_process_status_and_plot_from_run_records_only(tmp_path):
    records = load_records(FIXTURE)
    summary = aggregate(records, tmp_path)
    assert summary["arm_count"] == 22
    assert summary["execution_count"] == 36
    assert summary["protocol_seed"] == 20260814
    assert summary["replicate_seed"] == 20260814
    assert summary["mechanism_status"] == {"passed": 36}
    assert summary["requested_prediction_samples"] == [64]
    assert summary["effective_prediction_samples"] == {"64": 36}
    assert summary["implementation_source_bundle_sha256"] is None
    assert summary["implementation_execution_identity_sha256"] is None
    assert summary["comparison"] == {
        "scientific_status": "exploratory_only",
        "assessment": "not_assessed",
        "method": "registered_reference_point_estimates",
        "uncertainty_method": "paired_evaluation_segment_bootstrap_only",
        "bootstrap_iterations": 1000,
        "bootstrap_seed": 20260814,
        "status": {
            "reference": 8,
            "exploratory_point_estimate": 24,
            "requires_coverage_matched_reference": 1,
            "no_registered_reference": 3,
        },
        "uncertainty_status": {
            "reference": 8,
            "predictions_not_loaded": 24,
            "not_applicable": 4,
        },
    }
    with (tmp_path / "nex326_process.csv").open(encoding="utf-8", newline="") as source:
        process = list(csv.DictReader(source))
    with (tmp_path / "nex326_status.csv").open(encoding="utf-8", newline="") as source:
        status = list(csv.DictReader(source))
    assert len(process) == 36
    assert [int(row["arm_id"]) for row in status] == list(range(1, 23))
    assert next(row for row in status if row["arm_id"] == "6")["execution_count"] == "5"
    assert next(row for row in status if row["arm_id"] == "17")["execution_count"] == "4"
    assert next(row for row in status if row["arm_id"] == "22")["execution_count"] == "3"
    assert next(row for row in process if row["arm_id"] == "13")["idea_ids"] == "C-3"
    assert {row["requested_prediction_samples"] for row in process} == {"64"}
    assert {row["effective_prediction_samples"] for row in process} == {"64"}
    assert {row["replicate_seed"] for row in process} == {"20260814"}
    with (tmp_path / "nex326_pilot_comparisons.csv").open(
        encoding="utf-8", newline=""
    ) as source:
        comparisons = list(csv.DictReader(source))
    arm2 = next(row for row in comparisons if row["arm_id"] == "2")
    assert arm2["comparison_status"] == "exploratory_point_estimate"
    assert (arm2["reference_arm_id"], arm2["reference_subconfig_id"]) == ("1", "full")
    assert float(arm2["delta_energy_score_d2"]) == pytest.approx(0.01)
    dt30 = next(
        row
        for row in comparisons
        if row["arm_id"] == "6" and row["subconfig_id"] == "dt30"
    )
    assert (dt30["reference_arm_id"], dt30["reference_subconfig_id"]) == ("6", "dt60")
    terrain = next(
        row
        for row in comparisons
        if row["arm_id"] == "17" and row["subconfig_id"] == "terrain"
    )
    assert terrain["comparison_status"] == "requires_coverage_matched_reference"
    arm22 = [row for row in comparisons if row["arm_id"] == "22"]
    assert {row["comparison_status"] for row in arm22} == {"no_registered_reference"}
    assert {row["assessment"] for row in comparisons} == {"not_assessed"}
    for reference in summary["artifacts"].values():
        artifact = tmp_path / reference["path"]
        assert artifact.stat().st_size == reference["size_bytes"]
        assert hashlib.sha256(artifact.read_bytes()).hexdigest() == reference["sha256"]
    svg = (tmp_path / "nex326_test_plot.svg").read_text(encoding="utf-8")
    assert svg.startswith("<svg") and svg.count("<circle") == 36


def test_historical_eight_arm_artifact_cannot_pass_completeness(tmp_path):
    fixture_records = load_records(FIXTURE)
    records = [
        next(record for record in fixture_records if record["arm_id"] == arm_id)
        for arm_id in range(1, 9)
    ]
    with pytest.raises(AggregateError, match="requires arms 1..22; observed 8"):
        aggregate(records, tmp_path)


def test_boolean_only_mechanism_claim_is_rejected(tmp_path):
    records = json.loads(FIXTURE.read_text(encoding="utf-8"))["records"]
    records[0]["mechanism_gates"] = [{"passed": True}]
    with pytest.raises(AggregateError, match="only a label/boolean"):
        aggregate(records, tmp_path)


def test_missing_registered_subconfig_cannot_pass_completeness(tmp_path):
    records = load_records(FIXTURE)
    records = [
        record
        for record in records
        if (record["arm_id"], record["subconfig_id"]) != (6, "dt600")
    ]
    with pytest.raises(AggregateError, match="exact 36-execution matrix"):
        aggregate(records, tmp_path)


def test_one_aggregate_cannot_mix_replicate_seeds(tmp_path):
    records = load_records(FIXTURE)
    records[0]["replicate_seed"] += 1
    with pytest.raises(AggregateError, match="exactly one replicate seed"):
        aggregate(records, tmp_path)


def test_one_aggregate_cannot_mix_implementation_source_bundles(tmp_path):
    records = load_records(FIXTURE)
    for record in records:
        record["implementation"] = {
            "source_bundle_sha256": "a" * 64,
            "execution_identity_sha256": "c" * 64,
        }
    records[0]["implementation"]["source_bundle_sha256"] = "b" * 64
    with pytest.raises(AggregateError, match="multiple implementation source bundles"):
        aggregate(records, tmp_path)


def test_one_aggregate_cannot_mix_execution_identities(tmp_path):
    records = load_records(FIXTURE)
    for record in records:
        record["implementation"] = {
            "source_bundle_sha256": "a" * 64,
            "execution_identity_sha256": "c" * 64,
        }
    records[0]["implementation"]["execution_identity_sha256"] = "d" * 64
    with pytest.raises(AggregateError, match="multiple execution identities"):
        aggregate(records, tmp_path)


def test_data_unavailable_execution_remains_visible_in_outputs(tmp_path):
    records = load_records(FIXTURE)
    unavailable = next(record for record in records if record["arm_id"] == 13)
    unavailable["run_status"] = "data_unavailable"
    unavailable["verdict"] = "unavailable"
    unavailable["metrics"] = {}
    unavailable["runtime"]["effective_prediction_samples"] = None
    unavailable["artifacts"] = {
        "availability": {
            "path": "fixture-arm-13-animal_pretrain/availability.json",
            "sha256": "0" * 64,
            "size_bytes": 1,
        }
    }
    unavailable["failure"] = {
        "stage": "load_versioned_data",
        "reason": "licensed animal data are unavailable",
        "category": "external_data_unavailable",
    }
    unavailable["stages"] = [
        {
            "name": stage["name"],
            "status": "data_unavailable" if index == 0 else "not_run",
        }
        for index, stage in enumerate(unavailable["stages"])
    ]
    unavailable["mechanism_gates"] = [
        {
            "statistic": "data_availability",
            "value": 0.0,
            "threshold": 1.0,
            "operator": "ge",
            "passed": False,
            "sample_size": 0,
        }
    ]

    summary = aggregate(records, tmp_path)
    assert summary["run_status"] == {"succeeded": 35, "data_unavailable": 1}
    assert summary["mechanism_status"] == {"passed": 35, "not_run": 1}
    assert summary["comparison"]["status"]["data_unavailable"] == 1
    with (tmp_path / "nex326_status.csv").open(encoding="utf-8", newline="") as source:
        status = list(csv.DictReader(source))
    arm13 = next(row for row in status if row["arm_id"] == "13")
    assert arm13["run_status"] == "data_unavailable"
    assert arm13["verdict"] == "unavailable"
    assert arm13["mechanism_status"] == "not_run"


def test_directory_aggregation_adds_paired_segment_bootstrap_intervals(tmp_path):
    records = load_records(FIXTURE)
    records_root = tmp_path / "records"
    for record in records:
        run_dir = records_root / record["run_id"]
        run_dir.mkdir(parents=True)
        offset = float(record["arm_id"]) / 10.0
        predictions = {
            "predictions": [
                {
                    "segment_id": f"segment-{index}",
                    "target": [float(index), 0.0],
                    "samples": [
                        [float(index) + offset + jitter, jitter]
                        for jitter in (-0.2, -0.1, 0.1, 0.2)
                    ],
                }
                for index in range(4)
            ]
        }
        prediction_path = run_dir / "predictions.json"
        prediction_path.write_text(json.dumps(predictions), encoding="utf-8")
        record["artifacts"]["predictions"]["path"] = (
            f"{record['run_id']}/predictions.json"
        )
        jitters = (-0.2, -0.1, 0.1, 0.2)
        samples = [(offset + jitter, jitter) for jitter in jitters]
        first = sum(math.dist(sample, (0.0, 0.0)) for sample in samples) / len(samples)
        second = sum(
            math.dist(sample, samples[index - 1])
            for index, sample in enumerate(samples)
        ) / len(samples)
        radii = sorted(math.dist(sample, (offset, 0.0)) for sample in samples)
        q90 = radii[2] * 0.3 + radii[3] * 0.7
        record["metrics"].update(
            {
                "energy_score_d2": first - 0.5 * second,
                "hdr90_coverage": float(abs(offset) <= q90),
                "cep50_error": abs(offset),
            }
        )
    closed = next(
        record
        for record in records
        if record["arm_id"] == 10 and record["subconfig_id"] == "d2_closed"
    )
    closed["config"]["score"] = "d2_closed"

    output = tmp_path / "aggregate"
    summary = aggregate(records, output, records_root=records_root)
    assert summary["comparison"]["uncertainty_status"] == {
        "reference": 8,
        "complete": 23,
        "partial_closed_energy_not_resampled": 1,
        "not_applicable": 4,
    }
    with (output / "nex326_pilot_comparisons.csv").open(
        encoding="utf-8", newline=""
    ) as source:
        comparisons = list(csv.DictReader(source))
    arm2 = next(row for row in comparisons if row["arm_id"] == "2")
    assert arm2["bootstrap_status"] == "complete"
    assert arm2["bootstrap_unit"] == "paired_evaluation_segment"
    assert arm2["paired_segment_count"] == "4"
    assert arm2["delta_energy_score_d2_ci95_low"] != ""
    closed_row = next(
        row
        for row in comparisons
        if row["arm_id"] == "10" and row["subconfig_id"] == "d2_closed"
    )
    assert closed_row["bootstrap_status"] == "partial_closed_energy_not_resampled"
    assert closed_row["delta_energy_score_d2_ci95_low"] == ""
    assert closed_row["delta_cep50_error_ci95_low"] != ""


def test_directory_loading_verifies_artifact_size_and_sha256(tmp_path):
    record = load_records(FIXTURE)[0]
    records_root = tmp_path / "records"
    run_dir = records_root / record["run_id"]
    run_dir.mkdir(parents=True)
    for name, reference in record["artifacts"].items():
        artifact = run_dir / f"{name}.json"
        artifact.write_text(json.dumps({"artifact": name}), encoding="utf-8")
        reference.update(
            {
                "path": f"{record['run_id']}/{artifact.name}",
                "size_bytes": artifact.stat().st_size,
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            }
        )
    (run_dir / "run_record.json").write_text(json.dumps(record), encoding="utf-8")

    assert len(load_records(records_root)) == 1
    (run_dir / "checkpoint.json").write_text("tampered", encoding="utf-8")
    with pytest.raises(AggregateError, match="size mismatch|SHA-256 mismatch"):
        load_records(records_root)


def test_directory_loading_rejects_artifact_path_escape(tmp_path):
    record = load_records(FIXTURE)[0]
    records_root = tmp_path / "records"
    run_dir = records_root / record["run_id"]
    run_dir.mkdir(parents=True)
    record["artifacts"] = {
        "checkpoint": {
            "path": "../outside.json",
            "size_bytes": 1,
            "sha256": "0" * 64,
        }
    }
    (run_dir / "run_record.json").write_text(json.dumps(record), encoding="utf-8")

    with pytest.raises(AggregateError, match="escapes the records root"):
        load_records(records_root)
