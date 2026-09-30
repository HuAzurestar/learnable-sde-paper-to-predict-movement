"""Frozen all-attempt cost validation, including unsuccessful resource use."""

import csv
import io

import pytest

from scripts.pirc25.aggregate import aggregate, csv_bytes, fingerprint
from test_shared_evidence import bundle, seal


def cost_bundle():
    value = bundle()
    for row in value["cells"]:
        row["history"] = [{"attempt_id": row["attempt_id"], "state": "SUCCEEDED", "error_code": None}]
        payload = {"reservation_id": fingerprint(row["attempt_id"]), "attempt_id": row["attempt_id"],
                   "run_id": row["run_id"], "arm_id": row["arm_id"], "study_id": value["study_id"],
                   "reserved_ms": 1000, "charged_ms": 100, "monotonic_elapsed_ms": 100, "settled": True}
        event = {"event_kind": "SETTLE", "sequence": 1, "payload": payload}
        event["hash"] = fingerprint(event)
        row["cost"] = {"unit": "slot-ms", "scope": "all-cell-attempts-including-failures", "charged_ms": 100,
                       "reserved_ms": 0, "measured_ms": 100, "missing_attempt_ids": [], "unknown_attempt_ids": [],
                       "pending_attempt_ids": [], "sources": [event]}
    return seal(value)


def test_frozen_costs_match_csv_and_include_failed_cells():
    value = cost_bundle()
    value["cells"][0].update(status="FAILED", metrics=None)
    result = aggregate(seal(value))
    assert result["arms"][0]["independent_n"] == 1
    assert result["arms"][0]["cost"]["charged_ms"] == 400
    assert len(result["arms"][0]["cost"]["source_event_hashes"]) == 4
    table = list(csv.DictReader(io.StringIO(csv_bytes(result).decode())))
    assert all(row["charged_ms"] == "400" and row["cost_unit"] == "slot-ms" for row in table)


@pytest.mark.parametrize("mutation", ["summary", "event", "identity", "duplicate", "negative", "missing-history"])
def test_resealed_cost_tampering_is_rejected(mutation):
    value = cost_bundle()
    row = value["cells"][0]
    event = row["cost"]["sources"][0]
    if mutation == "summary":
        row["cost"]["charged_ms"] = 0
    elif mutation == "event":
        event["payload"]["charged_ms"] = 0
    elif mutation == "identity":
        event["payload"]["study_id"] = "another"
        event["hash"] = fingerprint({k: v for k, v in event.items() if k != "hash"})
    elif mutation == "duplicate":
        row["cost"]["sources"].append(event)
    elif mutation == "negative":
        event["payload"]["charged_ms"] = event["payload"]["monotonic_elapsed_ms"] = -1
        event["hash"] = fingerprint({k: v for k, v in event.items() if k != "hash"})
    else:
        row["history"] = []
    with pytest.raises(ValueError, match="cost"):
        aggregate(seal(value))


def test_legacy_cost_is_unavailable_not_free():
    result = aggregate(bundle())
    assert all(arm["cost"]["charged_ms"] is None for arm in result["arms"])
    assert all(arm["cost"]["unavailable_cells"] == 4 for arm in result["arms"])
