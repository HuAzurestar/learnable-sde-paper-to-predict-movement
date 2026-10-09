"""Pure frozen preparation serialization, not a source-qualification fixture."""

import csv
import io
import json

import pytest

from scripts.pirc25.aggregate import aggregate, csv_bytes, evidence_index, fingerprint
from tests.test_shared_evidence import bundle


FIELDS = ("calibration_cost", "calibration_evidence_hash", "calibration_status_counts")


def display_value(*, known, metrics):
    value = aggregate(bundle())
    if not metrics:
        for arm in value["arms"]:
            arm.update(metrics={}, independent_n=0)
    value.update(calibration_cost={"unit": "slot-ms", "scope": "unique-original-attempts-not-per-target",
        "unique_attempts": 2, "charged_ms": 23 if known else None, "reserved_ms": 0 if known else None,
        "measured_ms": 23 if known else None, "sources": [{"attempt_id": "failed", "charged_ms": 23},
            {"attempt_id": "unreserved", "charged_ms": 0 if known else None}]},
        calibration_evidence_hash=fingerprint("recorded-preparation"),
        calibration_status_counts={"CALIBRATED": 1, "FAILED": 2, "UNAVAILABLE": 1})
    return value


@pytest.mark.parametrize("known", [False, True])
@pytest.mark.parametrize("metrics", [False, True])
@pytest.mark.parametrize("managed", [False, True])
def test_shared_cost_has_one_global_row_and_no_claim_replication(known, metrics, managed):
    value = display_value(known=known, metrics=metrics)
    if managed:
        value.update(adjudication={"records": []}, computation_ref={"manifest_id": "recorded-receipt"})
    table = csv_bytes(value)
    rows = list(csv.DictReader(io.StringIO(table.decode())))
    shared = [row for row in rows if row["row_kind"] == "shared-calibration-preparation"]
    assert len(shared) == 1
    row = shared[0]
    assert row["arm_id"] == row["metric"] == row["independent_n"] == ""
    assert row["charged_ms"] == ("23" if known else "")
    assert json.loads(row["calibration_cost"]) == value["calibration_cost"]
    assert json.loads(row["calibration_status_counts"]) == value["calibration_status_counts"]
    assert row["calibration_evidence_hash"] == value["calibration_evidence_hash"]
    assert all(all(row[name] == "" for name in FIELDS) for row in rows if row["row_kind"] == "method-metric")
    index = evidence_index(value, table)
    assert all(index[name] == value[name] for name in FIELDS)
    assert all(not any(name in claim for name in FIELDS) for claim in index["claims"])
    assert len(index["claims"]) == (2 if metrics else 0)


@pytest.mark.parametrize("missing", FIELDS)
def test_partial_preparation_cannot_silently_disappear(missing):
    value = display_value(known=False, metrics=False)
    del value[missing]
    with pytest.raises(ValueError, match="calibration"):
        csv_bytes(value)
    with pytest.raises(ValueError, match="calibration"):
        evidence_index(value, b"not-published")


@pytest.mark.parametrize("fault", ["cost", "hash", "bool-count", "unknown-status", "empty-counts"])
def test_malformed_preparation_summary_is_rejected(fault):
    value = display_value(known=False, metrics=False)
    if fault == "cost":
        value["calibration_cost"] = None
    elif fault == "hash":
        value["calibration_evidence_hash"] = "z" * 64
    elif fault == "bool-count":
        value["calibration_status_counts"]["CALIBRATED"] = True
    elif fault == "unknown-status":
        value["calibration_status_counts"]["SUCCESS"] = 1
    else:
        value["calibration_status_counts"] = {}
    with pytest.raises(ValueError, match="calibration"):
        csv_bytes(value)
    with pytest.raises(ValueError, match="calibration"):
        evidence_index(value, b"not-published")


def test_legacy_version_has_no_invented_cost_row_or_index_fields():
    value = aggregate(bundle())
    table = csv_bytes(value)
    rows = list(csv.DictReader(io.StringIO(table.decode())))
    assert len(rows) == 2 and all("row_kind" not in row for row in rows)
    assert not any(name in evidence_index(value, table) for name in FIELDS)
