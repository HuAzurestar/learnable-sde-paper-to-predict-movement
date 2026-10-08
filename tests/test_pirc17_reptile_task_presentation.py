"""Existing-label task counts and paper checks, not meta-learning qualification."""
import hashlib
import json
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"
PATH = PAPER / "reptile-task-description-v1.json"
D = json.loads(PATH.read_text(encoding="utf-8"))
L = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))


def test_complete_original_groups_and_repeated_exposure_not_distinct_samples():
    assert D["all_training_groups"] == dict(label_groups=84, segments=328, transitions_per_pass=26009)
    assert D["eligible_tasks"] == dict(label_groups=30, segments=258, transitions_per_pass=20029)
    assert D["ineligible_small_groups"] == dict(label_groups=54, segments=70, transitions_per_pass=5980)
    assert D["training_label_source_segments"] == {"city": 328}
    for key in ("label_groups", "segments", "transitions_per_pass"):
        assert D["eligible_tasks"][key] + D["ineligible_small_groups"][key] == D["all_training_groups"][key]
    assert D["exposure_reconciliation"] == dict(global_initialization=26009, repeated_meta_tasks=80116, target_adaptation=5762, total=111887)
    assert D["task_visits"] == 120 and D["inner_steps"] == 5 and D["outer_epochs"] == 4


def test_all30_tasks_and_rank_cardinalities_are_not_transition_frequencies():
    tasks = D["tasks"]
    assert [t["task"] for t in tasks] == [f"T{i:02d}" for i in range(1,31)]
    assert sum(t["segments"] for t in tasks) == 258
    assert sum(t["transitions_per_pass"] for t in tasks) == 20029
    assert min(t["segments"] for t in tasks) == 3 and max(t["segments"] for t in tasks) == 75
    assert min(t["transitions_per_pass"] for t in tasks) == 177 and max(t["transitions_per_pass"] for t in tasks) == 5324
    assert D["eligible_task_size_histogram"]["3"] == 10
    for t in tasks:
        k = t["segments"]
        assert t["segment_rank_cardinalities"] == [sum(min(2,3*r//k)==m for r in range(k)) for m in range(3)]
    assert [sum(t["segment_rank_cardinalities"][m] for t in tasks) for m in range(3)] == [94,86,78]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_bilingual_complete_task_table_and_main_group_definition(language):
    tex = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    for label in ("sec:reptile-task-accounting", "tab:reptile-task-accounting"):
        assert tex.count(r"\label{"+label+"}") == 1
    at = tex.index(r"\label{tab:reptile-task-accounting}")
    assert at > tex.index(r"\appendix")
    table = tex[at:tex.index(r"\end{longtable}", at)]
    for t in D["tasks"]:
        cells = [t["task"], str(t["segments"]), f"{t['transitions_per_pass']:,}"] + [str(x) for x in t["segment_rank_cardinalities"]]
        assert " & ".join(cells)+r"\\" in table
    assert "258 & 20,029 & 94 & 86 & 78" in table
    assert r"\endfirsthead" in table and r"\endhead" in table
    main = tex.split(r"\appendix",1)[0]
    assert r"\ref{sec:reptile-task-accounting}" in main
    for value in ("328", "84", "30", "258", "20,029", "54", "70", "5,980"):
        assert value in main
    for en, zh in (("without\na country key or case normalization", "不含国家键、不统一大小写"),
                   ("remain in the global\ninitialization", "仍参与全局初始化"),
                   ("not 120\nindependent held-out studies", "不是120个独立留出研究"),
                   ("not every reuse by five inner", "不枚举五个内步")):
        assert (en if language=="en" else zh) in tex
    assert "\n+" not in tex


def test_same_saved_reptile_model_inventory_and_counter():
    previous = json.loads((PAPER / "method-algorithm-description-v1.json").read_text(encoding="utf-8"))
    row = next(r for r in previous["methods"] if r["representative_slot"] == "arm-14/reptile")
    assert D["bindings"]["inventory_sha256"] == previous["inventory_sha256"]
    assert D["bindings"]["original_record_file_sha256"] == row["original_record_sha256"]
    assert D["eligible_tasks"]["label_groups"] == row["meta_task_count"]
    assert D["bindings"]["training_source_recordings"] == 266
    assert D["bindings"]["source_sha256"]["experiments/nex326/pirc20_adapter.py"] == "d9f82c905d299cb040157f1bbfb9995c3a197495abc756d1e29ee91fdccc25eb"


def test_metadata_only_no_new_labels_fits_predictions_or_qualification():
    scope = D["scope"]
    assert scope["source_columns_decoded"] == ["file_id","city","region"]
    assert scope["training_segments"] == 328
    for field in ("original_source_labels_constant_within_used_recordings_verified", "small_groups_remain_in_global_initialization",
                  "label_membership_reconciled_from_original_records_not_new_training", "task_groups_are_not_certified_cities_regions_participants_or_independent_samples"):
        assert scope[field]
    for field in ("intermediate_parameters_or_gmm_residual_labels_recovered", "final_mixture_probabilities_inverted_to_transition_frequencies",
                  "coordinates_clocks_speeds_predictions_or_scientific_scores_decoded_from_source", "new_experimental_qualification_or_final_acceptance",
                  "independent_saved_output_audit_completed", "raw_labels_segment_file_ids_private_paths_or_coefficients_exported", "all_review_items_or_paper_complete"):
        assert not scope[field]
    assert scope["new_fits_forecasts_scores_resampling_or_map_queries"] == 0


def test_projection_pin_and_existing_missing_labels_flags_not_overwritten():
    entry = L["original_reptile_task_description"]
    assert entry["projection_sha256"] == hashlib.sha256(PATH.read_bytes()).hexdigest()
    assert entry["membership_identity_sha256"] == D["membership_identity_sha256"]
    assert entry["eligible_within_task_segment_rank_cardinality_totals"] == [94,86,78]
    assert not entry["training_counter_counts_every_inner_step_or_validation_access"]
    old = json.loads((PAPER / "mode-partition-description-v1.json").read_text(encoding="utf-8"))
    assert not old["scope"]["actual_segment_labels_or_multimode_transition_frequencies_recovered"]
    assert not old["scope"]["gmm_residual_partitions_reconstructed"]
    assert not L["final_empirical_results_integrated"] and not L["human_accepted"]


def test_no_raw_labels_members_paths_or_coefficients_exported():
    text = PATH.read_text(encoding="utf-8")
    for key in ("segment_id", "file_id", "weights", "absolute_epoch_ns", "longitude", "latitude"):
        assert json.dumps(key)+":" not in text
    # A source-kind count named city is public aggregate metadata, not a place.
    def check(value, path=()):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"city", "region"}:
                    assert path == ("training_label_source_segments",) and type(item) is int
                check(item, path+(key,))
        elif isinstance(value, list):
            for item in value: check(item, path)
    check(D)
    assert all(drive+chr(58)+chr(92) not in text for drive in ("C","E"))
