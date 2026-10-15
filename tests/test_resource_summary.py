"""Saved-resource bookkeeping only; no native observer or shared study reads."""
from copy import deepcopy
import csv
import hashlib
import io
import json
import importlib
import pytest

from scripts.pirc25.resource_usage import summarize_resources, fingerprint
from scripts.pirc25.aggregate import aggregate, aggregate_stratum, csv_bytes, evidence_index
from test_resource_usage import fixture
from test_shared_evidence import bundle


def measured_cell(*, peaks=(100, 200), walls=(10, 30), missing=False):
    # Summaries consume already-validated saved entries. Source validation has
    # separate independent packet/event/artifact controls and actual owner tests.
    row = deepcopy(bundle()["cells"][0])
    row["history"] = []
    entries = []
    for i, (peak, wall) in enumerate(zip(peaks, walls)):
        packet, *_ = fixture()
        aid = f"{i+1:032x}"
        packet["attempt_id"] = aid
        packet["duration"].update(wall_ns=wall, cpu_ns=2*wall)
        packet["memory"]["peak_resident_bytes"] = peak
        packet["execution_state"] = "FAILED" if i == 0 else "SUCCEEDED"
        packet["memory"]["point"] = "observer-call" if i == 0 else "job-payload-before-encoding"
        row["history"].append({"attempt_id": aid, "state": packet["execution_state"], "error_code": None})
        entries.append({"attempt_id": aid, "status": "RECORDED", "reason": None, "packet": packet,
            "artifact": {"artifact_id": fingerprint(packet)}, "publication_event": {"hash": fingerprint([aid, "event"])}})
    if missing:
        aid = "f"*32
        row["history"].append({"attempt_id": aid, "state": "TIMEOUT", "error_code": "TIMEOUT"})
        entries.append({"attempt_id": aid, "status": "UNAVAILABLE", "reason": "MISSING_OBSERVATION",
                        "packet": None, "artifact": None, "publication_event": None})
    row["resource_usage"] = {"schema_version": "pirc27-resource-history-v1", "attempts": entries}
    return row


def test_all_attempts_include_failed_checkpoint_history_and_never_add_rss():
    summary = summarize_resources([measured_cell()])
    assert summary["observed_attempt_count"] == 2
    assert summary["pipeline_wall_ns"] == 40 and summary["pipeline_cpu_ns"] == 80
    assert summary["maximum_observed_self_peak_bytes"] == 200  # Not100+200.
    assert summary["duration_complete"] is summary["memory_complete"] is True
    assert summary["duration_scope"] == "worker-validation-method-reference-qualification-pipeline"
    assert summary["memory_scope"] == "current-process-lifetime-through-observation"
    assert summary["peak_aggregation"] == "max-of-observed-self-peaks;not-additive;not-phase-delta;not-tree-peak"
    assert len(summary["source_artifact_ids"]) == 2


def test_hard_killed_attempt_does_not_become_free_time_or_zero_memory():
    summary = summarize_resources([measured_cell(missing=True)])
    assert summary["pipeline_wall_ns"] is summary["pipeline_cpu_ns"] is None
    assert summary["observed_pipeline_wall_ns"] == 40 and summary["observed_pipeline_cpu_ns"] == 80
    assert summary["maximum_observed_self_peak_bytes"] == 200
    assert summary["duration_complete"] is summary["memory_complete"] is False
    assert summary["unavailable_attempt_ids"] == ["f"*32]


def test_unavailable_native_memory_does_not_erase_measured_duration():
    row = measured_cell(peaks=(100,), walls=(10,))
    row["resource_usage"]["attempts"][0]["packet"]["memory"].update(status="UNAVAILABLE", peak_resident_bytes=None,
        resident_counter=None, reason="NATIVE_COUNTER_UNAVAILABLE")
    summary = summarize_resources([row])
    assert summary["pipeline_wall_ns"] == 10 and summary["duration_complete"] is True
    assert summary["maximum_observed_self_peak_bytes"] is None and summary["memory_complete"] is False
    assert summary["memory_unavailable_attempt_ids"] == ["1".zfill(32)]


def test_legacy_mixed_with_measured_remains_incomplete_not_zero():
    row = measured_cell()
    summary = summarize_resources([row, bundle()["cells"][1]])
    assert summary["legacy_unavailable_cell_count"] == 1
    assert summary["pipeline_wall_ns"] is None and summary["duration_complete"] is False
    assert summary["maximum_observed_self_peak_bytes"] == 200 and summary["memory_complete"] is False


def test_unattempted_new_cells_have_no_fictitious_zero_measurement():
    row = measured_cell(peaks=(), walls=())
    summary = summarize_resources([row])
    assert summary["unattempted_cell_count"] == 1 and summary["observed_attempt_count"] == 0
    assert summary["pipeline_wall_ns"] is summary["observed_pipeline_wall_ns"] is None
    assert summary["maximum_observed_self_peak_bytes"] is None


def test_stratum_csv_and_index_copy_exact_frozen_resource_summary():
    value = aggregate(bundle())
    row = measured_cell()
    arms, _ = aggregate_stratum([row], row["arm_id"], [], include_resource_summaries=True)
    expected = summarize_resources([row])
    assert arms[0]["resource_usage_summary"] == expected
    value["arms"][0]["resource_usage_summary"] = expected
    table = csv_bytes(value)
    records = list(csv.DictReader(io.StringIO(table.decode())))
    own = [r for r in records if r["arm_id"] == value["arms"][0]["arm_id"]]
    assert own and all(json.loads(r["resource_usage_summary"]) == expected for r in own)
    index = evidence_index(value, table)
    claims = [c for c in index["claims"] if c["arm_id"] == value["arms"][0]["arm_id"]]
    assert all(c["resource_usage_summary"] == expected for c in claims)
    assert index["resource_usage_summaries"][0]["resource_usage_summary"] == expected


def test_default_transport_does_not_enable_new_columns_without_runtime_bridge():
    row = measured_cell()
    arms, _ = aggregate_stratum([row], row["arm_id"], [])
    assert "resource_usage_summary" not in arms[0]


def test_explicit_opt_in_reaches_every_stratum_without_changing_legacy_bytes(monkeypatch):
    module = importlib.import_module("scripts.pirc25.aggregate")
    original = module.aggregate_stratum
    calls = []
    def observe(*args, **kwargs):
        calls.append(kwargs["include_resource_summaries"])
        return original(*args, **kwargs)
    monkeypatch.setattr(module, "aggregate_stratum", observe)
    value = module.aggregate(bundle(), include_resource_summaries=True)
    assert calls and all(v is True for v in calls)
    assert value["aggregate_hash"] == "9f8cd08e836d0ddf6e1eab7290708cf17b777528ed9c41acccd27c59deca7913"


@pytest.mark.parametrize("flag", [1, None, "true"])
def test_resource_schema_change_is_not_enabled_by_truthiness(flag):
    with pytest.raises(ValueError, match="explicit boolean"):
        aggregate(bundle(), include_resource_summaries=flag)


def test_all_failed_stratum_keeps_resource_evidence_outside_quality_claims():
    row = measured_cell()
    row.update(status="FAILED", metrics=None)
    arms, _ = aggregate_stratum([row], row["arm_id"], [], include_resource_summaries=True)
    value = aggregate(bundle())
    arms[0].update(stratum_id="failed-resource-stratum", comparison_dimensions={})
    value["arms"] = arms
    table = csv_bytes(value)
    index = evidence_index(value, table)
    assert not index["claims"]
    assert index["resource_usage_summaries"][0]["resource_usage_summary"]["pipeline_wall_ns"] == 40
    records = list(csv.DictReader(io.StringIO(table.decode())))
    assert records[0]["value"] == "" and json.loads(records[0]["resource_usage_summary"])["maximum_observed_self_peak_bytes"] == 200


def test_legacy_aggregate_csv_and_index_bytes_are_unchanged():
    value = aggregate(bundle())
    table = csv_bytes(value)
    assert value["aggregate_hash"] == "9f8cd08e836d0ddf6e1eab7290708cf17b777528ed9c41acccd27c59deca7913"
    assert hashlib.sha256(table).hexdigest() == "cbd9c71ca061b9cf6afd04e1df0e49ac3316ca3a05295b44921b26f5b35b1069"
    assert fingerprint(evidence_index(value, table)) == "d9815e6ddc28abcc563d17321cffd1da075d9e83b1ec99413e21fd95bece4c60"
