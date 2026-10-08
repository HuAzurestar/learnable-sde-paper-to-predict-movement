"""Bound saved-score rendering checks; no fit, forecast or statistical test."""
from copy import deepcopy
from pathlib import Path

import pytest

from scripts import render_pirc17_inertial_tables as renderer

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"


def projection():
    return renderer.read_bound(PAPER / "inertial-primary-description-v1.json", renderer.SHA)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_exact_bilingual_saved_score_tables_and_manuscript_input(language):
    text = renderer.tex(projection(), language)
    assert text == (PAPER / language / "inertial-primary-comparison.tex").read_text(encoding="utf-8")
    assert text.count(r"\begin{table}") == 2
    assert "824.73" in text and "477.85" in text
    assert "31.17" in text and "50.57" in text
    assert "237.93" in text and "243.23" in text
    assert "934.03" in text and "609.27" in text
    assert "2095.78" in text and "1008.35" in text
    main = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    assert main.count(r"\input{inertial-primary-comparison.tex}") == 1
    assert "41.100259" in text
    assert "49--67" in text and "1785--1814" in text


@pytest.mark.parametrize("field", ["paired_blocks", "primary_full_forecasts_used",
    "primary_inertial_paths_used", "auxiliary_inertial_paths_total", "nominal_target_tolerance_seconds"])
def test_incomplete_or_changed_population_is_refused(field):
    data = deepcopy(projection())
    data[field] -= 1
    with pytest.raises(ValueError):
        renderer.tex(data, "en")


@pytest.mark.parametrize("field", ["new_fits", "new_forecasts", "new_particle_scores",
    "new_bootstrap_or_tests", "independent_saved_output_audit_completed", "scientific_claim_authorized"])
def test_rendering_cannot_promote_descriptive_evidence(field):
    data = deepcopy(projection())
    data[field] = True
    with pytest.raises(ValueError):
        renderer.tex(data, "zh")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, "477"])
def test_invalid_error_is_refused_not_zero_filled(value):
    data = deepcopy(projection())
    data["profiles"][1]["weighted_es_m"] = value
    with pytest.raises(ValueError):
        renderer.tex(data, "en")


def test_swapped_reference_profiles_are_refused():
    data = deepcopy(projection())
    data["profiles"].reverse()
    with pytest.raises(ValueError):
        renderer.tex(data, "en")
