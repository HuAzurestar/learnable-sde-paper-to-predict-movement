"""Saved-data arithmetic and bilingual presentation, not new experiments."""
import hashlib
import json
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"


def evidence():
    return json.loads((PAPER / "terrain-fit-scope-description-v1.json").read_text(encoding="utf-8"))


def test_original_fit_design_and_clock_population_bindings():
    entry = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))["original_terrain_fit_scope_description"]
    result = evidence()
    for name, field in (("terrain-fit-scope-description-v1.json", "projection_sha256"),
                        ("fit-diagnostics-v1.json", "original_fit_projection_sha256"),
                        ("feature-design-description-v1.json", "original_feature_projection_sha256")):
        assert hashlib.sha256((PAPER / name).read_bytes()).hexdigest() == entry[field]
    assert result["base_fit_projection_sha256"] == entry["original_fit_projection_sha256"]
    assert result["base_feature_projection_sha256"] == entry["original_feature_projection_sha256"]
    feature = json.loads((PAPER / "feature-design-description-v1.json").read_text(encoding="utf-8"))
    for key in ("original_context_file_sha256", "original_input_identity_sha256", "selected_sources_sha256", "selected_feature_files"):
        assert result[key] == feature[key]
    assert result["selected_feature_files"] == 397
    assert entry["training_transitions"] == 404 and entry["validation_transitions"] == 81


@pytest.mark.parametrize("role,count,median,q75,mean,maximum", [
    ("train", 404, 3., 6., 5.507430693069307, 38.),
    ("validation", 81, 2., 8., 6.62962962962963, 31.)])
def test_duration_summary_and_distinct_drift_diffusion_weights(role, count, median, q75, mean, maximum):
    r = evidence()["roles"][role]
    assert r["transitions"] == count
    assert r["minimum_seconds"] == r["q25_seconds"] == 1.
    assert r["median_seconds"] == median and r["q75_seconds"] == q75
    assert r["maximum_seconds"] == maximum and r["mean_seconds"] == pytest.approx(mean)
    assert r["equal_drift_row_weight"] == 1/count
    assert r["rate_outer_product_Q_coefficient_minimum_seconds"] == 1/count
    assert r["rate_outer_product_Q_coefficient_maximum_seconds"] == maximum/count
    assert sum(r["interval_bin_counts_seconds"].values()) == count
    assert r["sum_seconds"] == pytest.approx(count*mean)


def test_ten_Q_spectra_and_absolute_negative_roundoff_rule_are_not_rescaled():
    base = json.loads((PAPER / "fit-diagnostics-v1.json").read_text(encoding="utf-8"))
    rows = evidence()["terrain"]
    assert len(rows) == len(base["terrain"]) == 10
    for row, old in zip(rows, base["terrain"]):
        assert row["configuration"] == old["configuration"]
        assert row["original_record_sha256"] == old["original_record_sha256"]
        assert row["saved_eigenvalues_m2_per_s"] == old["diffusion_eigenvalues_m2_per_s"]
        assert 0 < row["saved_eigenvalues_m2_per_s"][0] <= row["saved_eigenvalues_m2_per_s"][1]
        assert row["negative_eigenvalue_rejection_threshold_m2_per_s"] == -1e-10
        assert row["symmetry_absolute_tolerance_m2_per_s"] == 1e-12
        assert row["saved_asymmetry_m2_per_s"] == 0
        assert not row["negative_roundoff_clamp_required_for_L"]
        assert not row["positive_floor_or_jitter_added_by_terrain_diffusion_estimator"]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_two_row_appendix_table_matches_original_clock_summary(language):
    tex = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    label = r"\label{tab:terrain-fit-intervals}"
    assert tex.count(label) == 1 and tex.index(label) > tex.index(r"\appendix")
    start = tex.index(label)
    table = tex[start:tex.index(r"\end{tabular}", start)]
    for role, label_name in (("train", "Training"), ("validation", "Validation")):
        r = evidence()["roles"][role]
        row = (f"{label_name} & {r['transitions']} & {r['minimum_seconds']:.2f} & "
               f"{r['median_seconds']:.2f} [{r['q25_seconds']:.2f}, {r['q75_seconds']:.2f}] & "
               f"{r['mean_seconds']:.2f} & {r['maximum_seconds']:.2f}" + r"\\")
        assert table.count(row) == 1
    assert r"\ref{tab:terrain-fit-intervals}" in tex.split(r"\appendix", 1)[0]
    assert r"\path{paper/pirc17/terrain-fit-scope-description-v1.json}" in tex


@pytest.mark.parametrize("language", ["en", "zh"])
def test_rate_Q_and_non_unbiased_boundary_are_explicit_in_mainline(language):
    main = (PAPER / language / "main.tex").read_text(encoding="utf-8").split(r"\appendix", 1)[0]
    assert main.count(r"\label{eq:terrain-rate-Q}") == 1
    assert r"\sum_{i=1}^n\Delta t_i\zeta_i\zeta_i^\top" in main
    assert r"\zeta_i=\Delta x_i/\Delta t_i-\widehat b_i" in main
    assert r"-10^{-10}" in main and r"10^{-12}" in main
    if language == "en":
        assert "not an unbiased estimator or joint drift--diffusion maximum likelihood" in main
        assert "without duration" in main
    else:
        assert "不作自由度校正" in main and "不是无偏估计" in main
        assert "不按时长" in main


def test_saved_only_scope_does_not_claim_final_acceptance():
    r = evidence()
    assert not r["weighting"]["diffusion_centered"]
    assert not r["weighting"]["diffusion_degrees_of_freedom_correction"]
    assert not r["weighting"]["joint_drift_diffusion_MLE_or_unbiased_estimator_claimed"]
    scope = r["scope"]
    assert scope["new_fits_forecasts_particle_scores_resampling_or_map_queries"] == 0
    assert all(not v for k, v in scope.items() if k != "new_fits_forecasts_particle_scores_resampling_or_map_queries")
    assert len(r["source_sha256"]) == 3
