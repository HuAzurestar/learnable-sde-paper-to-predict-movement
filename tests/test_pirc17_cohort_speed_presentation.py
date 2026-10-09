# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Original saved-scalar population description, not forecast qualification."""
import hashlib
import json
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"
PATH = PAPER / "final-cohort-speed-description-v1.json"
D = json.loads(PATH.read_text(encoding="utf-8"))
L = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))
GROUPS = ("released", "temporal_excluded", "coverage_excluded_after_temporal", "eligible_not_selected", "selected_primary")


def test_every_original_window_and_stage_matches_existing_population():
    for source in ("final-cohort-description-v1.json", "final-cohort-geography-description-v1.json", "final-cohort-duration-description-v1.json"):
        reference = json.loads((PAPER / source).read_text(encoding="utf-8"))
        for key in ("released", "metadata_complete", "temporal_support", "joint_feature_validity", "selected_primary"):
            assert {k: D["stages"][key][k] for k in ("windows", "recording_hash_blocks")} == {
                k: reference["stages"][key][k] for k in ("windows", "recording_hash_blocks")}
    assert sum(D["stages"][g]["windows"] for g in GROUPS[1:]) == 12370
    for stage in D["stages"].values():
        value = stage["window_median_saved_speed"]
        assert value["windows"] == value["statistic_successes"] == stage["windows"]
        assert value["statistic_failures"] == 0 and value["failure_reasons"] == {}
        assert value["full_stage_distribution_available"] == bool(stage["windows"])


def test_exact_saved_scalar_projection_values_not_online_velocity():
    names = ("minimum", "q25", "median", "q75", "maximum")
    assert [D["stages"]["released"]["window_median_saved_speed"][k] for k in names] == [
        0.09694444444444443, 1.1910279623743105, 1.6205555555555553, 1.9491319444444444, 4.0675]
    assert [D["stages"]["selected_primary"]["window_median_saved_speed"][k] for k in names] == [
        0.8313888888888888, 1.2445833333333334, 1.4855555555555555, 1.6364930555555555, 2.553611111111111]
    assert D["stages"]["metadata_excluded"]["window_median_saved_speed"]["median"] is None
    assert "not pooled-point or duration-weighted" in D["definition"]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_all_bilingual_cells_and_statistical_definitions(language):
    tex = (PAPER / language / "historical-main-v1.tex").read_text(encoding="utf-8")
    for label in ("sec:final-cohort-speeds", "tab:final-cohort-speeds", "eq:cohort-window-speed"):
        assert tex.count(r"\label{" + label + "}") == 1
    table = tex.split(r"\label{tab:final-cohort-speeds}", 1)[1].split(r"\end{tabular}", 1)[0]
    for name in GROUPS:
        stage = D["stages"][name]
        v = stage["window_median_saved_speed"]
        cells = [f"{stage['windows']:,}", f"{v['median']:.3f} [{v['q25']:.3f},{v['q75']:.3f}]",
                 f"{v['minimum']:.3f}--{v['maximum']:.3f}", str(v["statistic_failures"])]
        assert " & ".join(cells) + r"\\" in table
    for en, zh in (("including its future observations", "也包含后续观测"),
                   ("not predictor inputs or revised eligibility", "不输入预测器或重定资格"),
                   ("not a significance test", "不是显著性检验"),
                   ("not a distribution of online secant inputs", "不是在线割线输入"),
                   ("were not certified in the", "不在原发布认证绑定中"),
                   ("repeats\nthe last interval speed", "复制最后一个区间速率")):
        assert (en if language == "en" else zh) in tex
    assert "\n+" not in tex


def test_original_source_pins_and_separate_retained_script_identity():
    b = D["bindings"]
    assert b["alignment_file_sha256"] == "32761ada086f1530b66746dc9bc05a0e8cf33927da1ada6ee6c7723b0f8cb028"
    assert b["trajectory_file_sha256"] == "2afc0f4f03f0c653b9d977e865a4bdbef309d155ce1c010408922eacfa122557"
    assert b["retained_construction_script_sha256"] == "96eb327e834540d8ec3dc121a12b7ee484b51aeeb64d39861639a16b087c75d5"
    assert b["retained_builder_script_sha256"] == "9c41c05b32727e8a51e2e896fc4b6a1a88220379c65760198d0fe574c94bfd0f"
    assert hashlib.sha256((PAPER / "final-cohort-description-v1.json").read_bytes()).hexdigest() == b["base_cohort_description_sha256"]
    assert "not independently certified" in D["declared_unit"]


def test_bounded_columns_no_new_model_inputs_experiments_or_recovery_gate():
    scope = D["scope"]
    assert scope["alignment_columns_decoded"] == ["file_id", "segment_id", "source_segment_id", "segment_point_index", "source_point_index"]
    assert scope["trajectory_columns_decoded"] == ["file_id", "segment_id", "t", "speed"]
    for field in ("source_speed_is_saved_interval_scalar_not_norm_of_centered_vx_vy", "source_endpoint_padding_retained",
                  "statistical_failures_retained_in_original_denominators", "equal_window_summary_not_independent_participant_distribution",
                  "future_observation_used_only_for_posthoc_population_description"):
        assert scope[field]
    for field in ("source_construction_scripts_bound_by_original_release", "velocity_outlier_clipping_or_clock_speed_reconstruction",
                  "original_eligibility_or_selection_recomputed", "model_inputs_or_centered_velocity_components_reconstructed",
                  "positions_maps_predictions_or_scientific_scores_decoded", "whole_snapshot_revalidation_or_forecast_restart_gate",
                  "independent_saved_output_audit_completed", "private_identities_epochs_paths_or_coordinates_exported",
                  "all_review_items_or_paper_complete"):
        assert not scope[field]
    assert scope["new_fits_forecasts_scores_resampling_or_map_queries"] == 0


def test_projection_pin_and_prior_projection_flags_remain_scoped():
    entry = L["original_final_cohort_speed_description"]
    assert entry["projection_sha256"] == hashlib.sha256(PATH.read_bytes()).hexdigest()
    assert entry["statistic_failures"] == 0 and entry["original_final_windows"] == 12370
    for field in ("original_eligibility_or_selection_changed", "online_or_simulated_velocity_distribution_reconstructed",
                  "physical_speed_calibration_or_causal_effect_established", "all_review_items_or_paper_complete"):
        assert not entry[field]
    assert not L["original_final_cohort_duration_description"]["speed_distributions_reconstructed"]
    assert not L["original_final_cohort_geography_description"]["speeds_or_duration_distributions_reconstructed"]
    assert not L["final_empirical_results_integrated"] and not L["human_accepted"]


def test_private_identities_positions_epochs_and_workstation_paths_not_exported():
    text = PATH.read_text(encoding="utf-8")
    for key in ("sample_id", "segment_id", "file_id", "independent_block_id", "absolute_epoch_ns", "longitude", "latitude"):
        assert json.dumps(key) + ":" not in text
    assert all(drive + chr(58) + chr(92) not in text for drive in ("C", "E"))
