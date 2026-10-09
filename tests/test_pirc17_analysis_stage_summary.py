# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Existing saved-analysis transport; no inference, experiments or acceptance."""
from collections import Counter
import json
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"


def summary():
    return json.loads((PAPER / "analysis-stage-summary-v1.json").read_text(encoding="utf-8"))


def test_real_immutable_analysis_scope_and_no_gate_promotion():
    data = summary()
    assert data["analysis_content_sha256"] == "d1d67a3bf4cd08d46f7e73f0178950b047197275f3f32e29a61f3f699fe5febc"
    assert data["analysis_file_sha256"] == "edd988e3df7ae95de773b33f75d62656a5426585a79c4d65c9421c10b2a45c50"
    inventory = json.loads((PAPER / "terminal-score-inventory-v1.json").read_text(encoding="utf-8"))
    for key in ("protocol_sha256", "execution_sha256", "matrix_sha256", "population_sha256", "scoring_inputs_sha256"):
        assert data["source_scope"][key] == inventory["source_scope"][key]
    assert data["parameters"] == dict(alpha=.05, bootstrap_iterations=2000,
        bootstrap_seed=20260926, delta_m=41.100259, mc_check_seed=20260927,
        minimum_blocks=30, required_agreeing_seeds=4, tail_tolerance_fraction_of_delta=.25)
    assert data["forecast_seeds"] == list(range(20260814, 20260819))
    assert data["new_fits"] == data["new_forecasts"] == data["new_scores_or_resampling_by_projection"] == 0
    for field in ("independent_saved_output_audit_completed", "scientific_claim_authorized",
                  "numerically_qualified", "human_accepted", "private_case_data_exported"):
        assert data[field] is False
    forbidden = {"origin_id", "sample_id", "independent_block_id", "block_ids",
                 "work_id", "path", "positions_m", "coordinates", "elapsed_seconds"}
    def check(value):
        if isinstance(value, dict):
            assert not forbidden.intersection(value)
            for child in value.values():
                check(child)
        elif isinstance(value, list):
            for child in value:
                check(child)
    check(data)


def test_all_three_modes_seven_families_and_retained_failures():
    rows = summary()["families"]
    assert len(rows) == 21
    families = {"method-model-structure": 4, "method-observation-interval": 4,
        "method-objective-and-score": 5, "method-transfer-adaptation": 4,
        "method-numerical-propagation": 4, "weighted-es-primary": 5, "weighted-es-lio": 4}
    failed = {("causal_prefix", "weighted-es-primary"): 1,
        ("causal_prefix", "weighted-es-lio"): 2,
        ("known_velocity", "method-model-structure"): 1,
        ("known_velocity", "method-observation-interval"): 1}
    assert {(r["origin_mode"], r["family_id"]) for r in rows} == {
        (mode, family) for mode in ("causal_prefix", "known_velocity", "point_only") for family in families}
    for row in rows:
        key = row["origin_mode"], row["family_id"]
        assert row["comparisons"] == families[row["family_id"]]
        assert row["blocks"] == (46 if row["origin_mode"] == "causal_prefix" else 6)
        assert row["missing_rows"] == 0
        assert row["failed_rows"] == failed.get(key, 0)
        assert sum(row["verdict_counts"].values()) == row["comparisons"]
        assert row["inference_present"] is (row["origin_mode"] == "causal_prefix" and key not in failed)
        if key in failed:
            assert row["verdict_counts"] == {"unavailable": row["comparisons"]}
        elif row["origin_mode"] != "causal_prefix":
            assert row["verdict_counts"] == {"inconclusive": row["comparisons"]}


def test_all_21_comparisons_preserve_prior_exact_arithmetic_and_original_states():
    data = summary()
    old = json.loads((PAPER / "preliminary-method-statistics-v1.json").read_text(encoding="utf-8"))
    earlier = {(r["family_id"], r["candidate"]): r for r in old["comparisons"]}
    rows = data["primary_method_comparisons"]
    assert len(rows) == len(earlier) == 21
    assert Counter(r["saved_verdict"] for r in rows) == {"equivalent": 14, "inconclusive": 7}
    for row in rows:
        before = earlier[row["family_id"], row["candidate"]]
        for field in ("control", "delta_estimate_m", "simultaneous_interval_m",
                      "holm_adjusted_p_zero", "tail_check_passed"):
            assert row[field] == before[field]
        assert row["mechanism_passed"] and row["tail_check_passed"]
        assert row["precision_invariant_verdict"] == "inconclusive"
        if row["saved_verdict"] == "equivalent":
            low, high = row["simultaneous_interval_m"]
            assert -data["parameters"]["delta_m"] < low <= high < data["parameters"]["delta_m"]
            assert row["planning_qualified"]
    by_candidate = {r["candidate"]: r for r in rows}
    assert by_candidate["arm-04/gmm_kernel"]["saved_verdict"] == "equivalent"
    assert by_candidate["arm-06/dt300"]["saved_verdict"] == "inconclusive"
    assert by_candidate["arm-06/dt600"]["reason"] == "planning_power_below_target"
    for slot in ("arm-10/d2_closed", "arm-10/d2_mc"):
        assert by_candidate[slot]["simultaneous_interval_m"] == [0., 0.]
        assert by_candidate[slot]["reason"] == "zero_development_SD_is_not_power_evidence"


def test_complete_mechanism_counts_do_not_become_global_accuracy_certification():
    data = summary()
    assert set(data["mechanisms"]) == {"causal_prefix", "known_velocity", "point_only"}
    for mode, evidence in data["mechanisms"].items():
        assert evidence["required_count"] == evidence["passed_count"] == 28
        assert evidence["counts_by_status"] == {"computed": 28}
        gates = {g["slot_id"]: g for g in evidence["diagnostics"]}
        assert len(gates) == 7
        for gate in gates.values():
            assert gate["passed"] and gate["status"] == "computed"
            assert gate["available_count"] == gate["expected_count"]
        for slot in ("arm-19/em", "arm-19/euler"):
            assert gates[slot]["operator"] == "ge" and gates[slot]["threshold"] == 0
        assert gates["arm-18/full"]["threshold"] == 2
        assert gates["arm-10/d2_closed"]["threshold"] == .2
        assert gates["arm-10/d2_closed"]["expected_count"] == (230 if mode == "causal_prefix" else 30)
    assert 0 < data["scoring_only_gaussian_draws_evaluated"] <= data["registered_scoring_only_draw_ceiling"]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_bilingual_main_discloses_saved_states_and_later_arithmetic_qualification(language):
    text = (PAPER / language / "historical-main-v1.tex").read_text(encoding="utf-8")
    assert text.count(r"\label{sec:saved-analysis-status}") == 1
    assert text.count(r"\label{tab:saved-analysis-states}") == 1
    status = text.split(r"\label{sec:saved-analysis-status}", 1)[1].split(r"\begingroup", 1)[0]
    for token in ("analysis-stage-summary-v1.json", "14", "seven" if language == "en" else "7",
                  "41.100259", "dt300", "dt600", "0.1937", "28", "2.19", r"\geq0"):
        assert token in status
    assert ("pending" if language == "en" else "待完成") in status
    # The original projection remains a historical stage record. The later
    # externally bound receipt completes arithmetic, not global science/acceptance.
    for name in ('qualification-v1/test02.json', 'qualification-v1/card-inventory.json'):
        assert name in status
    assert ("not independent empirical" if language == "en" else "不是独立实证") in status
    assert ("historical" if language == "en" else "历史记录") in status
    historical = text.split(r"\label{sec:bootstrap-table-detail}", 1)[1].split(r"\begin{longtable}", 1)[0]
    assert ("historical caption" if language == "en" else "历史表题") in historical
    names = (["Model structure", "Observation interval", "Fitting and score route",
              "Training and adaptation", "Numerical propagation", "Total"] if language == "en"
             else ["模型结构", "观测间隔", "拟合与评分路线", "训练与适应", "数值传播", "合计"])
    for name, counts in zip(names, [(1, 3), (2, 2), (3, 2), (4, 0), (4, 0), (14, 7)]):
        assert f"{name} & {counts[0]} & {counts[1]}" + r"\\" in status
