"""Check disclosed inventory arithmetic and manuscript status, not raw outputs."""
from collections import Counter
import json
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"


def inventory():
    return json.loads((PAPER / "terminal-score-inventory-v1.json").read_text(encoding="utf-8"))


def test_complete_registered_inventory_retains_failures_and_reference_denominators():
    data = inventory()
    counts = Counter({(row["matrix"], row["scientific"], row["status"]): row["rows"] for row in data["rows"]})
    assert len(counts) == len(data["rows"]) == 6
    assert counts == {("NEX326-methods", True, "success"): 8118,
                     ("NEX326-methods", True, "failed"): 2,
                     ("terrain", True, "success"): 2897,
                     ("terrain", True, "failed"): 3,
                     ("NEX326-diagnostic", False, "success"): 290,
                     ("inertial", False, "success"): 58}
    assert sum(counts.values()) == data["total_score_rows"] == 11368
    assert data["successful_score_rows"] + data["failed_score_rows"] == 11368
    assert data["closed_blocks"] == data["primary_blocks"] + data["support_blocks"] == 58
    assert data["rows_per_block"] == 5 * (28 + 10 + 1) + 1 == 196
    assert 58 * 196 == 11368
    assert sum(n for (_, scientific, _), n in counts.items() if scientific) == 11020
    assert sum(n for (_, scientific, state), n in counts.items() if scientific and state == "success") == 11015
    assert data["scientific_forecasts_success"] + data["scientific_forecasts_failed"] == data["scientific_forecasts_total"] == 11020
    assert data["scientific_forecasts_nonterminal"] == 0


def test_count_evidence_has_original_closed_score_scope_not_scientific_acceptance():
    data = inventory()
    reference = json.loads((PAPER / "inertial-primary-description-v1.json").read_text(encoding="utf-8"))
    assert data["common_score_index_sha256"] == "fc7c9c4492b962763ecd0f13959a43bf00e2141e74d92273c45cf6ca98e7332f"
    assert data["common_score_cache_sha256"] == "892bb89b1d39d376c69d5a41570ad1655e50fe6950be6442db7f2b2f492c2878"
    assert data["source_scope"] == reference["source_scope"]
    assert data["new_fits_forecasts_scores_resampling_or_map_queries"] == 0
    assert not data["independent_saved_output_audit_completed"]
    assert not data["final_statistics_or_cards_complete"]
    assert not data["human_accepted"]


@pytest.mark.parametrize("language", ["en", "zh"])
def test_opening_distinguishes_terminal_predictions_from_pending_audit(language):
    text = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    opening = text.split(r"\begin{quote}", 1)[1].split(r"\end{quote}", 1)[0]
    assert "11020" in opening and "11015" in opening
    assert "11368" in opening and "58" in opening
    assert ("Pending:" if language == "en" else "未完成：") in opening
    assert ("auxiliary trials" if language == "en" else "辅助试验") in opening
    assert ("saved-output replay" if language == "en" else "保存输出复算") in opening
    assert "remaining original predictions" not in opening
    assert "其余原计划预测" not in opening
    assert text.count(r"\label{tab:terminal-score-inventory}") == 1
    for row in ["8120 & 8118 & 2", "2900 & 2897 & 3", "11020 & 11015 & 5", "11368 & 11363 & 5"]:
        assert row in text


@pytest.mark.parametrize("change", ["alter", "drop", "duplicate"])
def test_a_previously_present_terminal_table_cannot_be_changed_or_hidden(change):
    from scripts.pirc17_document_blocks import assert_preserved_blocks
    original = r"\begin{table}\label{tab:terminal-score-inventory}11015/5\end{table}"
    changed = ([original.replace("11015/5", "11020/0")] if change == "alter" else
               [] if change == "drop" else [original, original])
    with pytest.raises(AssertionError):
        assert_preserved_blocks([original], changed, "table")
