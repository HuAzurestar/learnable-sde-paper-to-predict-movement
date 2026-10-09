# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Saved-count reconciliation regressions; not individual output auditing."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.describe_pirc17_capture_difference import reconcile

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"


def fixture():
    stage = json.loads((PAPER / "preliminary-method-statistics-v1.json").read_text(encoding="utf-8"))
    later = json.loads((PAPER / "execution-coverage-20261006-v1.json").read_text(encoding="utf-8"))
    saved = json.loads((PAPER / "capture-count-reconciliation-v1.json").read_text(encoding="utf-8"))
    earlier = dict(saved["earlier_capture"], cache_sha256=stage["cache_sha256"],
                   configurations=[dict(matrix=r["matrix"], origin_mode=r["origin_mode"],
                                        configuration=r["configuration"], expected=r["expected"],
                                        counts={k: r["earlier"][k] for k in ("success", "failed")},
                                        missing=r["earlier"]["missing"])
                                   for r in saved["configurations"]])
    return stage, earlier, later


def test_all_114_count_cells_reproduce_saved_net_difference_without_claiming_item_sets():
    result = reconcile(*fixture())
    saved = json.loads((PAPER / "capture-count-reconciliation-v1.json").read_text(encoding="utf-8"))
    assert result == {k: v for k, v in saved.items() if k != "source_file_sha256"}
    assert result["net_success_count_change"] == 130
    assert result["changed_count_cells"] == 22
    assert result["method_count_cells_unchanged"]
    assert [g["net_success_count_change"] for g in result["matrix_modes"]] == [0, 0, 0, 57, 8, 65]
    assert not result["individual_work_id_sets_retained_in_these_sources"]
    assert not result["individual_identity_difference_reconstructed"]
    assert not result["no_replacements_within_a_cell_established"]
    assert not result["independent_saved_output_audit_completed"]
    assert not result["original_method_statistics_changed"]
    assert result["new_forecasts_fits_scores_resampling_or_map_queries"] == 0


def test_existing_input_and_generator_bytes_match_saved_source_bindings():
    saved = json.loads((PAPER / "capture-count-reconciliation-v1.json").read_text(encoding="utf-8"))
    for name, path in (("stage", PAPER / "preliminary-method-statistics-v1.json"),
                       ("execution_summary", PAPER / "execution-coverage-20261006-v1.json"),
                       ("generator", ROOT / "scripts/describe_pirc17_capture_difference.py")):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == saved["source_file_sha256"][name]
    stage = json.loads((PAPER / "preliminary-method-statistics-v1.json").read_text(encoding="utf-8"))
    assert saved["source_file_sha256"]["scoring_summary"] == stage["private_derivative_file_sha256"]


@pytest.mark.parametrize("bad", ["duplicate", "missing", "settings", "stage_index", "capture_order",
                                "denominator", "boolean", "negative", "unknown_status", "unaligned_index"])
def test_incomplete_or_misaligned_saved_counts_fail_whole_reconciliation(bad):
    stage, earlier, later = copy.deepcopy(fixture())
    if bad == "duplicate": earlier["configurations"][0] = earlier["configurations"][1]
    if bad == "missing": later["configurations"].pop()
    if bad == "settings": later["settings_id"] = "different"
    if bad == "stage_index": earlier["score_index_sha256"] = "different"
    if bad == "capture_order": later["captured_utc"] = earlier["captured_utc"]
    if bad == "denominator": earlier["configurations"][0]["expected"] -= 1
    if bad == "boolean": earlier["configurations"][0]["missing"] = False
    if bad == "negative": earlier["configurations"][0]["missing"] = -1
    if bad == "unknown_status": earlier["configurations"][0]["counts"]["invalid"] = 1
    if bad == "unaligned_index": later["configurations"][0]["score_index_success"] -= 1
    with pytest.raises(ValueError): reconcile(stage, earlier, later)


@pytest.mark.parametrize("language", ["en", "zh"])
def test_bilingual_count_table_and_membership_limitation_remain_in_appendix(language):
    text = (PAPER / language / "historical-main-v1.tex").read_text(encoding="utf-8")
    at = text.index(r"\label{tab:capture-count-difference}")
    assert at > text.index(r"\appendix")
    end = text.index(r"\end{tabular}", at)
    table = text[at:end]
    for pair in ("1974 & 2031 & 57", "292 & 300 & 8", "0 & 65 & 65", "10384 & 10514 & 130"):
        assert pair in table
    assert "capture-count-reconciliation-v1.json" in text
    assert "membership replacement" in text if language == "en" else "成员替换" in text
