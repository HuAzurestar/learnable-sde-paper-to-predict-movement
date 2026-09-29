"""Synthetic evidence: seed repeats, missing outcomes, units and atomic exports."""

import csv
import io
import json

import pytest

from scripts.pirc25.aggregate import aggregate, csv_bytes, fingerprint, write_package


def bundle():
    cells = []
    for arm, offset in (("baseline", 0), ("candidate", -1)):
        for block, base in (("block1", 10), ("block2", 20)):
            for seed in (1, 2):
                cells.append({"cell_hash": fingerprint([arm, block, seed]), "arm_id": arm, "block_id": block,
                    "seed": seed, "status": "SUCCEEDED", "attempt_id": f"{arm}-{block}-{seed}",
                    "run_id": fingerprint([arm, block, seed]), "artifact_id": fingerprint([base, offset, seed]),
                    "metrics": {"error": base + offset + seed}, "metric_units": {"error": "m"},
                    "qualification": "fixture", "state_order": ["x", "y", "vx", "vy"],
                    "units": ["m", "m", "m/s", "m/s"], "protocol_hash": fingerprint("protocol"), "history": []})
    value = {"schema_version": "pirc25-evidence-bundle-v1", "study_id": "synthetic", "independent_unit": "block_id",
        "expected_cells": [{k: cell[k] for k in ("cell_hash", "arm_id", "block_id", "seed")} for cell in cells], "cells": cells,
        "protocol_hash": fingerprint("protocol"), "spec_hash": fingerprint("spec"), "data_hash": fingerprint("data"),
        "code_hash": fingerprint("code"), "disclosure_scope": "synthetic"}
    return seal(value)


def seal(value):
    return {**value, "bundle_hash": fingerprint({k: v for k, v in value.items() if k != "bundle_hash"})}


def test_seed_replicates_are_not_independent_blocks():
    value = aggregate(bundle())
    assert value["expected_cell_count"] == 8
    assert [a["independent_n"] for a in value["arms"]] == [2, 2]
    assert value["arms"][0]["metrics"]["error"] == 16.5
    comparison = value["comparisons"][0]
    assert comparison["metrics"]["error"]["candidate_minus_reference"] == -1
    assert comparison["metrics"]["error"]["interval95"] == [-1, -1]


def test_failed_and_missing_cells_stay_in_denominator():
    value = bundle()
    value["cells"][0].update(status="TIMEOUT", metrics=None)
    value["cells"][1].update(status="MISSING", metrics=None, attempt_id=None, artifact_id=None)
    result = aggregate(seal(value))
    assert result["expected_cell_count"] == 8 and result["successful_cell_count"] == 6
    arm = result["arms"][0]
    assert arm["expected_cells"] == 4 and arm["independent_n"] == 1
    assert arm["dispositions"] == {"MISSING": 1, "SUCCEEDED": 2, "TIMEOUT": 1}
    assert result["comparisons"][0]["metrics"]["error"]["interval95"] is None


@pytest.mark.parametrize("mutation", ["unit", "protocol", "drop", "duplicate", "seed-unit", "failed-value"])
def test_incompatible_evidence_is_rejected(mutation):
    value = bundle()
    if mutation == "unit":
        value["cells"][0]["metric_units"] = {"error": "km"}
    elif mutation == "protocol":
        value["cells"][0]["protocol_hash"] = "0" * 64
    elif mutation == "drop":
        value["cells"].pop()
    elif mutation == "duplicate":
        value["cells"].append(value["cells"][0])
    elif mutation == "seed-unit":
        value["independent_unit"] = "seed"
    else:
        value["cells"][0]["status"] = "FAILED"
    with pytest.raises(ValueError):
        aggregate(seal(value))


def test_formal_comparison_requires_plan_and_qualification():
    value = bundle()
    with pytest.raises(ValueError, match="preregistered"):
        aggregate(value, formal=True)
    value["comparison_plan"] = {"reference_arm_id": "baseline", "candidate_arm_ids": ["candidate"],
        "preregistration_hash": "a" * 64, "failure_policy": "retain-and-exclude-incomplete-blocks"}
    with pytest.raises(ValueError, match="unqualified"):
        aggregate(seal(value), formal=True)


def test_csv_index_and_aggregate_share_values_hashes_and_immutable_publication(tmp_path):
    value = write_package(bundle(), tmp_path / "evidence")
    table = list(csv.DictReader(io.StringIO((tmp_path / "evidence/metrics.csv").read_text())))
    assert all(row["aggregate_hash"] == value["aggregate_hash"] for row in table)
    assert float(table[0]["value"]) == value["arms"][0]["metrics"]["error"]
    index = json.loads((tmp_path / "evidence/PaperEvidenceIndex.json").read_bytes())
    assert index["claims"][0]["value"] == float(table[0]["value"])
    assert write_package(bundle(), tmp_path / "evidence") == value
    (tmp_path / "evidence/metrics.csv").write_text("tampered")
    with pytest.raises(ValueError, match="immutable"):
        write_package(bundle(), tmp_path / "evidence")


def test_all_failed_arm_has_null_metrics_and_visible_csv_denominator():
    value = bundle()
    for cell in value["cells"]:
        cell.update(status="FAILED", metrics=None)
    result = aggregate(seal(value))
    assert all(not arm["metrics"] and arm["independent_n"] == 0 for arm in result["arms"])
    rows = list(csv.DictReader(io.StringIO(csv_bytes(result).decode())))
    assert len(rows) == 2 and rows[0]["value"] == "" and rows[0]["expected_cells"] == "4"
