# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Saved arithmetic and public display checks, not calibration qualification."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.plot_pirc17_calibration_blocks import (BASE, BASE_SHA, ROOT, SOURCE,
    SOURCE_SHA, aggregate_view, load_snapshot, table_rows, validate)


def test_whole_saved_scope_and_unchanged_original_aggregates():
    data = load_snapshot()
    assert aggregate_view(data) == json.loads(BASE.read_text(encoding="utf-8"))
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_SHA
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
    assert sum(len(v["blocks"]) for p in data["profiles"] for t in p["horizons"]
               for v in t["levels"]) == 3 * 4 * 4 * 46
    assert data["block_distribution_scope"]["coverage_resolution"] == .2


@pytest.mark.parametrize("language", ["en", "zh"])
def test_all_twelve_complete_table_rows_and_seed_count_explanation(language):
    text = (ROOT / "paper/pirc17" / language / "historical-main-v1.tex").read_text(encoding="utf-8")
    assert all(row + r"\\" in text for row in table_rows(load_snapshot()))
    for label in ("sec:block-calibration", "eq:block-calibration-summary",
                  "tab:block-calibration", "fig:block-calibration"):
        assert text.count(r"\label{" + label + "}") == 1
    assert ("not five" if language == "en" else "并非五个独立观测") in text
    assert ("not confidence intervals" if language == "en" else "不是置信区间") in text
    assert ("selected after seeing outcomes" if language == "en" else "在看过结果后选择") in text
    assert "B13" in text
    for number in ("3.489", "3.204", "8.260", "11.551"):
        assert number in text


def test_coordinate_free_example_and_zero_coverage_counts_are_actual_saved_values():
    data = load_snapshot()
    groups = [p["horizons"][-1]["levels"][2] for p in data["profiles"]]
    full, gmm, dt = groups
    assert full["blocks_by_covered_seed_count"] == [23, 1, 1, 0, 1, 20]
    assert dt["blocks_by_covered_seed_count"] == [16, 0, 0, 1, 0, 29]
    assert full["coverage_distribution"]["median"] == .1
    candidates = [i for i in range(46) if full["blocks"][i]["covered_seed_count"] == 0
                  and dt["blocks"][i]["covered_seed_count"] == 5]
    assert candidates[0] == 12
    assert [p["blocks"][12]["covered_seed_count"] for p in groups] == [0, 0, 5]
    assert [f"{p['blocks'][12]['mean_disk_area_km2']:.3f}" for p in groups] == ["3.489", "3.204", "8.260"]


def test_figure_and_reader_provenance_do_not_grant_empirical_or_route_permission():
    paper = ROOT / "paper/pirc17"
    manifest_path = paper / "figures/calibration-block-figure-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    ledger = json.loads((paper / "claim-ledger.json").read_text(encoding="utf-8"))["saved_calibration_block_description"]
    assert ledger["projection_sha256"] == manifest["source_sha256"] == SOURCE_SHA
    assert ledger["figure_manifest_sha256"] == hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    assert ledger["renderer_sha256"] == manifest["renderer_sha256"] == hashlib.sha256(
        (ROOT / "scripts/plot_pirc17_calibration_blocks.py").read_bytes()).hexdigest()
    assert ledger["reader_sha256"] == "3f20e0f73ed7d680e88652ac8446cfb739f2b38293c6aa8842074900d2ca7a57"
    assert manifest["panel_count"] == 12 and manifest["points_per_panel"] == 46
    assert manifest["shown_probability_level"] == .9 and manifest["area_axis_scale"] == "log"
    for stem, values in manifest["figures"].items():
        for extension, expected in values.items():
            assert hashlib.sha256((paper / "figures" / (stem + "." + extension)).read_bytes()).hexdigest() == expected
    for index, limits in enumerate(manifest["shared_area_limits_by_nominal_horizon"]):
        values = [b["mean_disk_area_km2"] for p in load_snapshot()["profiles"]
                  for b in p["horizons"][index]["levels"][2]["blocks"]]
        assert limits[0] < min(values) <= max(values) < limits[1]
    assert manifest["new_fits_predictions_scores_or_inference"] == 0
    assert not manifest["final_audit_performed"]
    assert not manifest["public_route_case_permission_verified"]
    assert not manifest["original_final_sixteen_figure_inventory_replaced"]


@pytest.mark.parametrize("kind", ["missing_block", "duplicate", "wrong_coverage", "wrong_histogram",
    "bad_area", "bad_summary", "private_field", "wrong_level", "qualified", "new_prediction", "wider_claim"])
def test_incomplete_invalid_or_claim_expanding_display_is_rejected(kind):
    data = copy.deepcopy(load_snapshot())
    value = data["profiles"][0]["horizons"][0]["levels"][2]
    if kind == "missing_block": value["blocks"].pop()
    if kind == "duplicate": value["blocks"][1] = copy.deepcopy(value["blocks"][0])
    if kind == "wrong_coverage": value["blocks"][0]["seed_coverage_fraction"] = .123
    if kind == "wrong_histogram": value["blocks_by_covered_seed_count"][0] += 1
    if kind == "bad_area": value["blocks"][0]["mean_disk_area_km2"] = float("nan")
    if kind == "bad_summary": value["area_km2_distribution"]["median"] += .001
    if kind == "private_field": value["blocks"][0]["target_coordinate"] = [0, 0]
    if kind == "wrong_level": value["nominal_level"] = .7
    if kind == "qualified": data["scope"]["independent_output_audit"] = True
    if kind == "new_prediction": data["scope"]["new_predictions"] = 1
    if kind == "wider_claim": data["block_distribution_scope"]["all_twenty_eight_models_described"] = True
    with pytest.raises(ValueError):
        validate(data)
