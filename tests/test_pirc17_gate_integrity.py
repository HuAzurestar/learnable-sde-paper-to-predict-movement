"""Aggregation must not trust a producer's mechanism passed flag."""
from pathlib import Path
import hashlib
import json

import pytest

from scripts.aggregate_nex326 import AggregateError, load_records, validate_records


@pytest.mark.parametrize("mutation", [
    {"value": float("nan")}, {"threshold": float("inf")},
    {"operator": "typo"}, {"value": 0.0, "threshold": 1.0, "operator": "ge", "passed": True},
    {"value": 2.0, "threshold": 1.0, "operator": "le", "passed": True},
])
def test_aggregate_rejects_forged_gate(mutation):
    records = load_records(Path(__file__).parent / "fixtures/nex326_run_records.json")
    records[0]["mechanism_gates"][0].update(mutation)
    with pytest.raises(AggregateError, match="mechanism gate"):
        validate_records(records)


def test_formal_aggregation_rejects_legacy_identity_free_records():
    records = load_records(Path(__file__).parent / "fixtures/nex326_run_records.json")
    with pytest.raises(AggregateError, match="implementation identity"):
        validate_records(records, require_implementation=True)
    records[0]["verdict"] = "retain"
    with pytest.raises(AggregateError, match="implementation identity"):
        validate_records(records)


def test_formal_identity_is_recomputed():
    records = load_records(Path(__file__).parent / "fixtures/nex326_run_records.json")
    files = [{"path": "environment.lock.json", "sha256": "a" * 64}]
    runtime = {"python": "test-fixture"}
    bundle = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    identity = hashlib.sha256(json.dumps({"source_bundle_sha256": bundle, "runtime": runtime}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    for record in records:
        record["implementation"] = {"files": files, "runtime": runtime,
            "source_bundle_sha256": bundle, "execution_identity_sha256": identity,
            "environment_lock": {"path": "environment.lock.json", "sha256": "a" * 64, "conformant": True}}
    validate_records(records, require_implementation=True)
    records[0]["implementation"]["execution_identity_sha256"] = "b" * 64
    with pytest.raises(AggregateError, match="identity hash mismatch"):
        validate_records(records, require_implementation=True)
