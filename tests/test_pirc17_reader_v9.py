"""User-requested structure, terrain semantics and active display-name coverage."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
import pytest

from scripts.pirc17_display_names import display_text, method_name, tex_display
from scripts.render_pirc17_reader_v9 import name_figure

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"


@pytest.mark.parametrize("lang", ["en", "zh"])
def test_model_design_training_prediction_form_one_subsection(lang):
    main = (PAPER / lang / "main.tex").read_text(encoding="utf-8")
    fit = (PAPER / lang / "reader-v4-full.tex").read_text(encoding="utf-8")
    assert r"\subsubsection" in fit.split(r"\label{sec:training-methods}")[0].splitlines()[-1]
    assert r"\subsubsection{Forecasting and component updates}\label{sec:forecast-methods}" in main if lang == "en" else r"\subsubsection{预测方法与分量更新}\label{sec:forecast-methods}" in main
    model = main.split(r"\label{sec:models}", 1)[1].split(r"\label{sec:terrain-methods}", 1)[0]
    assert model.count(r"\subsection{") == 1  # Only the next terrain heading.
    assert "heading-stratified mixture stochastic differential" in main
    assert "residual-direction mixture stochastic differential" in main
    assert "sec:main-terrain" not in model


@pytest.mark.parametrize("lang", ["en", "zh"])
def test_terrain_main_has_actual_inputs_compositions_and_configuration_mapping(lang):
    text = (PAPER / lang / "reader-v9-terrain-factors.tex").read_text(encoding="utf-8")
    assert all(v in text for v in ("tab:main-terrain-factors", "tab:main-terrain-configurations",
                                   "eq:main-map-distance", "eq:main-map-compositions",
                                   "leave-one-group-out", "leave-one-group-in", "28", "19", "23", "20", "7", "6", "10"))
    assert all(v in text for v in (r"\ell_{\rm river}", r"u_{\rm river}", r"\ell_{\rm road}w", "h^\\top a", "h^\\top q"))
    phrases = ("not a line tangent", "No direct", "speed-magnitude multiplier", "footway", "refitting") if lang == "en" else ("不是沿线切向量", "没有", "速度大小", "footway", "重新拟合")
    assert all(v in text for v in phrases)


def test_declarative_contract_derives_all_ten_widths_and_dependencies():
    contract = json.loads((PAPER / "reader-v9-terrain-contract.json").read_text())
    assert len(contract["configurations"]) == 10
    for row in contract["configurations"]:
        groups = {"history", *row["groups"]}
        k = sum(contract["groups"][g]["numeric_width"] for g in groups)
        k += sum(c["width"] for c in contract["compositions"].values() if set(c["parents"]) <= groups)
        assert k == row["numeric"]
    assert not contract["groups"]["river"]["direct_history_velocity_product"]
    assert not contract["new_empirical_execution"]


def test_display_policy_keeps_original_roles_and_tex_anchors():
    assert method_name("01", "full") == "HSM-01"
    assert method_name("11", "full") == "HSM-11"
    assert display_text("Full01 / GMM kernel / inertial") == "HSM-01 / RDM / CV"
    assert display_text("arm-04/gmm_kernel") == "RDM"
    assert display_text("arm-04/gmm\\_kernel") == "RDM"
    assert display_text("lio-river") == "B + river"
    raw = r"\label{fig:inertial}\ref{fig:inertial}\includegraphics{preliminary-full-horizons.pdf} Full01 & 46.52\\"
    translated = tex_display(raw)
    assert r"\label{fig:inertial}" in translated
    assert r"\ref{fig:inertial}" in translated
    assert r"\includegraphics{preliminary-full-horizons.pdf}" in translated
    assert "HSM-01 & 46.52" in translated
    assert display_text("the full table") == "the full table"


def test_actual_figure_text_relabel_preserves_scientific_artist_arrays():
    fig, ax = plt.subplots()
    ax.plot([1, 5, 15, 30], [50.57, 243.23, 400, 600], label="Full")
    ax.set_xticks([1, 5], ["Full01", "GMM"])
    ax.set_title("GMM kernel versus inertial")
    ax.legend()
    try:
        record = name_figure(fig)
        assert record["scientific_artist_sha256_before"] == record["scientific_artist_sha256_after"]
        assert [t.get_text() for t in ax.get_xticklabels()] == ["HSM-01", "RDM"]
        assert ax.get_title() == "RDM versus CV"
    finally:
        plt.close(fig)


def test_all_active_figures_have_new_names_and_unchanged_artist_data():
    folder = PAPER / "figures/reader-v9"
    manifest = json.loads((folder / "manifest.json").read_text())
    assert manifest["active_unique_figures"] == len(manifest["figures"]) == 19
    assert not manifest["historical_assets_overwritten"]
    for row in manifest["figures"]:
        assert row["scientific_artist_sha256_before"] == row["scientific_artist_sha256_after"]
        assert not any(re.search(r"\b(?:Full\d*|GMM|Inertial|inertial)\b", label) for label in row["displayed_labels"])
        assert hashlib.sha256((ROOT / row["original_pdf"]).read_bytes()).hexdigest() == row["original_pdf_sha256"]
        for file, checksum in row["files_sha256"].items():
            assert hashlib.sha256((folder / file).read_bytes()).hexdigest() == checksum
    for row in manifest["tex_projections"]:
        assert hashlib.sha256((PAPER / row["projection"]).read_text(encoding="utf-8").encode()).hexdigest() == row["projection_utf8_lf_sha256"]


def test_original_numeric_evidence_and_data_files_are_not_renamed():
    paths = subprocess.check_output(["git", "diff", "fdc07f0", "--name-only", "--", "paper/pirc17"], cwd=ROOT, text=True).splitlines()
    # Existing numerical evidence remains exact; new display contracts/manifests
    # are separate files, not edits to scientific JSON/CSV keys or source numbers.
    assert not [p for p in paths if p.endswith((".json", ".csv")) and "reader-v9" not in p]
    assert "paper/pirc17/revision46-numbers.tex" not in paths


def test_actual_pdf_figure_text_has_no_legacy_model_labels():
    import fitz
    files = list((PAPER / "figures/reader-v9").glob("*.pdf"))
    assert len(files) == 19
    for path in files:
        with fitz.open(path) as doc:
            text = " ".join(page.get_text() for page in doc)
        assert not re.search(r"\b(?:Full\d*|GMM|Inertial|inertial)\b", text), path.name
    original = [line.split("&", 1)[1] for line in (PAPER / "revision46-numbers.tex").read_text().splitlines() if line.startswith(r"\newcommand{\PointRow")]
    current = [line.split("&", 1)[1] for line in (PAPER / "reader-v9-number-labels.tex").read_text().splitlines()]
    assert current == original
