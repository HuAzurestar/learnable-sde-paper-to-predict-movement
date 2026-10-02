"""The same frozen decision is serialized, never recomputed by consumers."""

import csv
import io
import json

from scripts.pirc25.aggregate import fingerprint
from scripts.pirc25.comparison import compare_package
from test_shared_adjudication import evidence


def test_managed_outputs_share_full_policy_decision_and_reference():
    reference = {"manifest_id": "synthetic-worker-receipt", "attempt_id": "synthetic"}
    package = compare_package(evidence(), reference)
    value = package["aggregate"]
    assert value["aggregate_hash"] == fingerprint({k: v for k, v in value.items() if k != "aggregate_hash"})
    assert value["adjudication"]["records"][0]["effect"] == 1
    assert value["adjudication"]["records"][0]["verdict"] == "GAIN"
    assert all(c["bootstrap_replicates"] == 0 for c in value["comparisons"])
    assert all(m["interval95"] is None for c in value["comparisons"] for m in c["metrics"].values())
    rows = list(csv.DictReader(io.StringIO(package["metrics_csv"])))
    assert all(json.loads(row["adjudication"]) == value["adjudication"] for row in rows)
    assert all(json.loads(row["computation_ref"]) == reference for row in rows)
    assert package["paper_index"]["adjudication"] == value["adjudication"]
    assert package["paper_index"]["computation_ref"] == reference


def test_missing_preregistration_stays_visible_in_all_outputs():
    value = evidence()
    value["comparison_plan"].pop("adjudication_spec")
    value["comparison_plan"].pop("adjudication_hash")
    value["bundle_hash"] = fingerprint({k: v for k, v in value.items() if k != "bundle_hash"})
    package = compare_package(value, {"manifest_id": "synthetic-receipt"})
    assert package["aggregate"]["adjudication"]["status"] == "NEEDS_PREREGISTRATION"
    assert package["paper_index"]["adjudication"]["records"] == []
    assert "NEEDS_PREREGISTRATION" in package["metrics_csv"]
