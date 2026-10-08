"""Verify history model/data separation without weakening scientific content."""
from pathlib import Path
import json
import re
import subprocess

import pytest

from scripts.pirc17_document_blocks import assert_preserved_blocks

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"
BASE = "dd02d979e8d1f600b628e42ef0b79bce42f8f347"


def previous(language):
    return subprocess.check_output(["git","show",f"{BASE}:paper/pirc17/{language}/main.tex"],
        cwd=ROOT).decode("utf-8").replace("\r\n","\n")


def subsection(tex, anchor):
    start=tex.index(r"\label{"+anchor+"}")+len(r"\label{"+anchor+"}")
    return tex[start:tex.index(r"\subsection{",start)]


@pytest.mark.parametrize("language",["en","zh"])
def test_complete_observed_history_statistics_move_verbatim_to_experimental_setup(language):
    before=previous(language)
    after=(PAPER/language/"main.tex").read_text(encoding="utf-8")
    old=subsection(before,"sec:history-feedback")
    end=old.index("There is also a noise-distribution change." if language=="en" else r"\begin{samepage}")
    moved=old[:end].strip()
    timings=subsection(after,"sec:empirical-history-timings")
    assert timings.count(moved)==1 and after.count(moved)==1
    setup=r"\section{Experimental setup}" if language=="en" else r"\section{实验设置}"
    results=r"\section{Method ablation results}" if language=="en" else r"\section{方法消融结果}"
    for label in ("sec:empirical-history-timings","tab:history-spans","tab:development-history-spans"):
        at=after.index(r"\label{"+label+"}")
        assert after.index(setup)<at<after.index(results)<after.index(r"\appendix")
    assert "404 & 5.992 & 6 & 8 & 11 & 36" in timings
    assert ("not counts of independent participants" if language=="en" else "不是独立参与者数") in timings
    assert ("does not establish training--rollout" if language=="en" else "不证明训练与预测分布等价") in timings


@pytest.mark.parametrize("language",["en","zh"])
def test_rules_and_complete_original_noise_argument_stay_in_shorter_model_passage(language):
    before=previous(language)
    after=(PAPER/language/"main.tex").read_text(encoding="utf-8")
    old=subsection(before,"sec:history-feedback")
    model=subsection(after,"sec:history-feedback")
    at=old.index("There is also a noise-distribution change." if language=="en" else r"\begin{samepage}")
    assert old[at:]==model[model.index(old[at:].split("\n")[0]):]
    assert len(model)<len(old)
    assert r"\ref{sec:empirical-history-timings}" in model
    assert r"\(d+5\)" in model
    for formula in (r"\frac{Q}{T}",r"\frac{(T-s)_+}{T^2}Q",r"Q/T+2R_{\rm obs}/T^2"):
        assert formula in model
    for label in ("eq:secant-local-noise","eq:secant-overlap"):
        assert r"\label{"+label+"}" in model
    assert ("not a fitted sensor model" if language=="en" else "不是拟合的传感器模型") in model
    assert ("applies\nto the terrain buffer only" if language=="en" else "仅适用于地形缓冲") in model
    assert r"\begin{table}" not in model


@pytest.mark.parametrize("language",["en","zh"])
def test_every_scientific_block_is_exact_with_only_the_two_named_table_moves(language):
    before=previous(language)
    after=(PAPER/language/"main.tex").read_text(encoding="utf-8")
    for kind in ("table","longtable","figure","equation"):
        pattern=r"\\begin\{"+kind+r"\}.*?\\end\{"+kind+r"\}"
        assert_preserved_blocks(re.findall(pattern,before,re.S),re.findall(pattern,after,re.S),kind)


def test_preservation_guard_allows_only_exact_two_named_table_relocation():
    a=r"\begin{table}A\label{tab:history-spans}\end{table}"
    b=r"\begin{table}B\label{tab:development-history-spans}\end{table}"
    assert_preserved_blocks([a,"c","d",b],["c",a,b,"d"],"table")
    for changed in ([a,"c","d",b+"changed"],[a,"c","d"],[a,"c","d",b,b],
                    [a,"d","c",b]):
        with pytest.raises(AssertionError):
            assert_preserved_blocks([a,"c","d",b],changed,"table")
    with pytest.raises(AssertionError):
        assert_preserved_blocks([a,"c"],["c",a],"equation")


def test_reading_revision_does_not_change_science_or_certify_complete_paper():
    ledger=json.loads((PAPER/"claim-ledger.json").read_text(encoding="utf-8"))
    record=ledger["history_method_experiment_reading_revision"]
    assert record["source_base_commit"]==BASE
    assert record["review_items"]==["P2-02"]
    for field in ("observed_prefix_statistics_moved_verbatim_to_experimental_setup",
                  "buffer_rules_secant_formulas_and_local_noise_limits_retained_in_method",
                  "all_original_scientific_blocks_exact_only_two_history_tables_reordered"):
        assert record[field] is True
    for field in ("training_and_final_history_evidence_or_scientific_parameters_changed",
                  "whole_paper_page_reduction_claimed","independent_saved_output_audit_completed",
                  "whole_manuscript_reader_acceptance_obtained","all_review_items_or_paper_complete"):
        assert record[field] is False
    assert record["new_fits_forecasts_scores_resampling_or_map_queries"]==0
    assert not ledger["final_empirical_results_integrated"] and not ledger["human_accepted"]
