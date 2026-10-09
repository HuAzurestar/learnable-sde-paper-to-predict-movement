# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Synthetic JSON arithmetic only; no rollout, fitting or scoring."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "pirc17_target_time_reader", ROOT / "scripts/describe_pirc17_target_times.py")
reader = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reader)


def rows():
    return [
        {"configuration": subject, "origin_rank": rank, "seed": seed, "status": "success",
         "matrix": "NEX326-methods", "origin_mode": "causal_prefix", "partition": "final_eval",
         "scientific": True, "independent_block_id": f"block-{rank}",
         "sample_id": f"sample-{rank}", "target_sha256": f"target-{rank}",
         "scores": {"by_time": [{"elapsed_seconds": t + rank % 3 - 1}
                                for t in reader.HORIZONS]}}
        for subject in reader.SUBJECTS for rank in range(46) for seed in reader.SEEDS]


def test_complete_grid_counts_records_once_and_keeps_stop_after_nominal():
    result = reader.summarize(rows())
    assert result["bound_score_rows"] == 690 and result["recording_blocks"] == 46
    assert result["distinct_targets_across_four_slots"] == 184
    assert result["maximum_actual_stop_seconds"] == 1801
    assert result["actual_stops_after_1800_seconds"] == 15
    for profile in result["horizons"]:
        assert profile["recording_blocks"] == 46
        assert (profile["earlier_count"], profile["exact_nominal_count"],
                profile["later_count"]) == (16, 15, 15)
        assert profile["maximum_absolute_offset_seconds"] == 1
    assert not result["scope"]["independent_output_audit_completed"]
    assert not result["scope"]["physical_clock_or_utc_provenance_certified"]


@pytest.mark.parametrize("kind", ["missing", "duplicate", "failed", "secondary",
                                  "wrong_target", "wrong_times", "nonfinite",
                                  "outside_tolerance", "bool_time", "block_reuse"])
def test_incomplete_invalid_or_changed_rows_fail_whole_time_projection(kind):
    values = rows()
    if kind == "missing":
        values.pop()
    elif kind == "duplicate":
        values.append(deepcopy(values[0]))
    elif kind == "failed":
        values[0]["status"] = "failed"
    elif kind == "secondary":
        values[0]["origin_mode"] = "known_velocity"
    elif kind == "wrong_target":
        values[0]["target_sha256"] = "changed"
    elif kind == "wrong_times":
        values[0]["scores"]["by_time"][0]["elapsed_seconds"] += .25
    elif kind == "nonfinite":
        values[0]["scores"]["by_time"][0]["elapsed_seconds"] = float("nan")
    elif kind == "outside_tolerance":
        values[0]["scores"]["by_time"][0]["elapsed_seconds"] = 91
    elif kind == "bool_time":
        values[0]["scores"]["by_time"][0]["elapsed_seconds"] = True
    elif kind == "block_reuse":
        for row in values:
            if row["origin_rank"] == 1:
                row["independent_block_id"] = "block-0"
    with pytest.raises(ValueError):
        reader.summarize(values)


def test_json_reader_rejects_duplicate_keys_and_mismatched_hash(tmp_path):
    path = tmp_path / "metadata.json"
    path.write_text('{"a":1,"a":2}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        reader.read_json(path)
    path.write_text(json.dumps({"a": 1}), encoding="utf-8")
    with pytest.raises(ValueError, match="binding"):
        reader.read_json(path, "0" * 64)
    with pytest.raises(ValueError, match="binding"):
        reader.unpack({"payload": {"a": 1}, "sha256": "0" * 64})


def test_saved_projection_is_complete_bound_and_not_a_time_array_audit():
    paper = ROOT / "paper/pirc17"
    path = paper / "target-time-description-v1.json"
    value = reader.read_json(path)
    ledger = reader.read_json(paper / "claim-ledger.json")["target_time_description"]
    assert reader.hashlib.sha256(path.read_bytes()).hexdigest() == ledger["projection_sha256"]
    assert reader.hashlib.sha256((ROOT / ledger["reader"]).read_bytes()).hexdigest() == ledger["reader_sha256"]
    assert value["bound_score_rows"] == 690 and value["recording_blocks"] == 46
    assert value["distinct_targets_across_four_slots"] == 184
    assert value["input_bindings_sha256"] == reader.BINDINGS_SHA
    assert value["original_stage_sha256"] == reader.STAGE_SHA
    assert value["maximum_actual_stop_seconds"] == 1814
    assert value["actual_stops_after_1800_seconds"] == 13
    for item in value["horizons"]:
        assert item["earlier_count"] + item["exact_nominal_count"] + item["later_count"] == 46
        assert item["minimum_seconds"] <= item["median_seconds"] <= item["maximum_seconds"]
        assert item["maximum_absolute_offset_seconds"] <= 30
    assert not value["scope"]["independent_output_audit_completed"]
    assert not value["scope"]["physical_clock_or_utc_provenance_certified"]
    assert value["scope"]["new_fits_predictions_particle_scores_or_resampling"] == 0
    assert not ledger["all_review_items_or_paper_complete"]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_bilingual_time_table_matches_saved_46_block_summary(language):
    paper = ROOT / "paper/pirc17"
    value = reader.read_json(paper / "target-time-description-v1.json")
    tex = (paper / language / "historical-main-v1.tex").read_text(encoding="utf-8")
    assert tex.count(r"\label{sec:target-times}") == 1
    assert tex.count(r"\label{tab:actual-target-times}") == 1
    table = tex.split(r"\label{tab:actual-target-times}", 1)[1].split(r"\end{tabular}", 1)[0]
    for profile in value["horizons"]:
        values = [profile[k] for k in ("nominal_seconds", "minimum_seconds",
                  "median_seconds", "maximum_seconds", "maximum_absolute_offset_seconds")]
        assert " & ".join(f"{v:g}" for v in values) + r"\\" in table
    description = tex.split(r"\label{sec:target-times}", 1)[1].split(
        ("Every required configuration" if language == "en" else "五个预测种子"), 1)[0]
    assert "1814" in description and "184" in description and "18.3" in description
    assert ("not 690 independent targets" if language == "en" else "不是 690 个独立目标") in description
    assert ("at most one short" if language == "en" else "最多移除一个末端短间隔") in description
    assert (r"10^{-9}" in description) and "30" in description
