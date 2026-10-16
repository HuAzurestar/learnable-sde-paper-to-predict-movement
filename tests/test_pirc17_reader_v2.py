"""Regression guards for the review's concrete manuscript/estimator defects."""
import ast
import hashlib
from scripts.pirc17_historical_tex import historical_tex
from scripts.pirc17_paper_paths import paper_path
import json
from pathlib import Path
import re

import numpy as np
import pytest
from scripts.pirc17_figure_provenance import original_figure

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"


def read(path):
    return json.loads(paper_path(PAPER / path).read_text(encoding="utf-8"))


def test_bound_scoring_operator_discriminates_u_from_empirical_distribution():
    binding = read("reader-v2-score-binding.json")
    previous = read("public-paired-replay-v1/receipt.json")
    assert binding["source_file_sha256"]["experiments/pirc17/metrics.py"] == previous["source_file_sha256"]["experiments/pirc17/metrics.py"]
    # Execute only the two verbatim hash-bound pure definitions on a synthetic
    # analytic fixture. Research predictions/scores are never opened.
    source = binding["metric_source_projection"]
    parsed = ast.parse(source)
    assert [n.name for n in parsed.body] == ["_samples", "energy_score"]
    namespace = {"np": np}
    exec(compile(parsed, "bound-metric-projection", "exec"), namespace)
    samples = np.array([[0., 0.], [2., 0.]])
    assert namespace["energy_score"](samples, [0., 0.]) == 0.
    empirical_distribution_score = 1. - 4./(2*2**2)
    assert empirical_distribution_score == .5
    assert not binding["original_arrays_rescored"] and binding["new_research_scores"] == 0


@pytest.mark.parametrize("lang", ["en", "zh"])
def test_body_equation_matches_supplement_and_has_point_mass_exception(lang):
    body = (PAPER / lang / "main.tex").read_text(encoding="utf-8")
    eq = body.split(r"\label{eq:finite-es}", 1)[1].split(r"\end{equation}", 1)[0]
    assert r"\frac1{2N(N-1)}\sum_{i\ne j}" in eq
    assert "2N^2" not in eq
    assert ("deterministic CV" if lang == "en" else "确定性恒速参考（CV）") in body
    supplement = (PAPER / lang / "revision46-supplement-retained.tex").read_text(encoding="utf-8")
    assert "N(N-1)" in supplement
    assert all(r"\input{reader-v3-"+name+".tex}" in body for name in ("tradeoff", "calibration"))
    # Geometry/design remain in the supplement after reader-v3 convergence.
    supplement_entry = (PAPER / lang / "supplement.tex").read_text(encoding="utf-8")
    figures = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", supplement_entry)
    assert {"geometry.pdf", "design.pdf"} <= {original_figure(PAPER, path).name for path in figures}


def test_corrected_groups_and_plot_values_preserve_canonical_evidence():
    manifest = read("figures/reader-v2/manifest.json")
    for path, sha in manifest["source_sha256"].items():
        assert hashlib.sha256((PAPER / path).read_bytes()).hexdigest() == sha
    figures = {f["name"]: f for f in manifest["figures"]}
    groups = figures["geometry"]["displayed"]["cover_classes"]
    assert groups["vegetation"] == [10, 20, 30, 40, 95, 100]
    assert groups["water/wetland"] == [80, 90] and "open" not in groups
    full, selected = [figures[n]["displayed"] for n in ("full-overview", "selected-overview")]
    assert selected["all_cell_text_black"] and selected["coverage_colour_bounds_pp"] == [-90, 90]
    for i, name in enumerate(selected["configurations"]):
        j = full["configurations"].index(name)
        for key in ("ES_m", "area_km2", "coverage_deviation_pp"):
            assert selected[key][i] == full[key][j]
    stats = read("preliminary-method-statistics-v1.json")
    original = {r["candidate"]: r for r in stats["comparisons"]}
    assert len(figures["tradeoff"]["displayed"]) == 21
    for row in figures["tradeoff"]["displayed"]:
        assert row["control"] == original[row["candidate"]]["control"]
        assert row["delta_ES_m"] == original[row["candidate"]]["delta_estimate_m"]
    for f in manifest["figures"]:
        for path, sha in f["files_sha256"].items():
            assert hashlib.sha256((PAPER / "figures/reader-v2" / path).read_bytes()).hexdigest() == sha


@pytest.mark.parametrize("lang", ["en", "zh"])
def test_dated_status_updates_keep_historical_table_values_and_bindings(lang):
    source = (PAPER / lang / "revision46-supplement-retained.tex").read_text(encoding="utf-8")
    for stem in ("inertial-primary-comparison", "point-error-horizons"):
        old = historical_tex(PAPER / lang / (stem+".tex")).read_text(encoding="utf-8")
        new = (PAPER / lang / ("reader-v2-"+stem+".tex")).read_text(encoding="utf-8")
        for environment in ("table", "equation"):
            pattern = r"\\begin\{"+environment+r"\}.*?\\end\{"+environment+r"\}"
            assert re.findall(pattern, old, re.S) == re.findall(pattern, new, re.S)
        assert r"\input{reader-v2-"+stem+".tex}" in source
        assert ("human acceptance" if lang == "en" else "人工验收") in new
    assert "10" in (PAPER / lang / "reader-v2-inertial-primary-comparison.tex").read_text(encoding="utf-8")
