"""Main-body mechanism clarity, without fitting or forecasting."""
import json
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"


@pytest.mark.parametrize("language", ["en", "zh"])
def test_baseline_training_and_prediction_have_explicit_reading_order(language):
    main = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    full = (PAPER / language / "reader-v4-full.tex").read_text(encoding="utf-8")
    assert main.index(r"\label{sec:models}") < main.index(r"\input{reader-v4-full.tex}") < main.index(r"\label{sec:forecast-methods}")
    assert r"\label{sec:training-methods}" in full
    assert r"\input{reader-v8-procedures.tex}" in main
    table = (PAPER / language / "reader-v8-procedures.tex").read_text(encoding="utf-8")
    assert all(name in table for name in ("CV", "HSM", "RDM", r"\tau"))
    assert "not the separate terrain" in main if language == "en" else "不是地形分支的base" in main


@pytest.mark.parametrize("language", ["en", "zh"])
def test_grouping_and_component_refitting_are_not_only_names(language):
    text = (PAPER / language / "reader-v4-full.tex").read_text(encoding="utf-8")
    assert all(token in text for token in (r"\widehat\Theta_{\rm pool}", "eq:rdm-grouping", "0.35", "0.65", "Reptile"))
    phrases = ("original", "not retained as a common drift", "segment count", "not three fixed geographic angle sectors") if language == "en" else ("原始位移率", "不作为共同漂移保留", "段数近似平衡", "不是三个固定地理角度区间")
    assert all(phrase in text for phrase in phrases)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_prediction_distinguishes_random_redraw_from_rotation_and_integration(language):
    text = (PAPER / language / "reader-v4-propagation.tex").read_text(encoding="utf-8")
    assert all(token in text for token in ("eq:mode-update-rules", r"\pi_j", r"\mathbf1", r"\tau=60", "h=5", "2,2,2", "2,1,3"))
    phrases = ("independently", "same component again", "not a cyclic", "cannot", "grouping or redrawing") if language == "en" else ("独立重新抽取", "连续抽到同一分量", "轮流切换", "不能单独证明")
    assert all(phrase in text for phrase in phrases)


def test_code_verification_contract_has_distinct_training_and_forecast_changes():
    record = json.loads((PAPER / "reader-v8-methods.json").read_text(encoding="utf-8"))
    hsm, rdm = (record["procedures"][name] for name in ("HSM-SDE", "RDM-SDE"))
    assert hsm["components"] == rdm["components"] == 3
    assert hsm["grouping_unit"] != rdm["grouping_unit"]
    assert hsm["forecast_modes"] != rdm["forecast_modes"]
    assert record["shared_default_settings"]["reference_interval_saved_seconds"] == 60
    assert record["shared_default_settings"]["maximum_integration_step_saved_seconds"] == 5
    assert not record["numeric_evidence_changed"]
    assert record["new_fits_forecasts_scores_figures_or_inference"] == 0
