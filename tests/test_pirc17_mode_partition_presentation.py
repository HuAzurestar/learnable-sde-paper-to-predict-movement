# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Original count and rank-rule documentation, not recovered transition labels."""
import hashlib
import json
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"
D = json.loads((PAPER / "mode-partition-description-v1.json").read_text(encoding="utf-8"))
L = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))


def test_all_original_records_and_prediction_slots_match_saved_noise_projection():
    old = json.loads((PAPER / "method-noise-description-v1.json").read_text(encoding="utf-8"))
    rows = {r["representative_slot"]: r for r in D["methods"]}
    prior = {r["representative_slot"]: r for r in old["methods"]}
    assert len(rows) == len(prior) == 16 and rows.keys() == prior.keys()
    assert len({slot for r in rows.values() for slot in r["prediction_slots"]}) == 28
    for slot in rows:
        for field in ["original_record_sha256", "model_kind", "reference_interval_seconds", "prediction_slots"]:
            assert rows[slot][field] == prior[slot][field]
    assert D["inventory_sha256"] == old["inventory_sha256"]
    assert len(D["source_sha256"]) == 2


@pytest.mark.parametrize("role,n,cardinality", [("train", 328, [110, 109, 109]),
                                                ("adapt", 76, [26, 25, 25]),
                                                ("validation", 81, [27, 27, 27])])
def test_rank_cardinalities_are_segment_counts_and_transition_frequencies_remain_unknown(role, n, cardinality):
    assert D["whole_role_rank_segment_counts"][role] == cardinality
    assert sum(cardinality) == n
    for method in D["methods"]:
        row = method["roles"][role]
        assert row["segments"] == n and row["whole_role_heading_rank_segment_counts"] == cardinality
        assert row["multimode_transition_frequencies"] is None
        assert row["all_transitions"] >= 3 * n


def test_reference_full_role_transitions_are_not_divided_equally_or_inverted_from_probabilities():
    full = next(r for r in D["methods"] if r["representative_slot"] == "arm-01/full")
    assert full["reference_interval_seconds"] == 60.
    assert {role: full["roles"][role]["all_transitions"] for role in ["train", "adapt", "validation"]} == {
        "train": 26009, "adapt": 5762, "validation": 6149}
    scope = D["scope"]
    assert not scope["actual_segment_labels_or_multimode_transition_frequencies_recovered"]
    assert not scope["final_blended_probabilities_inverted_to_frequencies"]
    assert not scope["gmm_residual_partitions_reconstructed"]
    assert not scope["segment_balance_implies_transition_balance"]
    assert scope["counts_describe_complete_role_batches_not_all_Reptile_region_tasks"]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_bilingual_rank_formula_table_and_scope(language):
    tex = (PAPER / language / "historical-main-v1.tex").read_text(encoding="utf-8")
    for label in ["eq:segment-rank-mode", "tab:mode-rank-cardinality"]:
        assert tex.count(r"\label{" + label + "}") == 1
    assert r"\min\{2,\lfloor 3r_s/K\rfloor\}" in tex
    assert r"\(m=m_s+1\)" in tex
    assert r"\([-\pi,\pi]\)" in tex and r"\texttt{math.atan2}" in tex
    assert ("cut on the westward axis" if language == "en" else "切口位于向西轴") in tex
    assert ("zero-displacement heading filter" if language == "en" else "零位移方向过滤") in tex
    at = tex.index(r"\label{eq:segment-rank-mode}")
    end = tex.index(r"\label{tab:mode-rank-cardinality}", at) + 900
    section = tex[at:end]
    for row in ["328 & 110 & 109 & 109", "76 & 26 & 25 & 25", "81 & 27 & 27 & 27"]:
        assert row in section
    for phrase in (["do not give transition counts", "not a per-region task census",
                    "not describe the residual-mixture partition"] if language == "en" else
                   ["不提供逐模式转移数", "不是逐地区任务清点", "不描述残差混合的分组"]):
        assert phrase in section


def test_projection_and_reader_metadata_are_scoped_not_scientific_acceptance():
    r = L["original_mode_partition_description"]
    assert r["projection_sha256"] == hashlib.sha256((PAPER / "mode-partition-description-v1.json").read_bytes()).hexdigest()
    assert r["review_items"] == ["P1-02"] and r["original_fit_records"] == 16
    assert r["prediction_slots"] == 28 and r["prepared_segment_population_per_fit"] == 485
    assert r["complete_role_segment_counts"] == {"train": 328, "adapt": 76, "validation": 81}
    assert r["whole_role_rank_segment_cardinalities"] == D["whole_role_rank_segment_counts"]
    for flag in ["actual_multimode_transition_frequencies_recovered",
                 "gmm_residual_groups_or_reptile_region_task_counts_reconstructed",
                 "raw_development_inputs_reloaded_or_resampled", "final_probabilities_inverted_to_counts",
                 "independent_saved_output_audit_completed", "all_review_items_or_paper_complete"]:
        assert not r[flag]
    assert r["new_fits_forecasts_scores_resampling_or_map_queries"] == 0
    assert not L["final_empirical_results_integrated"] and not L["human_accepted"]


def test_no_new_experiments_or_private_source_identity_export():
    s = D["scope"]
    assert s["new_fits_forecasts_scores_resampling_or_map_queries"] == 0
    assert not s["raw_coordinates_times_labels_residuals_or_private_paths_exported"]
    assert not s["independent_saved_output_audit_completed"] and not s["all_review_items_or_paper_complete"]
    text = (PAPER / "mode-partition-description-v1.json").read_text(encoding="utf-8")
    assert '"segment_id"' not in text and '"mode_labels"' not in text
