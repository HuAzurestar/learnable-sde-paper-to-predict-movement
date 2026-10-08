"""Pure saved-artifact checks; registry coverage is not review acceptance."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"


def response():
    return json.loads((PAPER / "review-response-v1.json").read_text(encoding="utf-8"))


def test_all_original_items_have_one_response_and_explicit_remaining_scope():
    registry = response()
    expected = {f"P{priority}-{number:02d}" for priority, count in ((0, 6), (1, 26), (2, 10))
                for number in range(1, count + 1)}
    items = registry["items"]
    assert len(items) == len(expected) == 42
    assert {row["id"] for row in items} == expected
    for row in items:
        for field in ("original_title", "original_acceptance", "response", "remaining",
                      "manuscript_anchors", "evidence"):
            assert row[field], (row["id"], field)
    assert registry["review_source"]["issues_by_priority"] == {"P0": 6, "P1": 26, "P2": 10}
    assert registry["review_source"]["sha256"] == (
        "457688e8ba81c88b6c9f71f22da8f457fa2245809e1b1368c5e0aef5b824b65d")


def test_category_totals_are_draft_triage_not_final_closure():
    registry = response()
    counts = Counter(row["status"] for row in registry["items"])
    assert dict(counts) == registry["status_counts"]
    assert set(counts) == set(registry["status_definitions"])
    assert sum(counts.values()) == 42
    assert registry["accepted_items"] == 0
    assert not any(row["final_review_accepted"] for row in registry["items"])
    assert not registry["all_review_items_or_paper_complete"]
    assert not registry["independent_saved_output_audit_completed"]


def test_all_referenced_existing_evidence_bytes_match_reviewed_revision():
    registry = response()
    files = {entry["path"]: entry["sha256"] for entry in registry["evidence_files"]}
    assert len(files) == len(registry["evidence_files"]) >= 25
    for path, expected in files.items():
        resolved = (ROOT / path).resolve()
        assert resolved.is_relative_to(ROOT.resolve())
        assert path.startswith("paper/pirc17/") or path in {
            "scripts/describe_pirc17_target_times.py", "scripts/describe_pirc17_final_cohort.py",
            "scripts/plot_pirc17_calibration_blocks.py", "scripts/describe_pirc17_seed_stability.py",
            "scripts/plot_pirc17_method_horizons.py", "scripts/plot_pirc17_method_regions.py",
            "scripts/describe_pirc17_inertial.py", "scripts/render_pirc17_inertial_tables.py",
            "scripts/describe_pirc17_point_errors.py", "scripts/render_pirc17_point_error_tables.py"}
        assert hashlib.sha256(resolved.read_bytes()).hexdigest() == expected, path
    for row in registry["items"]:
        assert set(row["evidence"]).issubset(files), row["id"]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_each_response_anchor_exists_in_bilingual_reviewed_manuscript(language):
    text = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    inputs = re.findall(r"\\input\{([^}]+)\}", text)
    assert set(inputs) == {"all-method-absolute.tex", "method-seed-stability.tex",
                           "method-horizon-overview.tex", "method-horizon-tables.tex",
                           "method-region-overview.tex", "method-region-tables.tex",
                           "inertial-primary-comparison.tex", "point-error-horizons.tex",
                           "secondary-score-diagnostics.tex"}
    for filename in inputs:
        text += (PAPER / language / filename).read_text(encoding="utf-8")
    labels = Counter(re.findall(r"\\label\{([^}]+)\}", text))
    for row in response()["items"]:
        for anchor in row["manuscript_anchors"]:
            assert labels[anchor] == 1, (language, row["id"], anchor)


def test_response_cannot_authorize_new_experiments_or_replace_goal():
    registry = response()
    assert registry["new_fits_forecasts_scores_resampling_or_map_queries"] == 0
    assert not registry["additional_experiments_authorized_by_this_response"]
    assert registry["response_does_not_replace_original_full_goal"]
    ledger = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))
    assert not ledger["final_empirical_results_integrated"]
    assert not ledger["human_accepted"]


def test_known_missing_evidence_is_not_hidden_by_draft_checked_count():
    registry = response()
    items = {row["id"]: row for row in registry["items"]}
    history = json.loads((PAPER / "history-missingness-description-v1.json").read_text(encoding="utf-8"))
    for field in ("training_prefix_span_distribution_retained_in_this_projection",
                  "full_forecast_per_column_mask_rates_available",
                  "full_early_and_late_velocity_drift_distributions_available",
                  "missing_input_robustness_established",
                  "independent_saved_output_audit_completed"):
        assert not history[field]
    for item in ("P0-03", "P0-05", "P1-02", "P1-04", "P1-05",
                 "P1-08", "P1-11", "P1-12", "P1-13", "P1-15",
                 "P1-18", "P1-22", "P2-02", "P2-10"):
        assert items[item]["status"] == "partial"
    assert items["P1-20"]["status"] == "draft_checked"
    assert items["P1-06"]["status"] == "draft_checked"
    assert "paper/pirc17/terrain-fit-scope-description-v1.json" in items["P1-06"]["evidence"]
    assert "eq:terrain-rate-Q" in items["P1-06"]["manuscript_anchors"]
    assert items["P2-08"]["status"] == "draft_checked"
    for item in ("P0-06", "P1-16", "P1-17", "P1-19", "P1-23", "P1-24", "P2-09"):
        assert items[item]["status"] == "awaiting_original_results"
    assert items["P1-25"]["status"] == "permission_unverified"


def test_clock_draft_check_uses_original_fallback_not_physical_source_certification():
    import subprocess
    registry = response()
    item = next(row for row in registry["items"] if row["id"] == "P0-04")
    previous = json.loads(subprocess.check_output([
        "git", "show", "aff75cc52b6f9f177416550b03ef5459d332cb21:paper/pirc17/review-response-v1.json"
    ], cwd=ROOT).decode("utf-8"))
    original = next(row for row in previous["items"] if row["id"] == "P0-04")
    assert item["original_title"] == original["original_title"]
    assert item["original_acceptance"] == original["original_acceptance"]
    assert "否则" in item["original_acceptance"]
    assert item["status"] == "draft_checked"
    assert "原验收允许" in item["response"]
    assert "未获认证" in item["remaining"]
    assert not item["final_review_accepted"]
    clock = json.loads((PAPER/"clock-description-v1.json").read_text(encoding="utf-8"))
    assert not clock["scope"]["utc_or_sensor_clock_source_certified"]
    assert not clock["scope"]["physical_horizon_or_daylight_effect_certified"]
    assert not registry["all_review_items_or_paper_complete"]
