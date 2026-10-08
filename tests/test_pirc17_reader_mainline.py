"""Reader-facing placement and unchanged-data checks, not reader acceptance."""
import json
import re
import subprocess
from pathlib import Path

import pytest

from scripts.pirc17_document_blocks import assert_preserved_blocks

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"
BASE = "8457769ad6c76238525f1ee166c21a7b6895c948"


def current(language):
    return (PAPER / language / "main.tex").read_text(encoding="utf-8")


def original(language):
    return subprocess.check_output([
        "git", "show", f"{BASE}:paper/pirc17/{language}/main.tex"
    ], cwd=ROOT).decode("utf-8").replace("\r\n", "\n")


@pytest.mark.parametrize("language", ["en", "zh"])
def test_reptile_source_field_rule_moves_but_scientific_method_stays(language):
    tex = current(language)
    main, appendix = tex.split(r"\appendix", 1)
    before = subprocess.check_output([
        "git", "show", "12a9f36c2e2215f9082ac9584757a0d2cb073188:"
        f"paper/pirc17/{language}/main.tex"
    ], cwd=ROOT).decode("utf-8").replace("\r\n", "\n")
    if language == "en":
        start = before.index("The adapter first strips the source")
        end = before.index("Of 84 label groups", start)
    else:
        start = before.index("适配器先去除源")
        end = before.index("84个标签组中", start)
    rule = before[start:end].rstrip()
    assert rule not in main and appendix.count(rule) == 1
    path = "paper/pirc17/method-algorithm-description-v1.json"
    assert path not in main and appendix.count(path) == 1
    assert main.count(r"\ref{sec:reptile-task-accounting}") == 2
    at = main.index(r"\label{eq:meta-inner}")
    method = main[main.rfind(r"\subsection{", 0, at):main.find(r"\subsection{", at)]
    for value in ("328", "84", "30", "258", "20,029", "54", "70", "5,980",
                  "1.595", "1.260", r"\label{eq:meta-inner}",
                  r"\label{eq:meta-outer}", r"\label{eq:target-blend}"):
        assert value in method
    for en, zh in (("without a country key or case", "不含国家键、不统一大小写"),
                   ("not certified cities", "不是已核实城市"),
                   ("without random task sampling", "不随机抽任务或打乱"),
                   ("not held-out performance", "不是留出性能"),
                   ("Intermediate pre-meta and pre-target parameter snapshots were not saved",
                    "原结果未保存元更新前及目标混合前的中间参数快照")):
        assert (en if language == "en" else zh) in method


@pytest.mark.parametrize("language", ["en", "zh"])
def test_reptile_readability_preserves_all_scientific_blocks_and_shortens_reptile_passage(language):
    before = subprocess.check_output([
        "git", "show", "12a9f36c2e2215f9082ac9584757a0d2cb073188:"
        f"paper/pirc17/{language}/main.tex"
    ], cwd=ROOT).decode("utf-8").replace("\r\n", "\n")
    after = current(language)
    for kind in ("table", "longtable", "figure", "equation"):
        pattern = r"\\begin\{" + kind + r"\}.*?\\end\{" + kind + r"\}"
        assert_preserved_blocks(re.findall(pattern, before, re.S), re.findall(pattern, after, re.S), kind)
    def reptile_passage(tex):
        # Scope the historical shortening claim to the actual revised passage;
        # later mathematical specifications elsewhere in this method are allowed.
        start = r"\paragraph{Fitting and adaptation scope.}" if language=="en" else r"\paragraph{拟合与适应范围。}"
        end = r"\paragraph{What the finite objective comparison actually changes.}" if language=="en" else r"\paragraph{有限拟合目标比较实际改变了什么。}"
        return tex[tex.index(start):tex.index(end)]
    assert len(reptile_passage(after)) < len(reptile_passage(before))


def test_reptile_readability_does_not_change_scope_or_certify_acceptance():
    ledger = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))
    entry = ledger["reptile_description_readability_revision"]
    assert entry["source_base_commit"] == "12a9f36c2e2215f9082ac9584757a0d2cb073188"
    assert entry["review_items"] == ["P2-02"]
    assert entry["appendix_anchor"] == "sec:reptile-task-accounting"
    for field in ("exact_source_field_grouping_and_saved_algorithm_path_retained_in_appendix",
                  "task_counts_grouping_limits_updates_and_missing_parameters_retained_in_main",
                  "all_original_tables_figures_and_equations_preserved"):
        assert entry[field]
    for field in ("original_protocol_selection_or_task_definition_changed",
                  "full_manuscript_reader_acceptance_obtained",
                  "independent_saved_output_audit_completed", "all_review_items_or_paper_complete"):
        assert not entry[field]
    assert entry["new_fits_forecasts_scores_resampling_or_map_queries"] == 0
    assert not ledger["final_empirical_results_integrated"] and not ledger["human_accepted"]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_historical_population_construction_moves_without_changing_scientific_blocks(language):
    before = subprocess.check_output([
        "git", "show", "60308bea654c6487e16cd18c5af8c41c22d94669:"
        f"paper/pirc17/{language}/main.tex"
    ], cwd=ROOT).decode("utf-8").replace("\r\n", "\n")
    # The older unit retained tables in the main text. Verify that claim on
    # the last inspected pre-relocation delivery, not every future layout.
    after = subprocess.check_output(["git", "show",
        f"da0f9b2a513614923b57a43e3566d9b217f72143:paper/pirc17/{language}/main.tex"],
        cwd=ROOT).decode("utf-8").replace("\r\n", "\n")
    main, appendix = after.split(r"\appendix", 1)
    # Measure the population passage, not unrelated later-added scientific results.
    def population(tex):
        start = tex.index(r"\label{sec:final-cohort-durations}")
        end = tex.index(r"\subsection{", start)
        return tex[start:end]
    assert len(population(main)) < len(population(before))
    assert main.count(r"\ref{sec:population-description-construction}") == 3
    assert after.count(r"\label{sec:population-description-construction}") == 1
    for kind in ("table", "longtable", "figure", "equation"):
        pattern = r"\\begin\{" + kind + r"\}.*?\\end\{" + kind + r"\}"
        blocks = re.findall(pattern, after, re.S)
        if kind == "table":
            added = [block for block in blocks if r"\label{tab:case-point-errors}" in block]
            assert len(added) == 1
            blocks.remove(added[0])
        assert_preserved_blocks(re.findall(pattern, before, re.S), blocks, kind)
    for name in ("duration", "speed", "geography"):
        path = f"paper/pirc17/final-cohort-{name}-description-v1.json"
        assert path not in main and appendix.count(path) == 1
    for value in ("1,125", "12,370", "63"):
        assert value in appendix


@pytest.mark.parametrize("language", ["en", "zh"])
def test_historical_population_scientific_definitions_were_reader_facing(language):
    delivered = subprocess.check_output(["git", "show",
        f"da0f9b2a513614923b57a43e3566d9b217f72143:paper/pirc17/{language}/main.tex"],
        cwd=ROOT).decode("utf-8").replace("\r\n", "\n")
    main = delivered.split(r"\appendix", 1)[0]
    for token in ("D=t_{\\mathrm{last}}-t_{\\mathrm{origin}}", "130/12,370",
                  "38.7", "33/46", "493/1094", "465",
                  r"\label{eq:cohort-window-speed}"):
        assert token in main
    for en, zh in (("invalid clock windows are neither dropped nor clipped", "不裁剪或删除无效时间窗口"),
                   ("not certification of", "不认证原物理UTC"),
                   ("no window is removed", "不移除窗口"),
                   ("not predictor inputs or revised eligibility", "不输入预测器或重定资格"),
                   ("not a distribution of online secant inputs", "不是在线割线输入"),
                   ("not verified point locations", "而非逐点地理定位"),
                   ("465 lack a harvest-area", "465 项缺失采集区域"),
                   ("not a representative survey", "不是已发布 63 个来源国家的代表性调查")):
        assert (en if language == "en" else zh) in main


def test_population_readability_is_not_final_acceptance_or_new_experiment_authority():
    ledger = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))
    entry = ledger["population_description_readability_revision"]
    assert entry["source_base_commit"] == "60308bea654c6487e16cd18c5af8c41c22d94669"
    assert entry["review_items"] == ["P2-02"]
    assert entry["new_fits_forecasts_scores_resampling_or_map_queries"] == 0
    assert entry["full_population_denominators_and_scientific_caveats_retained_in_main"]
    assert entry["original_tables_figures_and_equation_blocks_preserved"]
    for field in ("original_selection_or_protocol_changed", "full_manuscript_reader_acceptance_obtained",
                  "independent_saved_output_audit_completed", "all_review_items_or_paper_complete"):
        assert not entry[field]
    assert not ledger["final_empirical_results_integrated"] and not ledger["human_accepted"]


def subsection(text, label):
    at = text.index(r"\label{" + label + "}")
    start = text.rfind(r"\subsection{", 0, at)
    end = text.find(r"\subsection{", at)
    return text[start:end if end >= 0 else None]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_project_codes_and_worker_jargon_are_not_required_in_main(language):
    main = current(language).split(r"\appendix", 1)[0]
    displayed = "\n".join(x for x in main.splitlines() if not x.lstrip().startswith("%"))
    assert "PIRC" not in displayed and "NEX326" not in displayed
    assert not re.search(r"\b(?:lane|WorkID|RunRecord)\b", displayed)
    assert r"\ref{sec:method-implementation-map}" in main
    appendix = current(language).split(r"\appendix", 1)[1]
    for name in ("PIRC-20", "PIRC-21", "PIRC-22", "NEX326"):
        assert name in appendix


@pytest.mark.parametrize("language", ["en", "zh"])
@pytest.mark.parametrize("label", ["tab:method-inventory", "tab:bootstrap-diagnostics"])
def test_complete_implementation_and_tail_tables_move_without_any_changes(language, label):
    before = original(language)
    after = current(language)
    needle = r"\label{" + label + "}"
    assert before.index(needle) < before.index(r"\appendix")
    assert after.index(needle) > after.index(r"\appendix")
    def table(text):
        at = text.index(needle)
        begin = text.rfind(r"\begin{longtable}", 0, at)
        end = text.index(r"\end{longtable}", at) + len(r"\end{longtable}")
        return text[begin:end]
    assert table(before) == table(after)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_detailed_development_section_is_verbatim_except_noise_moved_to_model(language):
    before = subsection(original(language), "sec:saved-fit-diagnostics")
    noise_at = before.index(r"\label{eq:saved-method-noise}")
    start = before.rfind(r"\paragraph{", 0, noise_at)
    end = before.index("\n\n", before.index(
        r"\path{paper/pirc17/method-noise-description-v1.json}")) + 2
    noise = before[start:end]
    text = current(language)
    assert text.count(noise) == 1
    assert text.index(noise) < text.index(r"\appendix")
    detailed = subsection(text, "sec:saved-fit-diagnostics")
    expected = before.replace(noise, "", 1)
    paragraph = expected.rstrip().split("\n\n")[-1]
    wrapper = "\\noindent\\parbox{\\linewidth}{\n" + paragraph + "\n}"
    detailed = detailed.replace(wrapper, paragraph)
    # A later count-reconciliation section starts on a fresh Chinese page;
    # this known trailing layout command changes no diagnostic content.
    if language == "zh":
        detailed = detailed.removesuffix("\\clearpage\n")
    assert detailed == expected
    assert text.index(r"\label{sec:saved-fit-diagnostics}") > text.index(r"\appendix")
    summary = subsection(text, "sec:development-fit-summary")
    for number in ("328", "76", "81", "404", "57", "27/25", "0.136666",
                   "0.145796", "0.079117", "0.077077"):
        assert number in summary
    assert r"\eqref{eq:constant-mask-penalty}" in summary


@pytest.mark.parametrize("language", ["en", "zh"])
def test_stage_capture_paragraph_is_preserved_in_appendix_not_rewritten_as_live(language):
    before = original(language)
    start = before.index(r"\label{sec:preliminary-methods}") + len(r"\label{sec:preliminary-methods}") + 1
    end = before.index("\n\n", start) + 2
    paragraph = before[start:end]
    text = current(language)
    assert text.count(paragraph) == 1
    assert text.index(paragraph) > text.index(r"\appendix")
    stage = subsection(text, "sec:preliminary-methods")
    assert "6440" in stage and "230" in stage and "46" in stage
    assert r"\ref{sec:score-execution-snapshots}" in stage
    assert "10384" not in stage and "631" not in stage


@pytest.mark.parametrize("language", ["en", "zh"])
def test_scientific_model_metric_and_result_definitions_stay_in_main(language):
    main = current(language).split(r"\appendix", 1)[0]
    for label in ("eq:method-sde", "eq:terrain-rate-Q", "eq:conditioner-fit",
                  "eq:ensemble-es", "eq:population-es", "eq:primary-aggregation",
                  "tab:method-reader", "tab:metric-reader", "tab:preliminary-method-effects",
                  "tab:preliminary-coverage", "tab:model-map-catalog", "tab:forecast-counts"):
        assert main.count(r"\label{" + label + "}") == 1
    for label in ("tab:method-inventory", "tab:bootstrap-diagnostics",
                  "tab:fit-transition-counts", "tab:terrain-fit-diagnostics", "tab:raw-terrain-design"):
        assert r"\label{" + label + "}" not in main
    assert r"\label{eq:saved-method-noise}" in main
    assert r"\label{sec:bootstrap-resolution}" in main and "2000" in main


@pytest.mark.parametrize("language", ["en", "zh"])
def test_all_original_table_numbers_and_scientific_data_are_unchanged(language):
    def bodies(tex):
        # Scientific family names replace internal arm numbers in exactly one guide.
        def keyed(kind):
            tables = re.findall(r"\\begin\{" + kind + r"\}.*?\\end\{" + kind + r"\}", tex, re.S)
            return {re.search(r"\\label\{([^}]+)\}", t).group(1): t
                    for t in tables if re.search(r"\\label\{([^}]+)\}", t)}
        result = {}
        for kind in ("table", "longtable"):
            for label, table in keyed(kind).items():
                if label == "tab:method-families":
                    continue
                if kind == "table":
                    table = table[table.index(r"\begin{tabular}"):table.index(r"\end{tabular}")]
                result[label] = table
        return result
    before, after = bodies(original(language)), bodies(current(language))
    # Every original scientific table must remain exact. Later-added clock
    # and metadata reconciliation tables have their own source/count tests.
    assert before == {label: after[label] for label in before}
    assert set(after) - set(before) == {"tab:capture-count-difference", "tab:development-history-spans",
                                     "tab:mode-rank-cardinality", "tab:final-cohort-geography",
                                     "tab:final-cohort-durations", "tab:final-cohort-speeds",
                                     "tab:reptile-task-accounting", "tab:case-point-errors",
                                     "tab:source-sequence-screen", "tab:terminal-score-inventory"}


@pytest.mark.parametrize("language", ["en", "zh"])
def test_all_scientific_cross_references_have_manuscript_or_appendix_anchors(language):
    tex = current(language)
    inputs = re.findall(r"\\input\{([^}]+)\}", tex)
    assert set(inputs) == {"all-method-absolute.tex", "method-seed-stability.tex",
                           "method-horizon-overview.tex", "method-horizon-tables.tex",
                           "method-region-overview.tex", "method-region-tables.tex",
                           "inertial-primary-comparison.tex", "point-error-horizons.tex"}
    for filename in inputs:
        tex += (PAPER / language / filename).read_text(encoding="utf-8")
    labels = set(re.findall(r"\\label\{([^}]+)\}", tex))
    references = set(re.findall(r"\\(?:eqref|ref)\{([^}]+)\}", tex))
    assert references <= labels, sorted(references - labels)


def test_structure_record_does_not_certify_reader_or_scientific_acceptance():
    j = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))
    r = j["reader_mainline_revision"]
    assert r["source_base_commit"] == BASE and r["review_items"] == ["P2-02"]
    assert r["new_fits_forecasts_scores_resampling_or_map_queries"] == 0
    for field in ("scientific_scope_numbers_failure_dispositions_or_parameters_changed",
                  "non_project_reader_acceptance_or_all_review_items_complete",
                  "final_paper_or_scientific_qualification_complete"):
        assert not r[field]
    for language, measurement in r["source_character_measurement"].items():
        assert measurement["main_before"] == len(original(language).split(r"\appendix", 1)[0])
        measured = subprocess.check_output([
            "git", "show", r["source_measurement_commit"] + ":paper/pirc17/" + language + "/main.tex"
        ], cwd=ROOT).decode("utf-8").replace("\r\n", "\n")
        assert measurement["main_after"] == len(measured.split(r"\appendix", 1)[0])
        assert measurement["main_after"] < measurement["main_before"]
    assert not j["final_empirical_results_integrated"] and not j["human_accepted"]
