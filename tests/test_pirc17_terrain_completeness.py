"""Saved status/count disclosure, not raw-output audit or terrain inference."""
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"


def projection():
    return json.loads((PAPER / "terrain-family-completeness-v1.json").read_text(encoding="utf-8"))


def test_whole_registered_families_and_shared_baseline_are_counted_once():
    data = projection()
    assert data["recording_hash_blocks"] == 46
    assert data["forecast_seeds"] == list(range(20260814, 20260819))
    primary, lio = data["families"]
    assert primary["family"] == "weighted-es-primary"
    assert lio["family"] == "weighted-es-lio"
    assert set(primary["configurations"]) == {"all-terrain", "base", "loo-road", "loo-river", "loo-worldcover", "loo-surface"}
    assert set(lio["configurations"]) == {"base", "lio-road", "lio-river", "lio-worldcover", "lio-surface"}
    for row, success, failures in ((primary, 1379, 1), (lio, 1148, 2)):
        assert row["required_rows"] == 46 * 5 * len(row["configurations"])
        assert row["missing_rows"] == 0
        assert row["successful_rows"] == success
        assert row["failed_rows"] == failures == len(row["failed_configurations"])
        assert success + failures == row["required_rows"]
        assert row["disposition"] == "unavailable_entire_registered_family"
    assert set(primary["configurations"]) & set(lio["configurations"]) == {"base"}
    assert data["shared_baseline_rows"] == 46 * 5 == 230
    assert data["distinct_union_rows"] == 1380 + 1150 - 230 == 2300
    assert data["distinct_union_successful_rows"] == 1379 + 1148 - 230 == 2297
    assert data["distinct_union_failed_rows"] == 3


def test_original_closed_score_scope_and_failure_policy_are_not_promoted():
    data = projection()
    inventory = json.loads((PAPER / "terminal-score-inventory-v1.json").read_text(encoding="utf-8"))
    failures = json.loads((PAPER / "failure-description-v1.json").read_text(encoding="utf-8"))
    for key in ("common_score_index_sha256", "common_score_cache_sha256", "source_scope"):
        assert data[key] == inventory[key]
    # Original byte binding remains literal. The approved public anonymous
    # copy has different whitespace, so also verify the exact JSON content.
    assert data["failure_description_sha256"] == "3d9167511b546c1496b8bc4b644264f920b78120bc49678ec7ab9953151a8d26"
    canonical = json.dumps(failures, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    assert hashlib.sha256(canonical).hexdigest() == data["failure_description_content_sha256"]
    assert hashlib.sha256((ROOT / data["shared_closed_score_reader"]).read_bytes()).hexdigest() == data["shared_closed_score_reader_sha256"]
    for path, expected in data["original_registry_source_sha256"].items():
        assert failures["source_sha256"][path] == expected
    dispositions = {r["family"]: r for r in failures["unavailable_families"] if r["origin_mode"] == "causal_prefix"}
    for row in data["families"]:
        old = dispositions[row["family"]]
        assert row["disposition"] == old["disposition"]
        assert row["failed_rows"] == len(old["failed_labels"])
        assert not old["successful_subset_inference_allowed"]
    assert data["families"][0]["failed_configurations"] == [{"configuration": "all-terrain", "seed": 20260815}]
    assert data["families"][1]["failed_configurations"] == [{"configuration": "lio-river", "seed": 20260817}, {"configuration": "lio-road", "seed": 20260814}]
    assert data["new_fits_forecasts_scores_resampling_or_map_queries"] == 0
    for field in ("raw_trajectories_or_prediction_arrays_opened", "successful_subset_inference_allowed",
                  "independent_saved_output_audit_completed", "final_statistics_or_cards_complete",
                  "scientific_claim_authorized", "human_accepted"):
        assert data[field] is False
    forbidden = {"origin_id", "sample_id", "independent_block_id", "forecast_work_id", "coordinates", "elapsed_seconds"}
    def check_keys(value):
        if isinstance(value, dict):
            assert not forbidden.intersection(value)
            for child in value.values(): check_keys(child)
        elif isinstance(value, list):
            for child in value: check_keys(child)
    check_keys(data)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_current_main_terrain_explanation_does_not_repeat_historical_missingness(language):
    text = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    terrain = text.split(r"\label{sec:terrain-results}", 1)[1].split(r"\paragraph", 1)[0]
    for value in ("1380", "1379", "1150", "1148", "2300", "2297", "230"):
        assert value in terrain
    assert "terrain-family-completeness-v1.json" in terrain
    assert ("none missing" if language == "en" else "0 缺项") in terrain
    assert ("dated snapshot" if language == "en" else "历史快照") in terrain
    assert ("do not establish" if language == "en" else "不能确立") in terrain
    assert ("completed auxiliary trials" if language == "en" else "现已完成的辅助试验或保存输出审计") in terrain
    assert ("do not replace failed forecasts or restore these comparisons" if language == "en" else "不会替换失败预测或恢复这些比较") in terrain
    assert ("pending audit" if language == "en" else "尚待执行的审计") not in terrain
    assert "has 160 missing" not in terrain and "缺评分索引 160" not in terrain
    # The historical execution table remains available and unchanged.
    assert ("1380 & 1219 & 160 & 1" in text and "1150 & 1017 & 131 & 2" in text)
