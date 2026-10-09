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
    plt.close(fig)
    fig, value = fit_diagnostics(Inputs())
    assert len(value["raw_rank"]) == len(value["raw_columns"]) == 10
    plt.close(fig)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_reader_body_has_independent_companions_and_public_boundary(language):
    text = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    assert len(text.splitlines()) < 500
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
