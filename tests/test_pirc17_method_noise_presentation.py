"""Pure arithmetic/layout bindings; not model fitting or scientific acceptance."""
import hashlib
import json
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"


def evidence():
    return json.loads((PAPER / "method-noise-description-v1.json").read_text(encoding="utf-8"))


def test_pinned_projection_and_unchanged_original_fit_diagnostics():
    ledger = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))
    entry = ledger["saved_method_noise_description"]
    assert hashlib.sha256((PAPER / "method-noise-description-v1.json").read_bytes()).hexdigest() == entry["projection_sha256"]
    base_bytes = (PAPER / "fit-diagnostics-v1.json").read_bytes()
    assert hashlib.sha256(base_bytes).hexdigest() == entry["original_aggregate_projection_sha256"]
    assert entry["original_aggregate_projection_sha256"] == (
        "b3d8b6e440399779f5fbac999aba13b23ab0749144441a4b767e746ae3123e3d")
    base = json.loads(base_bytes)
    result = evidence()
    assert result["method_fit_count"] == len(result["methods"]) == 16
    assert result["prediction_configuration_count"] == 28
    assert result["mode_parameter_records"] == 44
    assert result["base_projection_sha256"] == entry["original_aggregate_projection_sha256"]
    for m, old in zip(result["methods"], base["methods"]):
        for field in ("representative_slot", "prediction_slots", "original_record_sha256",
                      "model_kind", "reference_interval_seconds", "selected_estimator_drift_fraction"):
            assert m[field] == old[field]
        assert m["selected_covariance_scale_already_in_saved_R"] == old["selected_covariance_scale"]


def test_all_modes_normalized_finite_noise_embedding_and_no_extra_scale():
    for m in evidence()["methods"]:
        modes = m["modes"]
        assert [x["mode_index"] for x in modes] == list(range(m["mode_count"]))
        assert sum(x["final_mode_probability"] for x in modes) == pytest.approx(1., abs=1e-12)
        for x in modes:
            r = x["saved_rate_eigenvalues_m2_per_s2"]
            q = x["embedded_diffusion_eigenvalues_m2_per_s"]
            assert 0 < r[0] <= r[1]
            assert x["bound_rate_eigenvalues_m2_per_s2"] == r
            assert q == pytest.approx([m["reference_interval_seconds"] * v for v in r])
            assert x["saved_rate_asymmetry_m2_per_s2"] == 0
            assert not x["bind_time_negative_roundoff_repair_required"]
        expected = [min(x["embedded_diffusion_eigenvalues_m2_per_s"][0] for x in modes),
                    max(x["embedded_diffusion_eigenvalues_m2_per_s"][1] for x in modes)]
        assert m["diffusion_eigenvalue_envelope_m2_per_s"] == expected
        assert not m["per_role_mode_counts_retained_in_saved_artifact"]
        assert not m["final_probabilities_multiplied_by_exposure_label_to_invent_counts"]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_exact_sixteen_row_appendix_parameter_table(language):
    tex = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    label = r"\label{tab:method-noise-parameters}"
    assert tex.count(label) == 1
    assert tex.index(label) > tex.index(r"\appendix")
    start = tex.index(label)
    table = tex[start:tex.index(r"\end{tabular}", start)]
    for m in evidence()["methods"]:
        name = m["representative_slot"].replace("_", r"\_")
        pi = ", ".join(f"{x['final_mode_probability']:.4f}" for x in m["modes"])
        low, high = m["diffusion_eigenvalue_envelope_m2_per_s"]
        row = (r"\texttt{" + name + "} & " + str(int(m["reference_interval_seconds"]))
               + " & " + pi + f" & {low:.3f} / {high:.3f}" + r"\\")
        assert table.count(row) == 1
    assert table.count(r"\texttt{arm-") == 16


@pytest.mark.parametrize("language", ["en", "zh"])
def test_mainline_equation_and_full_spectra_are_bound_to_saved_numbers(language):
    tex = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    main = tex.split(r"\appendix", 1)[0]
    assert main.count(r"\label{eq:saved-method-noise}") == 1
    assert r"R_m=s^2\widetilde R_m" in main
    assert r"Q_m=\tau R_m" in main
    full = next(m for m in evidence()["methods"] if m["representative_slot"] == "arm-01/full")
    for x in full["modes"]:
        low, high = x["embedded_diffusion_eigenvalues_m2_per_s"]
        assert f"({low:.3f},{high:.3f})" in main
    assert "2.89" in main
    assert r"\ref{tab:method-noise-parameters}" in main
    assert r"\path{paper/pirc17/method-noise-description-v1.json}" in main


def test_missing_mode_counts_and_forecast_covariance_not_invented():
    scope = evidence()["scope"]
    assert scope["saved_covariances_already_include_selected_scale_squared"]
    assert scope["reference_interval_not_integration_step"]
    assert scope["mode_probabilities_are_fitted_parameters"]
    for field in ("scale_applied_again", "per_role_mode_counts_available",
                  "mixture_predictive_covariance_or_final_calibration_inferred_from_Q",
                  "coefficient_matrices_private_paths_or_trajectory_identifiers_exported",
                  "independent_saved_output_audit_completed", "all_review_items_or_paper_complete"):
        assert not scope[field]
    assert scope["new_fits_forecasts_particle_scores_resampling_or_map_queries"] == 0
    ledger = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))["saved_method_noise_description"]
    assert ledger["review_items"] == ["P1-02", "P1-06"]
    assert not ledger["final_probabilities_are_per_role_mode_frequencies"]
    assert not ledger["per_role_mode_counts_available"]
    assert not ledger["all_review_items_or_paper_complete"]


@pytest.mark.parametrize("name", ["experiments/nex326/model.py", "experiments/pirc17/method_training.py",
                                 "experiments/pirc17/method_rollout.py"])
def test_original_noise_source_bindings_are_not_replaced(name):
    assert evidence()["source_sha256"][name] == {
        "experiments/nex326/model.py": "8863e936419a55d95b4fe31ddb8790fcbb0a923b57cbc3f77cde3e095dea9aa2",
        "experiments/pirc17/method_training.py": "65c78934a74f2725bf7f792cd851178fcc539d67a912fc8d33253d45a1d15598",
        "experiments/pirc17/method_rollout.py": "076e3964d8f2f18ea45c93c964962be01a74eff62c380cc8719b5e3af4ac3560",
    }[name]
