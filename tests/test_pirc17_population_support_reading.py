# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Existing population-table placement checks, not new empirical evidence."""
import json
from pathlib import Path
import re
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"
BASE = "da0f9b2a513614923b57a43e3566d9b217f72143"
LABELS = ("final-cohort-durations", "final-cohort-speeds", "final-cohort-geography")


def before(language):
    return subprocess.check_output([
        "git", "show", f"{BASE}:paper/pirc17/{language}/main.tex"
    ], cwd=ROOT).decode("utf-8").replace("\r\n", "\n")


@pytest.mark.parametrize("language", ["en", "zh"])
def test_three_original_population_tables_are_verbatim_once_in_appendix(language):
    original = before(language)
    current = (PAPER / language / "historical-main-v1.tex").read_text(encoding="utf-8")
    main, appendix = current.split(r"\appendix", 1)
    tables = re.findall(r"\\begin\{table\}.*?\\end\{table\}", original, re.S)
    for label in LABELS:
        marker = r"\label{tab:" + label + "}"
        table, = [t for t in tables if marker in t]
        assert table not in main
        assert appendix.count(table) == current.count(table) == 1
        assert marker not in main
        assert r"\ref{tab:" + label + "}" in main
        assert r"\label{sec:" + label + "}" in appendix
    equation, = [e for e in re.findall(r"\\begin\{equation\}.*?\\end\{equation\}", original, re.S)
                 if r"\label{eq:cohort-window-speed}" in e]
    assert equation not in main and appendix.count(equation) == 1


@pytest.mark.parametrize("language", ["en", "zh"])
def test_main_summary_preserves_selection_limits_and_does_not_add_a_data_table(language):
    current = (PAPER / language / "historical-main-v1.tex").read_text(encoding="utf-8")
    main = current.split(r"\appendix", 1)[0]
    start = main.index(r"\label{sec:population-support-summary}")
    summary = main[start:main.index(r"\subsection", start)]
    for value in ("12,370", "46", "69.8", "2,323", "130", "1,800", "1.621", "1.486", "33/46", "71.7"):
        assert value in summary
    assert r"\ref{sec:population-description-construction}" in summary
    assert r"\ref{sec:source-reconciliation-details}" in summary
    assert r"\begin{table}" not in summary
    phrases = ("do not become predictor inputs or revised eligibility", "no window is removed",
               "physical-time independence", "certify physical") if language == "en" else (
               "不成为预测器输入或重定资格", "不移除窗口", "物理时间独立", "不认证物理采集")
    for phrase in phrases:
        assert phrase in summary


def test_revision_retains_old_evidence_and_no_claim_of_final_acceptance():
    ledger = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))
    old = json.loads(subprocess.check_output([
        "git", "show", f"{BASE}:paper/pirc17/claim-ledger.json"
    ], cwd=ROOT).decode("utf-8"))
    assert old == {key: ledger[key] for key in old}
    entry = ledger["population_support_reading_revision"]
    assert entry["source_base_commit"] == BASE
    assert entry["review_items"] == ["P2-02"]
    assert entry["moved_original_table_labels"] == ["tab:" + s for s in LABELS]
    assert entry["original_table_cells_equation_and_explanations_retained"]
    assert entry["new_fits_forecasts_scores_resampling_or_map_queries"] == 0
    for flag in ("original_protocol_selection_parameters_or_scientific_values_changed",
                 "independent_saved_output_audit_completed", "full_manuscript_reader_or_human_acceptance_obtained",
                 "publication_permissions_verified", "final_paper_or_all_review_items_complete"):
        assert entry[flag] is False
    assert not ledger["final_empirical_results_integrated"] and not ledger["human_accepted"]


@pytest.mark.parametrize("kind,label", [*(('table', 'tab:' + s) for s in LABELS),
                                       ('equation', 'eq:cohort-window-speed')])
@pytest.mark.parametrize("fault", ["changed", "missing", "duplicate"])
def test_named_relocation_guard_never_permits_changed_missing_or_duplicate_values(kind, label, fault):
    from scripts.pirc17_document_blocks import assert_preserved_blocks
    block = r"\begin{" + kind + "}10" + r"\label{" + label + "}" + r"\end{" + kind + "}"
    bad = [block.replace('}10', '}11')] if fault == "changed" else [] if fault == "missing" else [block, block]
    with pytest.raises(AssertionError):
        assert_preserved_blocks([block], bad, kind)


@pytest.mark.parametrize("kind,label", [("table", "tab:final-cohort-speeds"),
                                       ("equation", "eq:cohort-window-speed")])
def test_named_move_preserves_unrelated_order_and_bytes(kind, label):
    from scripts.pirc17_document_blocks import assert_preserved_blocks
    moved = r"\begin{" + kind + "}10" + r"\label{" + label + "}" + r"\end{" + kind + "}"
    assert_preserved_blocks(['before', moved, 'after'], ['before', 'after', moved], kind)


@pytest.mark.parametrize("kind", ["table", "equation"])
def test_unnamed_scientific_reordering_is_still_rejected(kind):
    from scripts.pirc17_document_blocks import assert_preserved_blocks
    with pytest.raises(AssertionError, match="other scientific blocks"):
        assert_preserved_blocks(['before', 'after'], ['after', 'before'], kind)
