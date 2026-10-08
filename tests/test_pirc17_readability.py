"""Pure manuscript/source checks; no simulations, scoring or inference."""
import hashlib
import json
import re
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"


@pytest.mark.parametrize("language", ["en", "zh"])
def test_names_and_original_identities_are_defined_not_relabelled(language):
    tex = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    model = tex.split(r"\section{Forecast models and terrain ownership}" if language == "en"
                      else r"\section{预测模型与地形归属}", 1)[1]
    definitions = model.split(r"\begin{figure}", 1)[0]
    for word in ("conditioner", "provider", "ensemble", "verdict", "Full",
                 "base", "all-terrain", "dt", r"two\_step", r"explicit\_decomp"):
        assert word in definitions
    assert ("not independent observations" if language == "en" else "不是独立观测样本") in definitions
    if language == "zh":
        assert "模拟模拟集合" not in tex
        assert "模拟 模拟集合" not in tex
    for label in ("eq:conditioner-fit", "eq:ensemble-es", "tab:method-reader",
                  "tab:forecast-counts"):
        assert tex.count(r"\label{" + label + "}") == 1


@pytest.mark.parametrize("language", ["en", "zh"])
def test_display_precision_preserves_bound_original_timings_and_delta(language):
    source = PAPER / "preliminary-reader-presentation-v1.json"
    timing = json.loads(source.read_text(encoding="utf-8"))
    ledger = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))
    revision = ledger["terminology_and_display_revision"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == revision["timing_source_sha256"]
    tex = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    table = tex.split(r"\label{tab:preliminary-cost}", 1)[1].split(r"\end{tabular}", 1)[0]
    names = {"arm-01/full": "Full01", "arm-04/gmm_kernel": "GMM kernel",
             "arm-06/dt300": "dt300", "arm-19/em": "EM", "arm-21/mc": "MC"}
    for row in timing["timings"]:
        expected = names[row["configuration"]] + f" & {row['prediction_seconds']:.3f}"
        assert expected in table
    config = json.loads((PAPER / "inference-description-v1.json").read_text(encoding="utf-8"))
    assert config["inference_config"]["delta_m"] == revision["registered_delta_m"] == 41.100259
    assert tex.count(r"\delta=41.100259") == 1
    assert r"\delta\approx41.10" in tex
    assert ("not a claim" if language == "en" else "不声称微秒级测量准确度") in tex
    assert not revision["registered_delta_or_decision_rules_changed"]
    assert revision["new_fits_forecasts_scores_or_inference"] == 0
    assert not revision["all_review_items_or_paper_complete"]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_all_five_method_questions_and_numerical_diagnostic_scope(language):
    tex = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    section = tex.split(r"\section{Method ablation results}" if language == "en"
                        else r"\section{方法消融结果}", 1)[1]
    introduction = section.split(r"\subsection", 1)[0]
    names = ("model structure", "observation", "learning objective", "training/adaptation",
             "numerical inference") if language == "en" else (
             "模型结构", "观测间隔", "学习目标", "训练/适应", "数值推断")
    for name in names:
        assert name in introduction
    for label in ("tab:method-reader", "tab:forecast-counts"):
        assert r"\ref{" + label + "}" in introduction
    assert ("not 36 independent algorithms" if language == "en" else "不是 36 个独立算法") in introduction
    assert ("numerical diagnostic scale" if language == "en" else "数值诊断尺度") in section
    assert ("not centimetre-level predictive accuracy" if language == "en" else "不表示厘米级预测精度") in section
    stage = json.loads((PAPER / "preliminary-method-statistics-v1.json").read_text(encoding="utf-8"))
    assert len(stage["comparisons"]) == 21 and len(stage["configs"]) == 28
    assert not stage["independent_raw_output_audit_completed"]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_longtable_continuations_restate_table_and_columns(language):
    tex = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    ledger = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))
    revision = ledger["table_layout_revision"]
    tables = re.findall(r"\\begin\{longtable\}.*?\\end\{longtable\}", tex, re.S)
    assert len(revision["main_longtable_columns"]) == 5  # original layout revision remains scoped
    labels = {re.search(r"\\label\{([^}]+)\}", table).group(1) for table in tables}
    assert labels == set(revision["main_longtable_columns"]) | {
        ledger["original_reptile_task_description"]["table_label"]}
    for label, columns in revision["main_longtable_columns"].items():
        table = next(t for t in tables if r"\label{" + label + "}" in t)
        first, remainder = table.split(r"\endfirsthead", 1)
        continued = remainder.split(r"\endhead", 1)[0]
        title = (r"Table~\thetable\ (continued)" if language == "en"
                 else r"表~\thetable\ （续表）")
        assert r"\multicolumn{" + str(columns) + "}{l}{" + title + r"}\\" in continued
        header = first.split(r"\toprule", 1)[1].strip()
        assert continued.split(r"\toprule", 1)[1].strip() == header
        assert tex.count(r"\label{" + label + "}") == 1
    appendix = (PAPER / language / "all-method-absolute.tex").read_text(encoding="utf-8")
    assert r"\endfirsthead" in appendix and r"\endhead" in appendix
    assert ("continued" if language == "en" else "续表") in appendix


@pytest.mark.parametrize("language", ["en", "zh"])
def test_layout_revision_preserves_pinned_stage_table_data(language):
    tex = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    ledger = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))
    revision = ledger["table_layout_revision"]
    tables = re.findall(r"\\begin\{longtable\}.*?\\end\{longtable\}", tex, re.S)
    for label, expected in revision["normalized_data_body_sha256"][language].items():
        table = next(t for t in tables if r"\label{" + label + "}" in t)
        body = table.split(r"\endhead", 1)[1].replace("\r\n", "\n")
        if label == "tab:method-inventory":
            # Review P2-08 harmonizes only the family name, not slots/counts.
            body = body.replace("Full anchor: training and adaptation", "Full anchor: transfer and adaptation")
            body = body.replace("Full 锚点：训练及适应", "Full 锚点：迁移与适应")
        assert hashlib.sha256(body.encode("utf-8")).hexdigest() == expected
    table = next(t for t in re.findall(r"\\begin\{table\}.*?\\end\{table\}", tex, re.S)
                 if r"\label{tab:preliminary-coverage}" in t)
    assert table.index(r"\caption{") < table.index(r"\label{tab:preliminary-coverage}") < table.index(r"\begin{tabular}")
    for row in ("1 & 50.57 & 95.65", "5 & 243.23 & 37.83",
                "15 & 609.27 & 35.22", "30 & 1008.35 & 46.52"):
        assert row + r"\\" in table
    assert revision["new_fits_forecasts_scores_or_inference"] == 0
    assert not revision["all_review_items_or_paper_complete"]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_float_only_page_spacing_is_scoped_without_shrinking_text(language):
    tex = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    preamble, body = tex.split(r"\begin{document}", 1)
    style = ("\\makeatletter\n\\setlength{\\@fptop}{0pt}\n"
             "\\setlength{\\@fpsep}{16pt}\n"
             "\\setlength{\\@fpbot}{0pt plus 1fil}\n\\makeatother")
    assert preamble.count(style) == 1 and style not in body
    ledger = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))
    revision = ledger["table_layout_revision"]
    assert revision["float_only_page_gap_pt"] == 16
    assert not revision["body_text_float_spacing_or_font_sizes_changed"]
    assert ledger["template"] == "existing article class and one-inch margins"


@pytest.mark.parametrize("language", ["en", "zh"])
def test_cost_reading_keeps_timing_units_and_moves_only_environment_details(language):
    tex = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    body, appendix = tex.split(r"\appendix", 1)
    heading = r"\section{Computational cost}" if language == "en" else r"\section{计算成本}"
    cost = body.split(heading, 1)[1].split(r"\section{", 1)[0]
    assert r"\ref{sec:runtime-record-details}" in cost
    assert r"\label{sec:runtime-record-details}" not in body
    assert appendix.count(r"\label{sec:runtime-record-details}") == 1
    assert "psutil" not in cost and "PyArrow" not in cost
    assert "psutil" in appendix and "PyArrow" in appendix
    assert r"\overline C/(H/60)" in cost
    assert "p50" in cost and "p95" in cost
    for phrase in (("operating-system cache is neither reset nor verified",
                    "total successful-trial latency in milliseconds",
                    "five-trial failure-rate", "per-trial peak", "added again")
                   if language == "en" else
                   ("操作系统缓存既未重置也未经核实", "成功试验总延迟",
                    "五次试验的故障率分母", "不是单次试验峰值", "不能再次相加")):
        assert phrase in cost
    assert ("not a measured cache-state guarantee" if language == "en"
            else "不是实测缓存状态保证") in appendix


def test_cost_revision_does_not_replace_pending_original_measurements():
    ledger = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))
    revision = ledger["computational_cost_reading_revision"]
    assert revision["source_base_commit"] == "2aa4e10808d1a7b2a70681b0ee89ceb3e80d8fdb"
    assert revision["review_items"] == ["P1-23", "P2-02"]
    source = PAPER / "preliminary-reader-presentation-v1.json"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == revision["timing_source_sha256"]
    assert revision["raw_p50_p95_milliseconds_distinct_from_horizon_normalized_mean"]
    assert revision["provider_cold_does_not_certify_operating_system_cache_state"]
    assert not revision["original_protocol_receipts_and_forecast_configuration_changed"]
    assert revision["new_fits_forecasts_scores_resampling_or_map_queries"] == 0
    assert not revision["formal_runtime_results_or_independent_output_audit_completed"]
    assert not revision["non_project_reader_acceptance_or_final_paper_complete"]
    assert not ledger["final_empirical_results_integrated"] and not ledger["human_accepted"]
