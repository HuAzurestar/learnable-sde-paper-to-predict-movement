# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Reader-facing order and exact saved-display preservation, not acceptance."""
import json
import re
import subprocess
from pathlib import Path

import pytest

from scripts.pirc17_document_blocks import assert_preserved_blocks

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"
BASE = "2d32a224ed62c2e5704df4f6ef76ec7b6cb95071"
HEADINGS = {
    "en": (r"\subsection{Structure, observation interval and fitting strategy}",
           r"\subsection{Horizon-dependent error and empirical coverage}"),
    "zh": (r"\subsection{结构、观测间隔及拟合策略}",
           r"\subsection{时域误差与经验覆盖率}"),
}


def sources(language):
    old = subprocess.check_output(
        ["git", "show", f"{BASE}:paper/pirc17/{language}/main.tex"], cwd=ROOT
    ).decode("utf-8").replace("\r\n", "\n")
    new = (PAPER / language / "historical-main-v1.tex").read_text(encoding="utf-8")
    return old, new


@pytest.mark.parametrize("language", ["en", "zh"])
def test_findings_precede_complete_estimates_and_fullpage_figures(language):
    _, tex = sources(language)
    guide = tex.index(r"\label{tab:metric-reader}")
    findings = tex.index(r"\label{sec:method-findings}")
    estimates = tex.index(r"\label{sec:preliminary-methods}")
    table = tex.index(r"\label{tab:preliminary-method-effects}")
    effects = tex.index(r"\label{fig:preliminary-method-effects}")
    absolute = tex.index(r"\label{fig:preliminary-method-absolute}")
    horizon = tex.index(HEADINGS[language][1])
    assert guide < findings < estimates < table < effects < absolute < horizon
    assert tex.count(r"\label{sec:method-findings}") == 1
    assert findings < tex.index(r"\appendix")
    assert r"\usepackage{placeins}" in tex
    barrier = r"\FloatBarrier"+"\n"
    if language == "en":
        barrier += r"\endgroup"+"\n"
        assert r"\renewcommand{\topfraction}{.95}" in tex
        assert r"\renewcommand{\textfraction}{.02}" in tex
    assert barrier+HEADINGS[language][0] in tex


@pytest.mark.parametrize("language", ["en", "zh"])
def test_existing_interpretation_moves_verbatim_not_new_findings(language):
    old, new = sources(language)
    head, end = HEADINGS[language]
    original = old[old.index(head):old.index(end)].strip()
    moved = new[new.index(head):new.index(r"\subsection{", new.index(head)+len(head))].strip()
    moved = moved.replace(r"\label{sec:method-findings}"+"\n", "", 1)
    assert moved == original
    assert new.count(original.split("\n\n")[1]) == 1
    for value in ("32.95", "41.10", "57.96", "11.56", "23.40",
                  "1326.09", "1335.73", "1340.94", "0.02545"):
        assert value in moved


@pytest.mark.parametrize("language", ["en", "zh"])
def test_all_original_table_and_figure_blocks_are_exactly_preserved(language):
    old, new = sources(language)
    for kind in ("table", "longtable", "figure"):
        pattern = r"\\begin\{" + kind + r"\}.*?\\end\{" + kind + r"\}"
        before = re.findall(pattern, old, re.S)
        after = re.findall(pattern, new, re.S)
        if kind == "table":
            # One later descriptive table repeats the24 bound map-panel errors.
            # Its complete contents are checked in test_pirc17_case_horizons;
            # every original table and all original figures must still be exact.
            added = [block for block in after if r"\label{tab:case-point-errors}" in block]
            assert len(added) == 1
            after.remove(added[0])
        assert before, kind
        assert_preserved_blocks(before, after, kind)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_scope_discussion_separates_four_limits_without_certifying_them(language):
    _, tex = sources(language)
    start = tex.index(r"\label{sec:discussion-scope}")
    scope = tex[start:tex.index(r"\section{", start)]
    names = (("Model-specific attribution.", "Population and clock support.",
              "Numerical and inferential support.", "Unavailable comparisons.")
             if language == "en" else
             ("模型内归因。", "人群与时钟支持。", "数值与推断支持。", "不可用比较。"))
    indexes = [scope.index(r"\paragraph{"+name+"}") for name in names]
    assert indexes == sorted(indexes)
    for label in ("eq:terrain-history", "eq:method-history", "eq:constant-mask-penalty",
                  "sec:clock-and-map-provenance", "sec:final-cohort-funnel",
                  "sec:final-cohort-geography"):
        assert label in scope
    for phrase in (("not certified", "independent participants", "worldwide performance",
                    "not a pure terrain", "cannot establish")
                   if language == "en" else
                   ("不等于已认证", "不能证明参与者独立或全球", "不是纯地形信息增量", "不能说明")):
        assert phrase in scope
    assert r"\(N=512\)" in scope and r"\(h\le5\)" in scope
    assert r"\hyperref[sec:final-cohort-funnel]" in scope
    assert r"\hyperref[sec:final-cohort-geography]" in scope


def test_revision_record_does_not_close_review_or_change_science():
    ledger = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))
    r = ledger["results_discussion_reading_revision"]
    assert r["source_base_commit"] == BASE and r["review_items"] == ["P2-02"]
    assert r["source_interpretation_paragraphs_moved_verbatim"]
    assert r["interpretation_placed_before_full_paired_table_and_two_full_page_figures"]
    assert r["float_barrier_keeps_method_and_metric_guides_before_findings"]
    assert r["all_original_tables_figures_effect_numbers_and_scientific_scope_preserved"]
    assert r["new_fits_forecasts_scores_resampling_or_map_queries"] == 0
    for name in ("physical_clock_participant_independence_or_worldwide_performance_certified",
                 "independent_saved_output_audit_completed",
                 "non_project_reader_acceptance_or_all_review_items_complete",
                 "final_paper_or_scientific_qualification_complete"):
        assert not r[name]
    assert not ledger["final_empirical_results_integrated"] and not ledger["human_accepted"]
