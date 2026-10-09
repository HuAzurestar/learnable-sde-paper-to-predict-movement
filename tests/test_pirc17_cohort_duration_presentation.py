# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Saved-clock distribution checks, not new eligibility or forecasts."""
import hashlib
import json
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"
PATH = PAPER / "final-cohort-duration-description-v1.json"
D = json.loads(PATH.read_text(encoding="utf-8"))
L = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))
GROUPS = ("released", "temporal_excluded", "coverage_excluded_after_temporal",
          "eligible_not_selected", "selected_primary")


def test_all_stage_denominators_match_unchanged_geography_and_original_cohort():
    geo = json.loads((PAPER / "final-cohort-geography-description-v1.json").read_text(encoding="utf-8"))
    for key, stage in D["stages"].items():
        assert {k: stage[k] for k in ("windows", "recording_hash_blocks")} == {
            k: geo["stages"][key][k] for k in ("windows", "recording_hash_blocks")}
        for span in ("visible_history", "followup", "whole_window"):
            assert stage[span]["windows"] == stage["windows"]
    assert sum(D["stages"][s]["windows"] for s in GROUPS[1:]) == 12370
    assert D["stages"]["metadata_excluded"]["windows"] == 0


def test_exact_recorded_followup_distribution_not_forecast_horizon():
    fields = ("minimum_seconds", "q25_seconds", "median_seconds", "q75_seconds", "maximum_seconds")
    assert [D["stages"]["released"]["followup"][k] for k in fields] == [2, 30, 69.753, 203, 4183]
    assert [D["stages"]["selected_primary"]["followup"][k] for k in fields] == [1808, 2034, 2323, 2519, 4143]
    assert D["stages"]["released"]["followup"]["at_least_1800s_count"] == 130
    assert D["stages"]["temporal_support"]["windows"] == 127
    assert D["stages"]["temporal_excluded"]["followup"]["at_least_1800s_count"] == 3
    assert sum(D["stages"][s]["followup"]["at_least_1800s_count"] for s in GROUPS[1:]) == 130


@pytest.mark.parametrize("language", ["en", "zh"])
def test_bilingual_table_matches_every_saved_cell_and_boundary(language):
    tex = (PAPER / language / "historical-main-v1.tex").read_text(encoding="utf-8")
    for label in ("tab:final-cohort-durations", "sec:final-cohort-durations"):
        assert tex.count(r"\label{" + label + "}") == 1
    table = tex.split(r"\label{tab:final-cohort-durations}", 1)[1].split(r"\end{tabular}", 1)[0]
    def number(x): return f"{x:.1f}".removesuffix(".0")
    for name in GROUPS:
        stage = D["stages"][name]
        value = stage["followup"]
        cells = [f"{stage['windows']:,}",
                 number(value["median_seconds"]) + " [" + number(value["q25_seconds"]) + "," + number(value["q75_seconds"]) + "]",
                 number(value["minimum_seconds"]) + "--" + number(value["maximum_seconds"]),
                 str(value["at_least_1800s_count"])]
        assert " & ".join(cells) + r"\\" in table
    assert "130/12,370" in tex and "38.7" in tex
    assert ("Saved speed is described separately" if language == "en" else "保存速率另见下文") in tex
    assert ("not certification of" if language == "en" else "不认证原物理UTC") in tex
    assert ("is not the retained last-two/three-point secant buffer" if language == "en"
            else "不等于实际保留的最后两/三个点割线缓冲") in tex
    assert "\n+" not in tex


def test_only_original_bound_clock_columns_and_no_whole_snapshot_gate():
    scope = D["scope"]
    assert scope["decoded_columns"] == ["dataset_version", "file_id", "segment_id", "split",
                                        "independent_block_id", "point_index", "absolute_epoch_ns"]
    assert D["bindings"]["used_clock_files"] == 1125
    for key in ("original_eligibility_or_selection_recomputed", "positions_speeds_feature_values_or_prediction_arrays_decoded",
                "invalid_clock_windows_dropped_or_time_differences_clipped", "physical_source_clock_provenance_certified",
                "whole_snapshot_revalidation_or_forecast_restart_gate", "independent_saved_output_audit_completed",
                "private_identities_epochs_paths_or_coordinates_exported", "all_review_items_or_paper_complete"):
        assert not scope[key]
    assert scope["new_fits_forecasts_scores_resampling_or_map_queries"] == 0


def test_new_projection_pin_and_unchanged_base_population():
    entry = L["original_final_cohort_duration_description"]
    assert entry["projection_sha256"] == hashlib.sha256(PATH.read_bytes()).hexdigest()
    assert entry["used_clock_sources_sha256"] == D["bindings"]["used_clock_sources_sha256"]
    base = PAPER / "final-cohort-description-v1.json"
    assert hashlib.sha256(base.read_bytes()).hexdigest() == D["bindings"]["base_cohort_description_sha256"]
    assert entry["released_history_spans_are_not_retained_predictor_buffer_spans"]
    assert not entry["speed_distributions_reconstructed"]
    assert not L["final_empirical_results_integrated"] and not L["human_accepted"]


def test_empty_stage_is_explicit_and_no_private_numeric_identity_export():
    assert D["stages"]["metadata_excluded"]["followup"]["median_seconds"] is None
    text = PATH.read_text(encoding="utf-8")
    for key in ("sample_id", "segment_id", "file_id", "independent_block_id", "absolute_epoch_ns"):
        assert json.dumps(key) + ":" not in text
    assert all(d + chr(58) + chr(92) not in text for d in ("C", "E"))
