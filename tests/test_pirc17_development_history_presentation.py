# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Retained clock-statistic checks; not history sensitivity or paper acceptance."""
import hashlib
import json
from pathlib import Path
import re

import pytest

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"
D = json.loads((PAPER / "development-history-description-v1.json").read_text(encoding="utf-8"))
L = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_original_selected_clock_scope_matches_existing_feature_and_fit_projections():
    feature = json.loads((PAPER / "feature-design-description-v1.json").read_text(encoding="utf-8"))
    fit = json.loads((PAPER / "terrain-fit-scope-description-v1.json").read_text(encoding="utf-8"))
    assert D["base_feature_projection_sha256"] == sha(PAPER / "feature-design-description-v1.json")
    assert D["base_history_projection_sha256"] == sha(PAPER / "history-missingness-description-v1.json")
    assert D["selected_feature_files"] == feature["selected_feature_files"] == fit["selected_feature_files"] == 397
    for field in ["selected_sources_sha256", "original_input_identity_sha256", "original_context_file_sha256"]:
        assert D[field] == feature[field] == fit[field]
    assert len(D["source_sha256"]) == 3
    assert D["metadata_columns_decoded"] == ["dataset_version", "file_id", "segment_id", "split",
                                             "independent_block_id", "point_index", "absolute_epoch_ns"]


@pytest.mark.parametrize("role,n,expected,ten_counts", [
    ("train", 404, [2., 2., 6., 12., 62.], {"shorter": 254, "equal": 13, "longer": 137}),
    ("validation", 81, [2., 2., 4., 11., 61.], {"shorter": 54, "equal": 3, "longer": 24})])
def test_original_observed_span_summary_and_ten_second_counts(role, n, expected, ten_counts):
    r = D["roles"][role]
    assert r["windows"] == n and r["retained_point_counts"] == {"2": 0, "3": n}
    s = r["origin_span"]
    assert [s[k] for k in ["minimum_seconds", "q25_seconds", "median_seconds", "q75_seconds", "maximum_seconds"]] == expected
    assert s["compared_with_stable_10s"] == ten_counts
    assert sum(s["span_bin_counts_seconds"].values()) == sum(ten_counts.values()) == s["count"] == n


@pytest.mark.parametrize("role,expected", [
    ("train", [5.992, 6., 8., 11., 36.]), ("validation", [6., 6., 7., 11., 35.])])
def test_first_tick_is_buffer_arithmetic_not_first_future_fitting_interval(role, expected):
    s = D["roles"][role]["first_tick_span_from_buffer_rule"]
    assert [s[k] for k in ["minimum_seconds", "q25_seconds", "median_seconds", "q75_seconds", "maximum_seconds"]] == expected
    gap = D["roles"][role]["last_gap"]
    for key in ["minimum_seconds", "q25_seconds", "median_seconds", "q75_seconds", "maximum_seconds", "mean_seconds"]:
        assert s[key] == pytest.approx(gap[key] + 5, abs=1e-12)
    assert D["scope"]["first_tick_spans_are_buffer_arithmetic_not_simulated_outputs"]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_bilingual_table_rows_and_complete_scope_are_explicit(language):
    tex = (PAPER / language / "historical-main-v1.tex").read_text(encoding="utf-8")
    assert tex.count(r"\label{tab:development-history-spans}") == 1
    history = tex.split(r"\label{sec:history-feedback}", 1)[1].split(r"\subsection{", 1)[0]
    timings = tex.split(r"\label{sec:empirical-history-timings}", 1)[1].split(r"\subsection{", 1)[0]
    for cells in ["404 & 2 & 2 & 6 & 12 & 62", "81 & 2 & 2 & 4 & 11 & 61",
                  "404 & 5.992 & 6 & 8 & 11 & 36", "81 & 6 & 6 & 7 & 11 & 35"]:
        assert cells in timings and cells not in history
    for value in ["397", "254", "13", "137", "54", "24"]:
        assert value in timings
    assert ("window-origin counts, not counts of independent participants" if language == "en"
            else "窗口起点数，不是独立参与者数") in timings
    assert ("not simulated outputs" if language == "en" else "不是模拟输出或敏感性实验") in timings
    assert ("not measured rollout velocity dispersions" if language == "en"
            else "不是测得的 rollout 速度离散程度") in history
    assert "has not been reconstructed here" not in history
    assert "尚未重建其完整跨度分布" not in history


def test_original_final_history_projection_remains_historically_scoped():
    old = json.loads((PAPER / "history-missingness-description-v1.json").read_text(encoding="utf-8"))
    assert not old["training_prefix_span_distribution_retained_in_this_projection"]
    assert not L["history_and_missing_input_description"]["training_prefix_span_distribution_reconstructed"]
    assert old["prefix_span_summary"]["origin_span_seconds"]["count"] == 46
    assert sha(PAPER / "history-missingness-description-v1.json") == (
        "36752fb1ee92575213e242631a16148dce06b26b3677234876df9c31fefe5087")


def test_ledger_binding_does_not_claim_full_feedback_diagnostics_or_final_acceptance():
    r = L["original_development_history_description"]
    assert r["projection_sha256"] == sha(PAPER / "development-history-description-v1.json")
    assert r["training_origins"] == 404 and r["validation_origins"] == 81
    assert r["review_items"] == ["P1-05"]
    assert r["terrain_training_and_validation_prefix_spans_described"]
    assert not r["ordinary_method_resampled_history_described"]
    assert r["new_fits_forecasts_scores_resampling_or_map_queries"] == 0
    for flag in ["training_rollout_distribution_equivalence_established",
                 "full_early_late_velocity_drift_distributions_or_history_sensitivity_established",
                 "physical_clock_provenance_certified", "independent_saved_output_audit_completed",
                 "all_review_items_or_paper_complete"]:
        assert not r[flag]
    assert not L["final_empirical_results_integrated"] and not L["human_accepted"]


def test_no_private_paths_clocks_positions_or_new_experiments_exported():
    scope = D["scope"]
    for flag in ["positions_velocities_drift_residuals_maps_or_final_eval_numeric_rows_decoded",
                 "clock_ticks_sample_identifiers_or_private_source_paths_exported",
                 "training_rollout_distribution_equivalence_established",
                 "history_sensitivity_or_out_of_bounds_rates_established",
                 "physical_source_clock_provenance_certified", "whole_snapshot_revalidated",
                 "independent_saved_forecast_audit_completed", "all_review_items_or_paper_complete"]:
        assert not scope[flag]
    assert scope["new_fits_forecasts_scores_resampling_or_map_queries"] == 0
    text = (PAPER / "development-history-description-v1.json").read_text(encoding="utf-8")
    assert not re.search(r"[A-Za-z]:[\\/]", text)
    for private in ["sample_id\"", "absolute_epoch_ns\":", "file_id\":"]:
        assert private not in text
