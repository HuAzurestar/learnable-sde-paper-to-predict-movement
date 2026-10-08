"""Complete saved region arithmetic/display contracts, not final qualification."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess

import pytest

from scripts.pirc17_document_blocks import assert_preserved_blocks

from scripts.plot_pirc17_method_regions import (SOURCE_SHA, GROUPS, validate,
                                               reconcile, table_tex, figure_tex,
                                               coverage_envelope, coverage_envelope_tex)

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"
BASE = "66ff1f45ecfb6009f6a7e2587304733c00584711"


def source():
    raw = (PAPER/"all-method-region-description-v1.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    return json.loads(raw)


def test_complete_original_means_and_three_model_profiles_reconcile():
    data = source()
    rows = reconcile(data,json.loads((PAPER/"preliminary-method-statistics-v1.json").read_text()),
                          json.loads((PAPER/"calibration-description-v1.json").read_text()))
    assert len(rows) == 28
    assert [p["configuration"] for p in rows] == [key for _,_,keys in GROUPS for key in keys]
    assert sum(len(h["levels"]) for p in rows for h in p["horizons"]) == 448
    values = [p["horizons"][3]["levels"][2] for p in rows]
    assert all(v["empirical_coverage"] < .9 for v in values)
    assert f"{min(v['mean_disk_area_km2'] for v in values):.3f}" == "1.247"
    assert f"{max(v['mean_disk_area_km2'] for v in values):.3f}" == "12.609"


@pytest.mark.parametrize("mutation", ["missing","duplicate","extra","partial","seeds",
    "horizon","level","nan","bool","negative","coverage","jensen","nested","audit","new"])
def test_changed_or_incomplete_saved_scope_fails_whole_display(mutation):
    data = deepcopy(source())
    rows = data["profiles"]
    level = rows[0]["horizons"][0]["levels"][2]
    if mutation == "missing": rows.pop()
    elif mutation == "duplicate": rows[-1] = deepcopy(rows[0])
    elif mutation == "extra": rows[-1]["configuration"] = "terrain/base"
    elif mutation == "partial": rows[0]["forecast_rows"] = 229
    elif mutation == "seeds": data["forecast_seed_ids"].reverse()
    elif mutation == "horizon": rows[0]["horizons"].pop()
    elif mutation == "level": rows[0]["horizons"][0]["levels"].pop()
    elif mutation == "nan": level["mean_disk_area_km2"] = float("nan")
    elif mutation == "bool": level["empirical_coverage"] = True
    elif mutation == "negative": level["mean_disk_radius_m"] = -1
    elif mutation == "coverage": level["empirical_coverage"] = 1.1
    elif mutation == "jensen": level["mean_disk_area_km2"] = .001
    elif mutation == "nested": level["empirical_coverage"] = .1
    elif mutation == "audit": data["scope"]["independent_saved_output_audit_completed"] = True
    elif mutation == "new": data["scope"]["new_forecasts"] = 1
    with pytest.raises(ValueError): validate(data)


def test_reconciliation_rejects_changed_stage_and_old_profiles():
    data=source()
    stage=json.loads((PAPER/"preliminary-method-statistics-v1.json").read_text())
    old=json.loads((PAPER/"calibration-description-v1.json").read_text())
    stage["configs"][0]["coverage_90_by_time"][0] += .001
    with pytest.raises(ValueError): reconcile(data,stage,old)
    stage=json.loads((PAPER/"preliminary-method-statistics-v1.json").read_text())
    old["profiles"][0]["horizons"][0]["levels"][0]["mean_disk_area_km2"] += .001
    with pytest.raises(ValueError): reconcile(data,stage,old)


@pytest.mark.parametrize("language",["en","zh"])
def test_exact_generated_table_and_figure_in_right_manuscript_sections(language):
    assert (PAPER/language/"method-region-tables.tex").read_text(encoding="utf-8") == table_tex(source(),language)
    assert (PAPER/language/"method-region-overview.tex").read_text(encoding="utf-8") == figure_tex(language)
    table = table_tex(source(),language)
    assert len(re.findall(r" & \d+ / \d+\.\d+ / \d+\.\d+",table)) == 112
    assert table.count(r"}}\\*") == 6
    tex=(PAPER/language/"main.tex").read_text(encoding="utf-8")
    assert tex.index(r"\input{method-region-overview.tex}") < tex.index(r"\appendix")
    assert tex.index(r"\input{method-region-tables.tex}") > tex.index(r"\appendix")
    for value in ("6440","1.247","12.609","79.13","2.78","1340.94","1326.09","0.400","0.294"):
        assert value in tex
    assert ("not only the prediction integration step" if language=="en" else "不只是预测积分步长") in tex
    assert ("not a universal size--quality rule" if language=="en" else "不是普遍的大小—质量规则") in tex


@pytest.mark.parametrize("language",["en","zh"])
def test_all_previous_literal_scientific_blocks_remain_exact(language):
    before=subprocess.check_output(["git","show",f"{BASE}:paper/pirc17/{language}/main.tex"],cwd=ROOT).decode("utf-8").replace("\r\n","\n")
    after=(PAPER/language/"main.tex").read_text(encoding="utf-8")
    for kind in ("table","longtable","figure","equation"):
        pattern=r"\\begin\{"+kind+r"\}.*?\\end\{"+kind+r"\}"
        assert_preserved_blocks(re.findall(pattern,before,re.S),re.findall(pattern,after,re.S),kind)


def test_saved_projection_manifest_and_ledger_are_exact_and_not_acceptance():
    manifest=json.loads((PAPER/"figures/method-region-manifest-v1.json").read_text())
    assert manifest["source_sha256"]==SOURCE_SHA
    renderer=ROOT/"scripts/plot_pirc17_method_regions.py"
    assert manifest["renderer_sha256"]==hashlib.sha256(renderer.read_bytes()).hexdigest()
    paths={**{f"method-region-overview.{ext}":PAPER/"figures"/f"method-region-overview.{ext}" for ext in ("pdf","png")},
           **{f"{lang}-method-region-{kind}.tex":PAPER/lang/f"method-region-{kind}.tex" for lang in ("en","zh") for kind in ("tables","overview")}}
    assert set(paths)==set(manifest["files_sha256"])
    for name,path in paths.items():
        assert manifest["files_sha256"][name]==hashlib.sha256(path.read_bytes()).hexdigest()
    ledger=json.loads((PAPER/"claim-ledger.json").read_text(encoding="utf-8"))
    entry=ledger["complete_method_region_description_revision"]
    assert entry["source_base_commit"]==BASE
    assert entry["projection_sha256"]==SOURCE_SHA
    assert entry["renderer_sha256"]==manifest["renderer_sha256"]
    assert entry["review_items"]==["P1-19","P1-20"]
    assert entry["block_resolved_diagnostics_remain_three_model_scope"]
    assert entry["all_original_main_literal_scientific_blocks_preserved"]
    for field in ("all_twenty_eight_prediction_array_clocks_audited","conditional_calibration_established",
                  "independent_saved_output_audit_completed","original_final_sixteen_figure_inventory_replaced",
                  "final_qualification_or_review_complete"):
        assert entry[field] is False
    assert entry["new_fits_forecasts_scores_resampling_or_map_queries"]==0
    assert ledger["final_empirical_results_integrated"] is False
    assert ledger["human_accepted"] is False


def test_complete_all_level_envelope_uses_each_identity_without_model_average():
    data = source()
    result = coverage_envelope(data)
    assert len(result) == 16
    for i, horizon in enumerate((60, 300, 900, 1800)):
        for j, nominal in enumerate((.5, .8, .9, .95)):
            row = result[4*i+j]
            values = [p["horizons"][i]["levels"][j] for p in data["profiles"]]
            assert row["nominal_horizon_seconds"] == horizon
            assert row["nominal_level"] == nominal
            assert row["configuration_count"] == 28
            assert row["coverage_min"] == min(v["empirical_coverage"] for v in values)
            assert row["coverage_max"] == max(v["empirical_coverage"] for v in values)
            assert row["mean_area_min_km2"] == min(v["mean_disk_area_km2"] for v in values)
            assert row["mean_area_max_km2"] == max(v["mean_disk_area_km2"] for v in values)
            assert row["below_nominal"] + row["equal_nominal"] + row["above_nominal"] == 28
    assert [(r["below_nominal"],r["equal_nominal"],r["above_nominal"]) for r in result] == [
        (24,0,4),(2,0,26),(1,0,27),(1,0,27),
        (27,0,1),(26,0,2),(26,0,2),(26,0,2),
        (28,0,0),(28,0,0),(27,0,1),(27,0,1),
        (27,1,0),(28,0,0),(28,0,0),(28,0,0)]
    assert f"{100*result[-1]['coverage_min']:.2f}" == "26.52"
    assert f"{100*result[-1]['coverage_max']:.2f}" == "87.39"


@pytest.mark.parametrize("offset,equal,above",[(0,1,0),(5e-13,1,0),(5e-11,0,1)])
def test_envelope_equality_only_guards_float_roundoff_not_scientific_margin(offset,equal,above):
    data=deepcopy(source())
    row=next(p for p in data["profiles"] if p["configuration"]=="arm-06/dt600")
    row["horizons"][3]["levels"][0]["empirical_coverage"] += offset
    result=coverage_envelope(data)[12]
    assert result["equal_nominal"] == equal
    assert result["above_nominal"] == above
    assert result["below_nominal"] == 27


@pytest.mark.parametrize("language",["en","zh"])
def test_all_probability_table_does_not_replace_original_90_percent_table(language):
    table=table_tex(source(),language)
    base=subprocess.check_output(["git","show",f"f11bcf39df113eb5b9d7a1d459da50622bf4fe38:paper/pirc17/{language}/method-region-tables.tex"],cwd=ROOT).decode("utf-8").replace("\r\n","\n")
    assert table == base + coverage_envelope_tex(source(),language)
    assert r"\label{tab:all-level-coverage}" in table
    assert coverage_envelope_tex(source(),language).startswith(r"\Needspace{.65\textheight}")
    assert len(re.findall(r"^\d+ & \d+ & \d+\.\d+--",table,re.M)) == 16
    tex=(PAPER/language/"main.tex").read_text(encoding="utf-8")
    assert r"Table~\ref{tab:all-level-coverage}" in tex if language=="en" else r"表~\ref{tab:all-level-coverage}" in tex
    for value in ("26.52","87.39","24","27"):
        assert value in tex
    assert ("not independent algorithm replications" if language=="en" else "不是独立算法重复数") in re.sub(r"\s+", " ", tex)
    assert ("not confidence intervals" if language=="en" else "不是置信区间") in table


def test_envelope_manifest_matches_saved_means_and_no_new_acceptance():
    manifest=json.loads((PAPER/"figures/method-region-manifest-v1.json").read_text())
    assert manifest["all_level_coverage_summary"] == coverage_envelope(source())
    ledger=json.loads((PAPER/"claim-ledger.json").read_text(encoding="utf-8"))
    entry=ledger["all_level_coverage_reading_revision"]
    assert entry["table_label"] == "tab:all-level-coverage"
    assert entry["configuration_count"] == 28
    assert entry["descriptive_table_cells"] == 16
    assert entry["configuration_counts_are_independent_models"] is False
    assert entry["ranges_are_confidence_intervals"] is False
    assert entry["new_fits_forecasts_scores_resampling_or_map_queries"] == 0
    assert entry["calibration_certified"] is False
    assert entry["final_paper_or_review_complete"] is False
