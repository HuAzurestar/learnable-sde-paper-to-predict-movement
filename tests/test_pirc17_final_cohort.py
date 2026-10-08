"""Saved metadata and synthetic JSON only; no raw qualification or forecasts."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.describe_pirc17_final_cohort import digest, summarize

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"


def sample_rows():
    reasons = [[], [], [], ["nonpositive-observation-gap", "followup-shorter-than-1800s"],
               ["followup-shorter-than-1800s", "invalid-road-coverage-origin-through-target-end"],
               ["invalid-road-coverage-origin-through-target-end"]]
    return [{"sample_id": f"sample-{i}", "segment_id": f"segment-{i}",
             "independent_block_id": b, "split": "final_eval", "eligible": not r,
             "reasons": r, "window_sha256": None if r else "a" * 64}
            for i, (b, r) in enumerate(zip(("a", "a", "b", "c", "d", "e"), reasons))]


def selection(rows):
    blocks = {r["independent_block_id"] for r in rows if r["eligible"]}
    ordered = sorted(blocks, key=lambda b: (digest(["pirc17-final-block-order-v1", b]), b))
    selected = [{"independent_block_id": b,
                 "sample_id": min(r["sample_id"] for r in rows
                                  if r["eligible"] and r["independent_block_id"] == b),
                 "split": "final_eval"} for b in ordered[:46]]
    return {"selected": selected, "secondary_selected": selected[:6],
            "eligible_block_count": len(blocks), "requested_blocks": 46,
            "selection_sha256": digest(selected)}


def test_nested_counts_and_overlap_do_not_double_count_exclusions():
    rows = sample_rows()
    result = summarize(rows, selection(rows))
    assert result["stages"]["released"] == {"windows": 6, "recording_hash_blocks": 5}
    assert result["stages"]["temporal_support"] == {"windows": 4, "recording_hash_blocks": 3}
    assert result["stages"]["joint_feature_validity"] == {"windows": 3, "recording_hash_blocks": 2}
    assert result["stages"]["selected_primary"] == {"windows": 2, "recording_hash_blocks": 2}
    assert result["mutually_exclusive_exclusions"] == {"coverage_after_temporal": 1, "temporal": 2}
    assert sum(result["first_recorded_reason_counts"].values()) == 3
    assert sum(result["overlapping_reason_counts"].values()) == 5
    assert result["eligible_windows_not_selected_as_origins"] == 1


@pytest.mark.parametrize("kind", ["duplicate", "unknown_reason", "wrong_status", "wrong_split",
                                  "reverse_selection", "wrong_sample", "wrong_secondary", "wrong_blocks"])
def test_changed_dispositions_or_outcome_blind_selection_fail(kind):
    rows = sample_rows()
    frozen = deepcopy(selection(rows))
    if kind == "duplicate":
        rows.append(deepcopy(rows[0]))
    elif kind == "unknown_reason":
        rows[-1]["reasons"] = ["low-performing-forecast"]
    elif kind == "wrong_status":
        rows[-1]["eligible"] = True
    elif kind == "wrong_split":
        rows[0]["split"] = "train"
    elif kind == "reverse_selection":
        frozen["selected"].reverse()
    elif kind == "wrong_sample":
        for row in frozen["selected"]:
            if row["independent_block_id"] == "a":
                row["sample_id"] = "sample-1"
    elif kind == "wrong_secondary":
        frozen["secondary_selected"] = []
    else:
        frozen["eligible_block_count"] += 1
    with pytest.raises(ValueError):
        summarize(rows, frozen)


def test_original_funnel_bindings_arithmetic_and_remaining_limits():
    path = PAPER / "final-cohort-description-v1.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    ledger = json.loads((PAPER / "claim-ledger.json").read_text(encoding="utf-8"))["final_cohort_description"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == ledger["projection_sha256"]
    assert hashlib.sha256((ROOT / data["reader"]).read_bytes()).hexdigest() == data["reader_sha256"]
    assert data["stages"]["released"] == {"windows": 12370, "recording_hash_blocks": 1094}
    assert data["stages"]["temporal_support"] == {"windows": 127, "recording_hash_blocks": 89}
    assert data["stages"]["joint_feature_validity"] == {"windows": 106, "recording_hash_blocks": 73}
    assert sum(data["first_recorded_reason_counts"].values()) + 106 == 12370
    assert sum(data["mutually_exclusive_exclusions"].values()) + 106 == 12370
    assert sum(int(k) * v for k, v in data["eligible_windows_per_block_histogram"].items()) == 106
    assert sum(data["eligible_windows_per_block_histogram"].values()) == 73
    assert data["eligible_blocks_not_selected"] == 27
    assert data["eligible_windows_not_selected_as_origins"] == 60
    assert not data["scope"]["included_excluded_geographic_speed_duration_distributions_available"]
    assert not data["scope"]["original_eligibility_recomputed_from_raw_points"]
    assert data["scope"]["new_fits_forecasts_particle_scores_or_map_queries"] == 0


@pytest.mark.parametrize("language", ["en", "zh"])
def test_bilingual_final_funnel_uses_saved_counts_not_development_or_forecast_counts(language):
    tex = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    assert tex.count(r"\label{sec:final-cohort-funnel}") == 1
    table = tex.split(r"\label{tab:final-cohort-funnel}", 1)[1].split(r"\end{tabular}", 1)[0]
    for numbers in ("12,370 & 1,094", "127 & 89", "106 & 73", "46 & 46"):
        assert numbers + r"\\" in table
    paragraph = tex.split(r"\label{sec:final-cohort-funnel}", 1)[1].split(r"\subsection", 1)[0]
    for number in ("12,243", "12,137", "1,497", "21", "60", "27"):
        assert number in paragraph
    assert ("not 60 failed predictions" if language == "en" else "不是 60 个预测失败") in paragraph
