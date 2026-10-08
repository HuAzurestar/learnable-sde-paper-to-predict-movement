"""Saved aggregate evidence only; not participant or route independence proof."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

import pytest
from scripts.pirc17_document_blocks import assert_preserved_blocks

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "paper/pirc17/source-sequence-description-v1.json"


def evidence():
    return json.loads(PATH.read_text(encoding="utf-8"))


def test_exact_saved_projection_binding_and_complete_scope():
    assert hashlib.sha256(PATH.read_bytes()).hexdigest() == (
        "3c6e119511cdfc09244511cc4b5b839a7dd86585a9c7e76adbb2ae4fe82443b9")
    data = evidence()
    assert set(data) == {"schema_version", "bindings", "roles", "cross_role", "definition", "scope"}
    assert data["schema_version"] == "pirc17-selected-source-sequence-description-v1"
    assert data["bindings"]["selected_condition_files"] == 443
    assert sum(r["selected_windows"] for r in data["roles"].values()) == 531
    assert sum(r["source_rows"] for r in data["roles"].values()) == 2499407
    assert set(data["roles"]) == {"train", "adapt", "validation", "final_eval"}
    assert len(data["cross_role"]) == 6


@pytest.mark.parametrize("role,windows,files,blocks", [
    ("train", 328, 266, 259), ("adapt", 76, 65, 62),
    ("validation", 81, 66, 62), ("final_eval", 46, 46, 46),
])
def test_original_selected_denominators_not_full_release_or_forecast_count(role, windows, files, blocks):
    row = evidence()["roles"][role]
    assert row["selected_windows"] == windows
    assert row["source_files"] == files
    assert row["selected_recording_hash_blocks"] == blocks
    assert row["nonfinite_coordinate_rows"] == row["missing_clock_rows"] == 0


@pytest.mark.parametrize("pair", ["train:adapt", "train:validation", "train:final_eval",
                                  "adapt:validation", "adapt:final_eval", "validation:final_eval"])
def test_all_cross_role_exact_sequence_pairs_use_full_source_file_denominators(pair):
    data = evidence()
    a, b = pair.split(":")
    row = data["cross_role"][pair]
    assert row["possible_source_file_pairs"] == data["roles"][a]["source_files"] * data["roles"][b]["source_files"]
    for key in ("coordinate_fingerprint", "coordinate_clock_fingerprint"):
        assert set(row[key]) == {"equal_sequence_file_pairs", "shared_sequence_groups",
                                 "matching_files_left", "matching_files_right"}
        assert all(value == 0 for value in row[key].values())


@pytest.mark.parametrize("role,pairs,groups,files", [
    ("train", 9, 5, 12), ("adapt", 4, 2, 5),
    ("validation", 4, 4, 8), ("final_eval", 0, 0, 0),
])
def test_retained_within_role_matches_do_not_disappear_or_claim_new_block_matches(role, pairs, groups, files):
    row = evidence()["roles"][role]
    for key in ("coordinate_fingerprint", "coordinate_clock_fingerprint"):
        assert row[key] == {"equal_sequence_file_pairs": pairs,
                            "equal_sequence_groups": groups,
                            "files_in_equal_sequence_groups": files,
                            "equal_sequence_pairs_outside_same_recording_hash_block": 0}


def test_exact_complete_sequences_are_not_near_route_or_physical_clock_qualification():
    data = evidence()
    scope = data["scope"]
    for name in ("near_route_partial_overlap_or_repeated_visit_search_performed",
                 "participant_or_physical_clock_independence_established",
                 "physical_utc_or_coordinate_provenance_certified",
                 "original_eligibility_selection_or_model_parameters_changed",
                 "independent_saved_forecast_output_audit_completed",
                 "private_ids_coordinates_epochs_paths_or_record_fingerprints_exported",
                 "all_review_items_or_paper_complete"):
        assert scope[name] is False
    assert scope["new_fits_forecasts_scores_resampling_or_map_queries"] == 0
    assert scope["whole_source_recordings_not_only_selected_window_or_fitted_transitions"]
    assert scope["whole_source_rows_are_not_independent_observations"]
    for text in ("original order", "no rounding/resampling/reversal/translation", "NaT sentinel"):
        assert text in data["definition"]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_actual_source_denominators_and_limits_are_in_bilingual_experiments(language):
    tex = (ROOT / "paper/pirc17" / language / "main.tex").read_text(encoding="utf-8")
    for label in ("sec:source-sequence-screen", "tab:source-sequence-screen"):
        assert tex.count(r"\label{" + label + "}") == 1
    start = tex.index(r"\label{sec:source-sequence-screen}")
    end = tex.index(r"\paragraph{Previously used evaluation data.}" if language == "en"
                    else r"\paragraph{评估数据的既往使用。}", start)
    passage = tex[start:end]
    assert "source-sequence-description-v1.json" in passage
    table = re.search(r"\\begin\{table\}.*?\\end\{table\}", passage, re.S).group()
    rows = [(328,266,1407171,9,5),(76,65,388784,4,2),
            (81,66,360616,4,4),(46,46,342836,0,0)]
    for windows, files, points, pairs, groups in rows:
        assert f"& {windows} & {files} & {points:,} & {pairs} ({groups})" in table
    for denominator in (17290,17556,12236,4290,2990,3036):
        assert f"{denominator:,}" in passage
    for term in (("not fitted transitions", "do not detect approximate routes",
                  "do not establish independent people", "physical UTC") if language == "en"
                 else ("不是拟合转移数", "不检索近似路线", "不能证明参与者或路线独立", "物理 UTC")):
        assert term in re.sub(r"\s+", " ", passage)
    setup = r"\section{Experimental setup}" if language == "en" else r"\section{实验设置}"
    results = r"\section{Method ablation results}" if language == "en" else r"\section{方法消融结果}"
    assert tex.index(setup) < start < end < tex.index(results)
    # The older identity-only check must not imply this new reader avoided coordinates.
    assert ("that identity" if language == "en" else "上述身份核对") in tex
    assert "本次没有重读原始坐标" not in tex


@pytest.mark.parametrize("language", ["en", "zh"])
def test_new_source_table_preserves_every_previous_scientific_environment(language):
    before = subprocess.check_output(["git", "show",
        f"7258b83ecb2025eb299e1797ca901c7272516904:paper/pirc17/{language}/main.tex"],
        cwd=ROOT).decode("utf-8").replace("\r\n", "\n")
    after = (ROOT / "paper/pirc17" / language / "main.tex").read_text(encoding="utf-8")
    for kind in ("table", "longtable", "figure", "equation", "align"):
        pattern = r"\\begin\{" + kind + r"\}.*?\\end\{" + kind + r"\}"
        old, new = re.findall(pattern,before,re.S), re.findall(pattern,after,re.S)
        if kind == "table":
            added = [block for block in new if r"\label{tab:source-sequence-screen}" in block]
            assert len(added) == 1 and len(new) == len(old)+1
            new.remove(added[0])
        # Permit only the later explicitly named verbatim relocations; still
        # require exact bytes, counts and order for all other scientific blocks.
        from scripts.pirc17_document_blocks import assert_preserved_blocks
        assert_preserved_blocks(old, new, kind)


def test_named_addition_guard_rejects_other_changes_duplicates_and_later_edits():
    added = r"\begin{table}SOURCE\label{tab:source-sequence-screen}\end{table}"
    assert_preserved_blocks(["a","b"],["a",added,"b"],"table")
    for invalid in (["b",added,"a"],["a",added,"changed"],
                    ["a",added,added,"b"],["a","unknown table","b"]):
        with pytest.raises(AssertionError):
            assert_preserved_blocks(["a","b"],invalid,"table")
    for invalid in (["a","b"],["a",added+"edit","b"],[added,"a","b"]):
        with pytest.raises(AssertionError):
            assert_preserved_blocks(["a",added,"b"],invalid,"table")
    with pytest.raises(AssertionError):
        assert_preserved_blocks(["a","b"],["a",added,"b"],"equation")


def test_manuscript_ledger_binds_limited_evidence_without_changing_selection_or_acceptance():
    ledger = json.loads((ROOT / "paper/pirc17/claim-ledger.json").read_text(encoding="utf-8"))
    entry = ledger["source_sequence_manuscript_revision"]
    assert entry["projection_sha256"] == hashlib.sha256(PATH.read_bytes()).hexdigest()
    assert entry["source_base_commit"] == "7258b83ecb2025eb299e1797ca901c7272516904"
    assert (entry["selected_windows"],entry["source_files"],entry["whole_source_rows"]) == (531,443,2499407)
    assert entry["cross_role_comparisons"] == 6
    assert entry["within_role_equal_file_pairs"] == [9,4,4,0]
    for key in ("whole_source_rows_are_fitted_transitions",
                "participant_near_route_partial_overlap_or_physical_utc_independence_established",
                "original_selection_weights_fits_predictions_or_scope_changed",
                "independent_saved_output_audit_completed", "final_paper_or_review_complete"):
        assert entry[key] is False
    assert entry["new_fits_forecasts_scores_resampling_or_map_queries"] == 0
    assert ledger["final_empirical_results_integrated"] is False
    assert ledger["human_accepted"] is False


def test_source_sequence_response_retains_original_unclosed_independence_boundary():
    registry=json.loads((ROOT/"paper/pirc17/review-response-v1.json").read_text(encoding="utf-8"))
    row=next(x for x in registry["items"] if x["id"]=="P0-03")
    assert row["status"]=="partial" and row["final_review_accepted"] is False
    assert "paper/pirc17/source-sequence-description-v1.json" in row["evidence"]
    assert {"sec:source-sequence-screen","tab:source-sequence-screen"}.issubset(row["manuscript_anchors"])
    assert "443" in row["response"] and "531" in row["response"]
    for limitation in ("参与者", "近似重复路线", "物理时间重叠"):
        assert limitation in row["remaining"]
    assert registry["accepted_items"]==0
    assert registry["all_review_items_or_paper_complete"] is False
