# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Saved per-time means and display completeness, not new empirical inference."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

import pytest

from scripts.plot_pirc17_method_horizons import SOURCE_SHA, GROUPS, project, table_tex, figure_tex

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT/"paper/pirc17"


def source():
    raw = (PAPER/"preliminary-method-statistics-v1.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    return json.loads(raw)


def test_all_original_values_and_28_identities_are_exact():
    saved = source()
    result = project(saved)
    assert len(result["configs"]) == 28
    assert len({r["configuration"] for r in result["configs"]}) == 28
    index = {r["configuration"]:r for r in saved["configs"]}
    for row in result["configs"]:
        original = index[row["configuration"]]
        assert row["es_by_time_m"] == original["es_by_time_m"]
        assert row["coverage_90_by_time"] == original["coverage_90_by_time"]
        assert row["saved_score_rows"] == 230
    assert result["thirty_minute_es_range_m"] == [941.8934482293058,1197.6152619441532]
    assert result["thirty_minute_coverage_range"] == [0.21739130434782608,0.7913043478260869]
    assert result["all_thirty_minute_coverages_below_nominal"]


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "extra", "failed", "secondary",
                                    "seeds", "nan", "bool", "negative", "coverage", "times", "final"])
def test_incomplete_or_changed_metrics_fail_whole_display(mutation):
    saved = deepcopy(source())
    rows = saved["configs"]
    if mutation == "missing": rows.pop()
    elif mutation == "duplicate": rows[-1] = deepcopy(rows[0])
    elif mutation == "extra": rows[-1]["configuration"] = "terrain/base"
    elif mutation == "failed": rows[0]["counts"] = {"success":229,"failed":1}
    elif mutation == "secondary": rows[0]["origin_mode"] = "known_velocity"
    elif mutation == "seeds": saved["forecast_seeds"].reverse()
    elif mutation == "nan": rows[0]["es_by_time_m"][0] = float("nan")
    elif mutation == "bool": rows[0]["coverage_90_by_time"][0] = True
    elif mutation == "negative": rows[0]["es_by_time_m"][0] = -1
    elif mutation == "coverage": rows[0]["coverage_90_by_time"][0] = 1.01
    elif mutation == "times": rows[0]["es_by_time_m"].pop()
    elif mutation == "final": saved["scientific_claim_authorized"] = True
    with pytest.raises(ValueError): project(saved)


def test_group_order_not_performance_sorted_or_control_pooled():
    result = project(source())
    assert [r["configuration"] for r in result["configs"]] == [c for _,_,rows in GROUPS for c in rows]
    assert len(result["groups"]) == 6  # Five families plus one extra role, not a sixth family.
    assert result["groups"][-1]["configurations"] == ["arm-16/full"]
    rows = {r["configuration"]:r for r in result["configs"]}
    for metric in ("es_by_time_m","coverage_90_by_time"):
        assert rows["arm-19/em"][metric] == rows["arm-19/euler"][metric]
        assert rows["arm-06/dt60"][metric] == rows["arm-01/full"][metric]
        assert rows["arm-10/d2_mc"][metric] == rows["arm-07/full"][metric]
    assert rows["arm-07/full"]["es_by_time_m"] != rows["arm-01/full"]["es_by_time_m"]


def test_projection_does_not_authorize_new_science_or_all_clock_audit():
    result = project(source())
    for field in ("new_fits","new_forecasts","new_scores","new_resampling","new_per_horizon_inference"):
        assert result[field] == 0
    for field in ("forecast_arrays_opened","independent_saved_output_audit_completed",
                  "scientific_claim_authorized","original_final_sixteen_figure_inventory_replaced",
                  "ranges_are_confidence_intervals","configs_are_independent_algorithms"):
        assert result[field] is False
    assert "three configurations, not all 28" in result["target_scope"]
    assert "not 230 independent" in result["averaging_scope"]
    assert "not higher-is-always-better" in result["coverage_units"]


@pytest.mark.parametrize("language",["en","zh"])
def test_full_table_and_overview_are_exact_generated_includes(language):
    description = project(source())
    assert (PAPER/language/"method-horizon-tables.tex").read_text(encoding="utf-8") == table_tex(description,language)
    assert (PAPER/language/"method-horizon-overview.tex").read_text(encoding="utf-8") == figure_tex(language)
    tex = (PAPER/language/"historical-main-v1.tex").read_text(encoding="utf-8")
    assert tex.index(r"\input{method-horizon-overview.tex}") < tex.index(r"\appendix")
    assert tex.index(r"\input{method-horizon-tables.tex}") > tex.index(r"\appendix")
    assert r"\usepackage{needspace}" in tex
    assert r"\Needspace{.70\textheight}"+"\n"+r"\input{method-horizon-tables.tex}" in tex
    fulltable = table_tex(description,language)
    assert len(re.findall(r" & \d+\.\d+ /",fulltable)) == 112
    assert "Full16" in fulltable and "Full18" in fulltable and "Full20" in fulltable
    assert fulltable.count(r"}}\\*") == 6
    assert r"\renewcommand{\arraystretch}{.90}" in fulltable
    assert "941.89" in tex and "1197.62" in tex and "79.13" in tex


def test_projection_manifest_and_scientific_scope_remain_bound():
    projection = PAPER/"method-horizon-description-v1.json"
    assert json.loads(projection.read_text(encoding="utf-8")) == project(source())
    manifest = json.loads((PAPER/"figures/method-horizon-manifest-v1.json").read_text())
    assert manifest["source_sha256"] == SOURCE_SHA and manifest["configs"] == 28
    assert manifest["renderer_sha256"] == hashlib.sha256((ROOT/"scripts/plot_pirc17_method_horizons.py").read_bytes()).hexdigest()
    mapping = {"method-horizon-description-v1.json":projection,
               **{f"{language}-method-horizon-{kind}.tex":PAPER/language/f"method-horizon-{kind}.tex"
                  for language in ["en","zh"] for kind in ["tables","overview"]},
               **{f"method-horizon-overview.{ext}":PAPER/"figures"/f"method-horizon-overview.{ext}" for ext in ["pdf","png"]}}
    assert set(manifest["files_sha256"]) == set(mapping)
    for name,path in mapping.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest["files_sha256"][name]
    ledger = json.loads((PAPER/"claim-ledger.json").read_text(encoding="utf-8"))
    record = ledger["original_method_horizon_description"]
    assert record["renderer_sha256"] == manifest["renderer_sha256"]
    assert record["projection_sha256"] == hashlib.sha256(projection.read_bytes()).hexdigest()
    assert not record["final_qualification_or_review_complete"]
    assert not ledger["final_empirical_results_integrated"] and not ledger["human_accepted"]
