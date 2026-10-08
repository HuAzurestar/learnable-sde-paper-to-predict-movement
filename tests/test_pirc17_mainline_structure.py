"""Pure presentation placement checks; not experiment or peer-review acceptance."""
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"


def revision():
    return json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))["mainline_structure_revision"]


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("table", ["execution-coverage", "family-coverage", "forecast-counts"])
def test_scale_and_execution_table_bodies_are_preserved_at_intended_locations(language, table):
    tex = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    label = r"\label{tab:" + table + "}"
    assert tex.count(label) == 1
    start = tex.index(label)
    if table == "forecast-counts":
        assert start < tex.index(r"\label{sec:method-results}") < tex.index(r"\appendix")
        assert tex.index(r"\label{sec:forecast-inventory}") < start
    else:
        assert start > tex.index(r"\appendix")
    begin = tex.index(r"\begin{tabular}", start)
    end = tex.index(r"\end{tabular}", begin) + len(r"\end{tabular}")
    expected = revision()["moved_tables_and_main_source_measurement"][language]["moved_table_body_sha256"][table]
    body = tex[begin:end]
    if table == "family-coverage":
        # Only this family label is harmonized; every count/disposition stays exact.
        body = body.replace("Training and adaptation", "Transfer and adaptation")
        body = body.replace("训练及适应", "迁移及适应")
    assert hashlib.sha256(body.encode()).hexdigest() == expected


@pytest.mark.parametrize("language", ["en", "zh"])
def test_scientific_guides_and_paired_estimates_remain_in_main_text(language):
    tex = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    main = tex.split(r"\appendix", 1)[0]
    for label in revision()["preserved_main_labels"]:
        assert main.count(r"\label{" + label + "}") == 1
    section = main.split(r"\label{sec:method-results}", 1)[1]
    intro = section.split(r"\subsection", 1)[0]
    assert "6440" in intro and "46" in intro
    assert r"\ref{sec:forecast-inventory}" in intro
    assert r"\ref{sec:execution-coverage}" in intro
    assert "10514" not in section and "501" not in section
    assert ("completed independent output audit" if language == "en" else "独立输出审计及固定预算汇总复算核对") in intro
    assert ("interruption limits" if language == "en" else "中断限制") in intro
    assert ("pending output verification" if language == "en" else "仍待输出复核") not in intro


@pytest.mark.parametrize("language", ["en", "zh"])
def test_appendix_does_not_drop_failures_or_scheduled_auxiliary_scope(language):
    tex = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    appendix = tex.split(r"\appendix", 1)[1]
    for number in ("11020", "10514", "501", "261", "58", "38", "75", "15", "290"):
        assert number in appendix
    assert r"\label{sec:forecast-inventory}" not in appendix
    assert r"\label{sec:execution-coverage}" in appendix
    assert r"\texttt{lio-road}" in appendix and r"\texttt{lio-river}" in appendix
    assert ("not retried automatically" if language == "en" else "不自动重试") in appendix


def test_structure_revision_does_not_claim_review_closure_or_changed_science():
    value = revision()
    assert value["review_items"] == ["P2-02", "P2-08"]
    assert value["new_fits_forecasts_scores_or_statistical_inference"] == 0
    assert not value["registered_scope_or_failed_family_dispositions_changed"]
    assert not value["all_review_items_or_paper_complete"]
    assert value["source_base_commit"] == "3c180eb493a5f4e1f8a6f54a269f606aa3b7dc51"


def test_original_empirical_snapshot_is_not_replaced_by_layout_changes():
    path = PAPER / "preliminary-method-statistics-v1.json"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == (
        "8900f3dee68d5fc9cafd5ced2e2394503432d2493251601c0ba9cb771cbefba1")
    value = json.loads(path.read_text(encoding="utf-8"))
    assert len(value["configs"]) == 28 and len(value["comparisons"]) == 21
    assert not value["independent_raw_output_audit_completed"]


def test_five_method_families_match_seven_panel_controls_and_layout_ledger():
    from scripts.plot_pirc17_preliminary import effect_panels, load_snapshot

    panels = effect_panels(load_snapshot())
    assert [(p["title"], p["control"], len(p["rows"])) for p in panels] == [
        ("Model structure", "arm-01/full", 4),
        ("Observation interval", "arm-01/full", 4),
        ("Objective / score", "arm-07/full", 5),
        ("Training / adaptation", "arm-11/full", 4),
        ("Integration aliases", "arm-18/full", 2),
        ("MC propagation", "arm-20/full", 1),
        ("CRN propagation", "arm-20/full", 1),
    ]
    # The last three are axes within the fifth (numerical) family.
    labels = ["Model structure / Full01", "Observation interval / Full01",
              "Objective and score / Full07", "Training and adaptation / Full11",
              "Numerical propagation / Full18, Full20"]
    en = (PAPER / "en/main.tex").read_text(encoding="utf-8")
    assert all(en.count(label) == 1 for label in labels)
    intro = en.split(r"\label{sec:method-results}", 1)[1].split(r"\subsection", 1)[0]
    assert "observation interval" in intro and "training/adaptation" in intro
    assert "numerical inference" in intro
    assert "seven panels represent five method families" in en
    assert "Training and adaptation & 1150 & 1150" in en
    assert "Full anchor: training and adaptation" in en
    assert "Full anchor: transfer and adaptation" not in en
    zh = (PAPER / "zh/main.tex").read_text(encoding="utf-8")
    assert "Full 锚点：训练及适应" in zh
    assert "迁移与适应" not in zh
    value = revision()
    assert value["appendix_sections"] == ["sec:execution-coverage"]
    for language in ("en", "zh"):
        # The character-count measurement belongs to its delivered revision;
        # later paper additions do not rewrite that historical measurement.
        text = subprocess.check_output([
            "git", "show", value["source_measurement_commit"] + ":paper/pirc17/" + language + "/main.tex"
        ], cwd=PAPER.parents[1]).decode("utf-8")
        actual = len(text.split(r"\appendix", 1)[0])
        assert actual == value["moved_tables_and_main_source_measurement"][language]["main_source_characters_after"]
