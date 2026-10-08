"""Saved-number/table/figure bindings only, not scientific qualification."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.plot_pirc17_calibration import SOURCE, SOURCE_SHA, validate


ROOT = Path(__file__).resolve().parents[1]


def data():
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def test_projection_and_figure_bindings():
    validate(data())
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
    ledger = json.loads((ROOT / "paper/pirc17/claim-ledger.json").read_text(encoding="utf-8"))
    assert ledger["saved_calibration_and_area_description"]["projection_sha256"] == SOURCE_SHA
    manifest = json.loads((ROOT / "paper/pirc17/figures/calibration-figure-manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_sha256"] == SOURCE_SHA
    assert not manifest["final_audit_performed"]
    for stem, hashes in manifest["figures"].items():
        for extension, expected in hashes.items():
            path = ROOT / "paper/pirc17/figures" / (stem + "." + extension)
            assert hashlib.sha256(path.read_bytes()).hexdigest() == expected


@pytest.mark.parametrize("language", ["en", "zh"])
def test_bilingual_full_table_exact_rounding(language):
    tex = (ROOT / "paper/pirc17" / language / "main.tex").read_text(encoding="utf-8")
    for time in data()["profiles"][0]["horizons"]:
        cells = [str(time["nominal_horizon_seconds"] // 60)]
        cells += [f"{100*v['empirical_coverage']:.2f} / {v['mean_disk_area_km2']:.3f}" for v in time["levels"]]
        assert " & ".join(cells) in tex


@pytest.mark.parametrize("language", ["en", "zh"])
def test_bilingual_same_target_model_table(language):
    tex = (ROOT / "paper/pirc17" / language / "main.tex").read_text(encoding="utf-8")
    for name, model in zip(("Full", "GMM kernel", "dt300"), data()["profiles"]):
        v = model["horizons"][-1]["levels"][2]
        assert (f"{name} & {100*v['empirical_coverage']:.2f} & "
                f"{v['mean_disk_area_km2']:.3f} & {v['mean_disk_radius_m']:.1f}") in tex
    assert "fig:calibration-area" in tex


@pytest.mark.parametrize("kind", ["partial", "qualified", "new_prediction", "wrong_level", "bad_area"])
def test_no_partial_or_new_science_in_plot(kind):
    value = copy.deepcopy(data())
    if kind == "partial": value["profiles"][0]["forecast_rows"] = 229
    if kind == "qualified": value["scope"]["independent_output_audit"] = True
    if kind == "new_prediction": value["scope"]["new_predictions"] = 1
    if kind == "wrong_level": value["profiles"][0]["horizons"][0]["levels"][0]["nominal_level"] = .4
    if kind == "bad_area": value["profiles"][0]["horizons"][0]["levels"][0]["mean_disk_area_km2"] = float("nan")
    with pytest.raises(ValueError): validate(value)
