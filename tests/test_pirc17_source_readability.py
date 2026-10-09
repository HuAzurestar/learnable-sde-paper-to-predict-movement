# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Pure manuscript reorganization checks; not scientific or reader acceptance."""
import json
from pathlib import Path
import re
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"
BASE = "8e739ba307746e54d8c1e4a57432f435c8a52a5a"
MARKERS = {
    "en": [["We checked every one of the 7,618 assignments","\\begin{table}[htbp]"],["For a refined segment with \\(n\\geq4\\) points","\\paragraph{Exact source-sequence check.}"],["The release report records 74 exact recording-hash groups","Table~\\ref{tab:cohort-denominators}"],["The source construction script converts input km/h","The released and selected medians"],["Table~\\ref{tab:clock-use} separates the saved","\\begin{table}[htbp]"],["The original release report records 37,957","\\paragraph{Executed solar condition.}"],["The private case backgrounds use WorldCover","\\subsection{Model map support and query rules}"],["The model's retained map catalog is distinct","\\begin{table}[htbp]"],["The model's elevation channel labelled","\\subsection{Three origin modes}"]],
    "zh": [["本次用冻结源函数核对全部 7,618 个文件分配","\\begin{table}[htbp]"],["对于 \\(n\\geq4\\) 个点的细分 segment","\\paragraph{源记录完整序列的精确重复检查。}"],["release 报告记载 74 个完全相同的记录哈希组","表~\\ref{tab:cohort-denominators}"],["保留源构建脚本将输入km/h","已发布与最终入选的窗口间中位数"],["表~\\ref{tab:clock-use} 区分保存时钟与算法时钟。release","\\begin{table}[htbp]"],["原 release 报告记录 37,957 个重复时刻间隔","\\paragraph{实际太阳条件计算。}"],["私有案例背景使用 WorldCover","\\subsection{模型地图支持与查询规则}"],["模型保留的地图目录不同于三份案例背景","\\begin{table}[htbp]"],["模型中标为 \\texttt{srtm} 的高程通道","\\subsection{三种起点模式}"]]
}


def previous(language):
    return subprocess.check_output(["git", "show",
        f"{BASE}:paper/pirc17/{language}/main.tex"], cwd=ROOT).decode("utf-8").replace("\r\n", "\n")


def current(language):
    return (PAPER/language/"historical-main-v1.tex").read_text(encoding="utf-8")


@pytest.mark.parametrize("language", ["en", "zh"])
def test_nine_original_source_descriptions_move_verbatim_once_to_appendix(language):
    before, after = previous(language), current(language)
    main, appendix = after.split(r"\appendix", 1)
    assert appendix.count(r"\label{sec:source-reconciliation-details}") == 1
    assert r"\label{sec:source-reconciliation-details}" not in main
    assert main.count(r"\ref{sec:source-reconciliation-details}") == 9
    for start, end in MARKERS[language]:
        at = before.index(start)
        original = before[at:before.index(end, at)].rstrip()
        assert original not in main
        assert appendix.count(original) == after.count(original) == 1
    for path in ("partition-description-v1.json", "clock-description-v1.json",
                 "map-source-acknowledgements-v1.json"):
        assert path in appendix


@pytest.mark.parametrize("language", ["en", "zh"])
def test_historical_source_only_revision_kept_scientific_environments_exact_ordered(language):
    before = previous(language)
    # This ordered-environment claim belongs to the delivered source-only
    # revision. Later reviewed table relocation must not rewrite its proof,
    # or be forbidden merely because the original prose unit moved no tables.
    after = subprocess.check_output(["git", "show",
        f"0ce0a107b8695635fb45a06205ed17ad790145c1:paper/pirc17/{language}/main.tex"],
        cwd=ROOT).decode("utf-8").replace("\r\n", "\n")
    for kind in ("table", "longtable", "figure", "equation", "align"):
        pattern = r"\\begin\{" + kind + r"\}.*?\\end\{" + kind + r"\}"
        assert re.findall(pattern,before,re.S) == re.findall(pattern,after,re.S)
    # No moved display or numeric block is hidden by the prose relocation.
    displays = re.findall(r"\\\[.*?\\\]",before,re.S)
    assert displays and displays == re.findall(r"\\\[.*?\\\]",after,re.S)
    bib = r"\begin{thebibliography}{99}"
    assert before[before.index(bib):] == after[after.index(bib):]
    assert re.findall(r"\\label\{([^}]+)\}",before) == [
        label for label in re.findall(r"\\label\{([^}]+)\}",after)
        if label != "sec:source-reconciliation-details"]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_shorter_experimental_main_retains_population_clock_permissions_and_solar_spec(language):
    before, after = previous(language), current(language)
    main = after.split(r"\appendix",1)[0]
    start, end = ((r"\section{Experimental setup}",r"\section{Method ablation results}")
                  if language=="en" else (r"\section{实验设置}",r"\section{方法消融结果}"))
    old = before[before.index(start):before.index(end)]
    new = main[main.index(start):main.index(end)]
    assert len(new) < len(old)
    for count in ("328","76","81","259","62","12,370","46","1354","1283","1232","1405"):
        assert count in new
    for anchor in ("sec:clock-and-map-provenance","sec:model-map-support",
                   "sec:data-reference-roles","tab:clock-use","eq:solar-condition",
                   "sec:source-sequence-screen","tab:source-sequence-screen"):
        assert r"\label{"+anchor+"}" in new
    phrases = ("no window is removed","not a first-use",
               "Exact tick matching or timestamp format does not certify UTC provenance",
               "case publication permissions remain unverified",
               "do not establish a physically\nvalidated daylight") if language=="en" else (
               "不移除窗口","不是首次使用","不能认证 UTC 来源",
               "案例发表授权仍未核实","不证明经物理验证的日光")
    for phrase in phrases:
        assert phrase in new


def test_readability_ledger_does_not_promote_science_permissions_or_final_acceptance():
    ledger=json.loads((PAPER/"claim-ledger.json").read_text(encoding="utf-8"))
    entry=ledger["source_provenance_readability_revision"]
    assert entry["source_base_commit"]==BASE
    assert entry["review_items"]==["P2-02"]
    assert entry["moved_source_descriptions"]==9
    assert entry["original_source_descriptions_retained_verbatim_once"]
    assert entry["all_original_tables_figures_equations_align_and_display_blocks_exact_ordered"]
    assert entry["new_fits_forecasts_scores_resampling_or_map_queries"]==0
    for key in ("protocol_selection_parameters_or_scientific_values_changed",
                "clock_participant_or_map_provenance_certified",
                "privacy_or_publication_permissions_verified",
                "independent_saved_output_audit_completed",
                "whole_paper_or_non_project_reader_acceptance_obtained",
                "final_paper_or_review_complete"):
        assert entry[key] is False
    assert ledger["final_empirical_results_integrated"] is False
    assert ledger["human_accepted"] is False
