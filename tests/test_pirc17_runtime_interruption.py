"""One retained original timing interruption; no correction or science gate."""
from collections import Counter
import hashlib
import json
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"
EVIDENCE = "paper/pirc17/runtime-interruption-disclosure-v1.json"


def disclosure():
    return json.loads((PAPER / "runtime-interruption-disclosure-v1.json").read_text(encoding="utf-8"))


def test_exact_original_scalar_record_and_counter_arithmetic():
    data = disclosure()
    assert data["source_artifact_content_sha256"] == (
        "7c2325f975990c06ddb2c1ac28685f8aa7f78e65ab33f88ad580403861e55b66")
    assert data["original_condition"] == dict(
        matrix="terrain", subject="loo-surface", kind="runtime_cold",
        repetition=0, trials_per_condition=5)
    recorded = data["recorded"]
    assert recorded["prediction_seconds"] == 2315.9963217000004
    assert recorded["actual_horizon_seconds"] == 1801
    assert recorded["end_to_end_ms"] == (
        recorded["ended_monotonic_ns"] - recorded["started_monotonic_ns"]) / 1e6
    assert recorded["prediction_seconds"] * 1000 == pytest.approx(recorded["end_to_end_ms"])
    stages = recorded["inclusive_stage_ms"]
    assert stages["checkpoint_and_input_io"] + stages["rollout"] == pytest.approx(
        recorded["end_to_end_ms"])
    assert 0 < stages["terrain_io_and_query"] < stages["rollout"]


def test_confirmed_event_gap_is_not_subtracted_or_a_new_denominator():
    data = disclosure()
    host = data["host_observation"]
    assert host["event_timestamp_gap_seconds"] == 30 * 60 + 43
    assert host["sleep_event_id"] == 42 and host["resume_event_id"] == 1
    assert host["original_trial_overlaps_observed_sleep"] is True
    assert "later paired" in host["endpoint_mapping"]
    assert "not a precise CPU-inactivity duration" in host["gap_resolution"]
    disposition = data["disposition"]
    assert disposition["original_values_and_costs_retained"]
    assert disposition["original_trial_denominator_retained"]
    for key in (
        "trial_excluded", "sleep_subtracted", "replacement_trial_run",
        "uninterrupted_latency_certified", "affected_summary_uninterrupted_latency_certified",
        "all_other_trials_interruption_free_certified", "complete_runtime_qualification",
        "independent_saved_output_audit_completed", "predictive_scores_recomputed",
        "predictive_scores_independently_validated", "scientific_claim_authorized", "human_accepted",
    ):
        assert disposition[key] is False, key


def test_anonymous_projection_does_not_export_routes_or_start_experiments():
    data = disclosure()
    for field in ("new_fits", "new_forecasts", "new_scores_or_resampling", "new_map_queries"):
        assert data[field] == 0
    assert data["private_case_data_exported"] is False
    forbidden = {
        "origin_id", "sample_id", "independent_block_id", "case_sha256", "work_id",
        "artifact_path", "positions_m", "coordinates", "maps", "arrays",
        "hardware", "hostname", "filepath",
    }
    def check(value):
        if isinstance(value, dict):
            assert not forbidden.intersection(value)
            for child in value.values():
                check(child)
        elif isinstance(value, list):
            for child in value:
                check(child)
    check(data)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_main_manuscripts_make_affected_cost_claims_explicit(language):
    text = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    section = text.split(r"\label{sec:runtime-environment}", 1)[1].split(r"\section{", 1)[0]
    for token in ("loo-surface", "2315.996", "1801", r"perf\_counter\_ns"):
        assert token in section
    if language == "en":
        for phrase in (
            "30~min~43~s", "without subtracting", "five-trial denominator",
            "any affected", "not isolated uninterrupted", "later paired clock",
            "Other trials have", "qualification remains pending",
        ):
            assert phrase in section
    else:
        for phrase in (
            "30 分 43 秒", "不扣除休眠", "五次试验分母", "受影响的分位数",
            "不能作为无中断", "后续时钟配对", "不认证其他试验", "资格仍待核对",
        ):
            assert phrase in section


def test_cost_review_response_binds_new_disclosure_without_promoting_acceptance():
    registry = json.loads((PAPER / "review-response-v1.json").read_text(encoding="utf-8"))
    item = next(row for row in registry["items"] if row["id"] == "P1-23")
    assert EVIDENCE in item["evidence"]
    bindings = {row["path"]: row["sha256"] for row in registry["evidence_files"]}
    assert bindings[EVIDENCE] == hashlib.sha256(
        (PAPER / "runtime-interruption-disclosure-v1.json").read_bytes()).hexdigest()
    assert item["status"] == "awaiting_original_results"
    assert "休眠" in item["response"] and "受影响" in item["remaining"]
    assert not item["final_review_accepted"]
    assert dict(Counter(row["status"] for row in registry["items"])) == {
        "draft_checked": 20, "partial": 14, "awaiting_original_results": 7,
        "permission_unverified": 1,
    }
    assert len(registry["items"]) == 42 and registry["accepted_items"] == 0
    assert not registry["all_review_items_or_paper_complete"]
    ledger = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))
    assert not ledger["final_empirical_results_integrated"]
    assert not ledger["human_accepted"]
