"""Current-revision scientific and source invariants; no human acceptance claim."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"


def read(name):
    return json.loads((PAPER / name).read_text(encoding="utf-8"))


def test_all46_and_original42_are_preserved_without_fake_acceptance():
    value = read("revision46-response-v1.json")
    expected = {f"{p}{n:02d}" for p,t in (("G",13),("O",8),("R",17),("X",8)) for n in range(1,t+1)}
    assert {r["id"] for r in value["tasks"]} == expected
    assert len(value["tasks"]) == 46
    assert len(value["original42_mapping"]) == 42
    assert all(set(ids) <= expected and ids for ids in value["original42_mapping"].values())
    assert value["human_accepted"] is False and value["original42_accepted"] == 0
    assert value["new_experiments"] == 0


@pytest.mark.parametrize("language", ["en", "zh"])
def test_historical_sources_are_exact_git_bytes_and_every_unit_is_accounted(language):
    historical = (PAPER / language / "historical-main-v1.tex").read_bytes()
    original = subprocess.check_output(["git", "show", "8cbcb114:paper/pirc17/"+language+"/main.tex"], cwd=ROOT)
    assert historical == original
    migration = read("revision46-source-migration.json")["languages"][language]
    assert migration["frozen_source_sha256"] == hashlib.sha256(original).hexdigest()
    assert migration["all_units_assigned"] and len(migration["units"]) == 61
    assert all(u["destination"] in {"historical-source", "audit-notes", "supplement"} for u in migration["units"])


def test_figure_sources_are_original_canonical_bytes_and_no_experiment():
    manifest = read("figures/revision46-v1/revision46-figure-manifest.json")
    assert manifest["renderer_sha256"] == hashlib.sha256((ROOT / "scripts/plot_pirc17_revision46.py").read_bytes()).hexdigest()
    assert manifest["new_fits_forecasts_particle_scores_resampling_or_map_queries"] == 0
    assert {r["task"] for r in manifest["figures"]} == {f"G{n:02d}" for n in range(1,14) if n != 12}
    for name, sha in manifest["source_sha256"].items():
        data = (PAPER / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == sha
        original = subprocess.check_output(["git", "show", "8cbcb114:paper/pirc17/"+name], cwd=ROOT)
        assert data == original
    for record in manifest["figures"]:
        for file in record["files"].values():
            assert hashlib.sha256((PAPER / "figures/revision46-v1" / file["name"]).read_bytes()).hexdigest() == file["sha256"]


def test_presentation_corrections_are_versioned_and_used_by_current_supplements():
    manifest = read("figures/revision46-corrections-v1/manifest.json")
    assert manifest["new_fits_forecasts_scores_or_resampling"] == 0
    assert manifest["old_figures_or_historical_hashes_overwritten"] is False
    assert len(manifest["figures"]) == 3
    for row in manifest["figures"]:
        assert hashlib.sha256((ROOT / "scripts" / row["renderer"]).read_bytes()).hexdigest() == row["renderer_sha256"]
        for name, sha in row["files_sha256"].items():
            assert hashlib.sha256((PAPER / "figures/revision46-corrections-v1" / name).read_bytes()).hexdigest() == sha
    for language in ("en", "zh"):
        retained = (PAPER / language / "revision46-supplement-retained.tex").read_text(encoding="utf-8")
        assert "revision46-corrections-v1/preliminary-full-horizons.pdf" in retained
        for name in ("method-horizon-overview", "method-region-overview"):
            assert r"\input{revision46-"+name+".tex}" in retained
            child = (PAPER / language / ("revision46-"+name+".tex")).read_text(encoding="utf-8")
            assert "revision46-corrections-v1/"+name+".pdf" in child


def test_every_pre_revision_scientific_json_is_exact_canonical_git_bytes():
    names = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "8cbcb114", "paper/pirc17"], cwd=ROOT, text=True).splitlines()
    count = 0
    for name in names:
        if not name.endswith(".json"):
            continue
        original = subprocess.check_output(["git", "show", "8cbcb114:"+name], cwd=ROOT)
        assert (ROOT / name).read_bytes() == original, name
        count += 1
    assert count == 66


def test_historical_test_migration_does_not_change_a_scientific_assertion():
    import ast
    value = read("revision46-test-migration.json")
    assert value["scientific_assertions_changed"] == 0 and not value["skip_exclude_or_deselect_added"]
    for row in value["tests"]:
        path = ROOT / row["path"]
        original = subprocess.check_output(["git", "show", "8cbcb114:"+row["path"]], cwd=ROOT)
        assert hashlib.sha256(original).hexdigest() == row["original_test_sha256"]
        asserts = lambda data: [ast.dump(n, include_attributes=False) for n in ast.walk(ast.parse(data)) if isinstance(n, ast.Assert)]
        assert asserts(original.decode("utf-8")) == asserts(path.read_text(encoding="utf-8"))
        assert row["assertions_changed"] == 0


@pytest.mark.parametrize("language", ["en", "zh"])
def test_current_six_document_structure_and_bounded_claims(language):
    main = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    for label in ("eq:ordinary-full", "eq:terrain-summary", "eq:constant-penalty", "eq:finite-es", "tab:inputs", "tab:actual-changes", "tab:point-errors"):
        assert main.count(r"\label{"+label+"}") == 1
    numbers = (PAPER / "revision46-numbers.tex").read_text(encoding="utf-8")
    for token in ("512", "110/109/109", "26/25/25", "27/27/27", "404", "81", "0.0404", "41.100259", "46.52", "37.83", "35.22", "33.04", "95.65", "52.17", "21.74", "79.13", "1379/1380", "1148/1150", "F01", "F02", "F03", "F04", "F05", "165", "150", "15", "90"):
        assert token in main, (language, token)
    assert all(chr(92)+macro in main for macro in ("FullES", "InertialES", "InertialDelta", "PointRowFull", "PointRowGMM", "PointRowdtThreeHundred", "PointRowInertial"))
    assert "477.85" in numbers and "824.73" in numbers and "-346.87" in numbers
    assert main.index("fig:inertial") < main.index("fig:practical-effects")
    assert "bridleway" in main and "footway" in main and "path" in main and "steps" in main
    assert "N(N-1)" in main and r"2N^2" in main
    assert r"\appendix" not in main
    assert r"\input{revision46-supplement-retained.tex}" in (PAPER / language / "supplement.tex").read_text(encoding="utf-8")
    assert r"\input{revision46-audit-notes-retained.tex}" in (PAPER / language / "audit-notes.tex").read_text(encoding="utf-8")
    assert ("not a fresh blinded holdout" if language == "en" else "不是全新盲测留出集") in main
    assert ("not a positive or null terrain" if language == "en" else "不是地形正效应或零效应") in main


def test_current_bilingual_bibliography_and_all23_citation_roles():
    entries = []
    for language in ("en", "zh"):
        bib = (PAPER / language / "revision46-bibliography.tex").read_text(encoding="utf-8")
        labels = re.findall(r"\\bibitem\{([^}]+)\}", bib)
        main = (PAPER / language / "main.tex").read_text(encoding="utf-8")
        cited = {key for group in re.findall(r"\\cite\{([^}]+)\}", main) for key in group.split(",")}
        assert len(labels) == len(set(labels)) == 23 and cited == set(labels)
        entries.append(" ".join(bib.split()))
    assert entries[0] == entries[1]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_five_follow_up_designs_are_not_silently_executed(language):
    source = (PAPER / language / "supplement.tex").read_text(encoding="utf-8")
    assert all(source.count(f"N{n:02d}:") == 1 if language == "en" else source.count(f"N{n:02d}：") == 1
               for n in range(1,6))
    assert ("None is executed" if language == "en" else "未执行这些实验") in source
    assert "$z=(x_e,x_n,v_e,v_n)$" in source
    assert ("training data only" if language == "en" else "仅用训练数据") in source


def test_paired_effects_and_seed_values_retain_every_named_control():
    from scripts.plot_pirc17_revision46 import forest, seed_blocks, tradeoff
    from matplotlib import pyplot as plt
    stats = read("preliminary-method-statistics-v1.json")
    assert len(stats["comparisons"]) == 21
    assert all(not (r["simultaneous_interval_m"][1] < -41.100259 or r["simultaneous_interval_m"][0] > 41.100259)
               for r in stats["comparisons"])
    practical, a = forest(stats)
    micro, b = forest(stats, micro=True)
    assert len(a["comparisons"])+len(b["comparisons"]) == 21
    assert set(a["comparisons"]).isdisjoint(b["comparisons"])
    plt.close(practical); plt.close(micro)
    fig, rows = seed_blocks(stats)
    plt.close(fig)
    assert len(rows) == 21
    fig, rows = tradeoff(stats)
    plt.close(fig)
    assert len(rows) == 21


def test_selection_horizons_fit_and_masks_use_fixed_inputs():
    from scripts.plot_pirc17_revision46 import Inputs, design_matrix, population, fit_diagnostics
    from matplotlib import pyplot as plt
    fig, value = population(Inputs())
    assert value["windows"] == [12370,127,106,46]
    assert value["blocks"] == [1094,89,73,46]
    plt.close(fig)
    fig, value = design_matrix()
    assert len(value["retained"]) == 10
    assert value["K"] == [2,28,19,23,20,20,7,7,6,10]
    assert all(row[0] == 1 for row in value["retained"])
    assert value["retained"][2][5] == value["retained"][4][5] == 0
    assert value["retained"][6][5] == value["retained"][8][5] == 0
    assert value["retained"][9][6] == 1
    assert all(row[7] == row[1] and row[8] == row[2] for row in value["retained"])
    plt.close(fig)
    fig, value = fit_diagnostics(Inputs())
    assert len(value["raw_rank"]) == len(value["raw_columns"]) == 10
    plt.close(fig)


@pytest.mark.parametrize("candidate,control,interval,seeds", [
    (100,160,(-80,-50),[-60]*5), (160,100,(50,80),[60]*5),
    (100,100,(-10,10),[0]*5), (100,105,(-30,20),[-5]*5)])
def test_factor_benefit_is_only_a_sign_reexpression(candidate,control,interval,seeds):
    delta = candidate-control
    benefit, benefit_interval = -delta, (-interval[1],-interval[0])
    assert benefit == control-candidate
    assert benefit_interval[0] <= benefit_interval[1]
    assert (-benefit_interval[1],-benefit_interval[0]) == interval
    assert [s < 0 for s in seeds] == [-s > 0 for s in seeds]
    # Practical-side/inside/crossing-zero geometry is invariant under the
    # reexpression, not a new qualification or statistical decision.
    assert (interval[1] < -41.100259) == (benefit_interval[0] > 41.100259)
    assert (interval[0] > 41.100259) == (benefit_interval[1] < -41.100259)
    assert (interval[0] <= 0 <= interval[1]) == (benefit_interval[0] <= 0 <= benefit_interval[1])


@pytest.mark.parametrize("language", ["en", "zh"])
def test_reader_body_has_independent_companions_and_public_boundary(language):
    text = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    # Source wrapping is not a reading-length measure. The editorial contract
    # is a 12--16 page body in the retained 11pt, one-inch-margin template.
    import fitz
    with fitz.open(PAPER / "revision46-review-v1" / language / "main.pdf") as document:
        assert 12 <= len(document) <= 16
    assert r"\appendix" not in text
    assert "inertial-horizons.pdf" in text and "practical-effects.pdf" in text
    assert "512" in text and "41.100259" in text
    assert "46.52" in text and "21.74--79.13" in text
    assert "1379/1380" in text and "1148/1150" in text
    assert r"\label{sec:case-horizons}" in text
    assert not re.search(r"\\(?:includegraphics|input)\{?[^\n]*case-", text)
    assert not (PAPER / "figures/case-horizons.json").exists()
    assert (PAPER / language / "supplement.tex").is_file()
    assert (PAPER / language / "audit-notes.tex").is_file()
    assert "11368" in text.replace(",", "")


def test_shared_unrounded_mean_error_rows_and_inertial_delta():
    profiles = read("point-error-horizon-description-v1.json")["profiles"]
    full = profiles[0]
    assert abs(sum(full["point_error_by_time_m"])/4-full["ade_m"]) < 1e-10
    assert full["point_error_by_time_m"][-1] == full["fde_m"]
    macros = (PAPER / "revision46-numbers.tex").read_text(encoding="utf-8")
    assert "{-346.87}" in macros
    for profile in profiles:
        assert " & ".join(f"{v:.2f}" for v in profile["point_error_by_time_m"]) in macros
