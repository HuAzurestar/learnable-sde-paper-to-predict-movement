# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Partial existing runtime scalars, not a repaired benchmark or new experiment."""
import hashlib
import json
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"
NAME = "runtime-interruption-census-v1.json"


def census():
    return json.loads((PAPER / NAME).read_text(encoding="utf-8"))


def test_original_design_and_partial_denominators_are_complete():
    data = census()
    assert data["original_design"] == dict(
        subjects=15, provider_cold_trials=75, warmup_trials=15, warm_trials=75,
        total_runtime_trials=165, trials_per_cold_or_warm_condition=5,
        warmups_in_latency_quantiles=0)
    assert data["snapshot_counts"] == dict(
        hash_verified_records=153, not_in_completed_snapshot=12,
        cold_records=70, warm_records=69, warmup_records=14)
    rows = data["subjects"]
    assert len(rows) == len({(r["matrix"], r["subject"]) for r in rows}) == 15
    for kind, expected_total, recorded_total in (
        ("runtime_cold", 75, 70), ("runtime_warmup", 15, 14), ("runtime_warm", 75, 69)
    ):
        conditions = [r["conditions"][kind] for r in rows]
        assert sum(r["expected_trials"] for r in conditions) == expected_total
        assert sum(r["recorded_trials"] for r in conditions) == recorded_total
        for row in conditions:
            assert row["expected_trials"] == row["recorded_trials"] + row["not_in_completed_snapshot"]
            assert row["warmup_excluded_from_quantiles"] is (kind == "runtime_warmup")
    bindings = data["source_artifact_content_sha256"]
    assert len(bindings) == len(set(bindings)) == 153
    assert all(len(v) == 64 and int(v, 16) >= 0 for v in bindings)


def test_two_original_flagged_records_are_not_corrected_or_excluded():
    data = census()
    expected = {
        ("all-terrain", 3): (
            "50f49474aa4f18d7405641fb42c32442def43b95dbb46ae035f8a8c18dfca95f",
            3000463.8613),
        ("loo-surface", 0): (
            "7c2325f975990c06ddb2c1ac28685f8aa7f78e65ab33f88ad580403861e55b66",
            2315996.3217),
    }
    flagged = data["flagged_existing_records"]
    assert len(flagged) == 2
    assert {(r["subject"], r["repetition"]) for r in flagged} == set(expected)
    for row in flagged:
        assert row["matrix"] == "terrain" and row["kind"] == "runtime_cold"
        sha, ms = expected[row["subject"], row["repetition"]]
        assert row["artifact_content_sha256"] == sha
        assert sha in data["source_artifact_content_sha256"]
        assert row["original_elapsed_ms"] == ms
        assert ms == (row["ended_monotonic_ns"] - row["started_monotonic_ns"]) / 1e6
        assert row["actual_horizon_seconds"] == 1801
        assert row["mapping_status"] == "possible_overlap_under_later_clock_mapping"
        assert row["values_costs_and_original_denominator_retained"]
        assert not row["sleep_subtracted"] and not row["trial_excluded"] and not row["replacement_trial_run"]
    for subject in data["subjects"]:
        cold = subject["conditions"]["runtime_cold"]
        assert cold["flagged_repetitions"] == (
            [3] if subject["subject"] == "all-terrain" else
            [0] if subject["subject"] == "loo-surface" else [])


def test_clock_flags_are_conservative_and_do_not_certify_unflagged_rows():
    data = census()
    clock = data["clock_scope"]
    assert clock["host_sleep_resume_event_pairs_observed"] == 4
    assert clock["host_clock_change_events_in_scan_window"] == 5
    assert clock["host_clock_change_events_during_mapped_record_span"] == 2
    assert clock["later_counter_to_utc_mapping_used"]
    for field in (
        "original_trial_endpoint_utc_available", "all_clock_adjustments_independently_qualified",
        "other_trials_interruption_free_certified", "event_timestamp_gaps_are_cpu_inactivity_durations",
        "private_host_event_timestamps_or_identity_exported"
    ):
        assert clock[field] is False
    assert all(value is False for value in data["disposition"].values())


def test_no_routes_arrays_new_work_or_qualification_are_invented():
    data = census()
    for field in ("new_fits", "new_forecasts", "new_scores_or_resampling", "new_map_queries"):
        assert data[field] == 0
    for field in ("prediction_arrays_loaded", "raw_routes_or_maps_loaded", "private_case_data_exported"):
        assert not data[field]
    forbidden = {"origin_id", "sample_id", "independent_block_id", "case_sha256", "work_id",
                 "artifact_path", "positions_m", "coordinates", "maps", "arrays", "hardware",
                 "hostname", "filepath", "sleep_utc", "resume_utc"}
    def check(value):
        if isinstance(value, dict):
            assert not forbidden.intersection(value)
            for v in value.values():
                check(v)
        elif isinstance(value, list):
            for v in value:
                check(v)
    check(data)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_two_flagged_conditions_are_visible_in_the_actual_main_manuscript(language):
    text = (PAPER / language / "historical-main-v1.tex").read_text(encoding="utf-8")
    section = text.split(r"\label{sec:runtime-environment}", 1)[1].split(r"\section{", 1)[0]
    for token in ("loo-surface", "all-terrain", "2315.996", "3000.464", "1801", "153"):
        assert token in section
    for phrase in (("clock-change", "does not certify", "scalar metadata")
                   if language == "en" else ("时钟变更", "不认证", "标量元数据")):
        assert phrase in section


def test_census_is_bound_to_the_unpromoted_cost_review_item():
    registry = json.loads((PAPER / "review-response-v1.json").read_text(encoding="utf-8"))
    item = next(row for row in registry["items"] if row["id"] == "P1-23")
    path = "paper/pirc17/" + NAME
    assert path in item["evidence"]
    entry = next(row for row in registry["evidence_files"] if row["path"] == path)
    assert entry["sha256"] == hashlib.sha256((PAPER / NAME).read_bytes()).hexdigest()
    assert item["status"] == "awaiting_original_results" and not item["final_review_accepted"]
    assert len(registry["items"]) == 42 and registry["accepted_items"] == 0
