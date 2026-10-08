"""Existing-cohort label counts, not new geographic performance estimates."""
import hashlib
import json
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"
PATH = PAPER / "final-cohort-geography-description-v1.json"
D = json.loads(PATH.read_text(encoding="utf-8"))
L = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))


def test_nested_stages_match_unchanged_original_cohort():
    cohort = json.loads((PAPER / "final-cohort-description-v1.json").read_text(encoding="utf-8"))
    for stage in ("released", "metadata_complete", "temporal_support", "joint_feature_validity", "selected_primary"):
        assert {k: D["stages"][stage][k] for k in ("windows", "recording_hash_blocks")} == cohort["stages"][stage]
    assert [D["stages"][s]["source_country_count"] for s in
            ("released", "temporal_support", "joint_feature_validity", "selected_primary")] == [63, 21, 14, 12]
    assert D["stages"]["temporal_excluded"]["windows"] == 12243
    assert D["stages"]["coverage_excluded_after_temporal"]["windows"] == 21
    assert D["stages"]["eligible_not_selected"]["windows"] == 60
    assert D["rejection_block_counts_not_additive_to_admitted_block_counts"]


def test_every_source_country_and_display_denominator_is_retained():
    for stage in D["stages"].values():
        assert len(stage["countries"]) == stage["source_country_count"]
        for key in ("windows", "recording_hash_blocks"):
            assert sum(v[key] for v in stage["countries"].values()) == stage[key]
    assert len(D["display_rows"]) == 16
    for stage in ("released", "temporal_support", "joint_feature_validity", "selected_primary"):
        for key in ("windows", "recording_hash_blocks"):
            assert sum(r[stage][key] for r in D["display_rows"][:-1]) == D["display_rows"][-1][stage][key]
    assert {r["source_country"] for r in D["display_rows"][:-2]} == (
        set(D["stages"]["selected_primary"]["countries"]) | {"HT", "NI"})


def test_same_selected_origins_and_composition_not_window_weighted():
    old = json.loads((PAPER / "preliminary-geography-v1.json").read_text(encoding="utf-8"))
    selected = D["stages"]["selected_primary"]["countries"]
    assert {k: v["recording_hash_blocks"] for k, v in selected.items()} == old["countries"]
    assert sum(selected[c]["recording_hash_blocks"] for c in ("GB", "BE", "LU")) == 33
    assert sum(D["stages"]["released"]["countries"][c]["recording_hash_blocks"]
               for c in ("GB", "BE", "LU")) == 493
    assert D["stages"]["released"]["countries"]["HT"] == {"windows": 1731, "recording_hash_blocks": 2}
    assert set(D["stages"]["joint_feature_validity"]["countries"]) - set(selected) == {"IT", "SI"}


def test_missing_harvest_area_is_counted_not_excluded_or_imputed():
    assert D["stages"]["released"]["source_harvest_area_missing_windows"] == 465
    assert D["stages"]["temporal_support"]["source_harvest_area_missing_windows"] == 2
    assert D["stages"]["joint_feature_validity"]["source_harvest_area_missing_windows"] == 0
    assert D["stages"]["selected_primary"]["source_harvest_area_missing_windows"] == 0
    assert all(stage["source_region_missing_windows"] == 0 for stage in D["stages"].values())


@pytest.mark.parametrize("language", ["en", "zh"])
def test_bilingual_display_matches_each_original_metadata_cell(language):
    tex = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    for label in ("sec:final-cohort-geography", "tab:final-cohort-geography"):
        assert tex.count(r"\label{" + label + "}") == 1
    table = tex.split(r"\label{tab:final-cohort-geography}", 1)[1].split(r"\end{tabular}", 1)[0]
    for row in D["display_rows"]:
        values = [f"{row[s]['windows']} ({row[s]['recording_hash_blocks']})"
                  for s in ("released", "temporal_support", "joint_feature_validity")]
        values.append(str(row["selected_primary"]["recording_hash_blocks"]))
        assert " & ".join(values) + r"\\" in table
    assert "33/46" in tex and "493/1094" in tex and "465" in tex
    assert ("not a significance test" if language == "en" else "不是显著性检验") in tex
    assert ("saved interval-speed" if language == "en"
            else "源表保存区间速率") in tex
    assert "\n+" not in tex
    assert ("not a criterion available from the visible prefix alone at deployment" if language == "en"
            else "不是部署时仅凭可见前缀即可判定的资格条件") in tex
    assert ("Future-route validity is used for admission, not passed to the predictor" if language == "en"
            else "未来路线有效性只用于入选，不传入预测器") in tex


def test_unchanged_base_projection_bytes_and_new_evidence_pin():
    b = D["bindings"]
    for filename, field in (("final-cohort-description-v1.json", "base_cohort_description_sha256"),
                            ("preliminary-geography-v1.json", "base_selected_geography_sha256")):
        assert hashlib.sha256((PAPER / filename).read_bytes()).hexdigest() == b[field]
    ledger = L["original_final_cohort_geography_description"]
    assert hashlib.sha256(PATH.read_bytes()).hexdigest() == ledger["projection_sha256"]
    assert ledger["source_country_counts"] == dict(released=63, temporal_support=21, joint_feature_validity=14, selected_primary=12)


def test_provenance_limitations_not_scientific_or_privacy_acceptance():
    scope = D["scope"]
    assert scope["raw_columns_decoded"] == ["file_id", "cluster_A"]
    assert not scope["cluster_metadata_in_original_release_binding"]
    assert scope["source_country_labels_not_verified_point_locations"]
    assert scope["source_country_not_participant_or_spatial_independence_unit"]
    for field in ("positions_speeds_durations_features_predictions_or_scores_decoded",
                  "private_sample_block_file_ids_or_coordinates_exported",
                  "original_eligibility_recomputed_or_selection_changed",
                  "geographical_performance_or_causal_effect_estimated",
                  "independent_saved_output_audit_completed", "all_review_items_or_paper_complete"):
        assert not scope[field]
    assert scope["new_fits_forecasts_scores_resampling_or_map_queries"] == 0
    ledger = L["original_final_cohort_geography_description"]
    assert not ledger["speeds_or_duration_distributions_reconstructed"]
    assert not ledger["participant_or_near_route_independence_established"]
    assert not L["final_empirical_results_integrated"] and not L["human_accepted"]


def test_projection_omits_private_identities_and_coordinates():
    text = PATH.read_text(encoding="utf-8")
    for key in ('"sample_id"', '"file_id"', '"independent_block_id"', '"longitude"', '"latitude"'):
        assert key + ":" not in text  # column names are declared, no identity values exported
    assert all(drive + chr(58) + chr(92) not in text for drive in ("C", "E"))
