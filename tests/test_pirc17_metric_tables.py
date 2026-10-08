"""Pure metric-to-TeX transport fixtures, not experimental qualification."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

import pytest

from scripts import aggregate_pirc17 as source
from scripts import render_pirc17_metric_tables as module
from scripts import render_pirc17_paper_tables as tex
from tests.test_pirc17_tables import cards, write_cards


def computed(cards):
    value = deepcopy(cards)
    row = value["metric_tables"][0]
    row.update(status="computed", expected_forecasts=5, available_score_rows=5,
               missing_score_rows=0, counts_by_status={"success": 5},
               means={**dict(zip(source.METRICS, [11, 22, 33, 44, 55])),
                      "by_time": [
                          dict(nominal_seconds=t, actual_elapsed_seconds_range=[t - 1, t + 2],
                               energy_score_m=12.3456, position_entropy_nats=2.3456,
                               coverage=[dict(level=level, coverage_rate=.45678,
                                              mean_area_m2=9876.54321)
                                         for level in module.LEVELS])
                          for t in source.SCORING_SECONDS]})
    return value


def test_complete_rows_all_modes_levels_and_synthetic_notice(cards):
    before = deepcopy(cards)
    files, counts, rows = module.fragments(cards, software_fixture=True)
    assert cards == before
    assert len(files) == len(counts) == 18
    assert rows == {key: source.project(cards)[key] for key in ("accuracy", "accuracy_times")}
    assert len(rows["accuracy"]) == 120 and len(rows["accuracy_times"]) == 480
    for language in tex.LANGUAGES:
        for mode in source.MODES:
            for kind, n in [("absolute-quality", 40), ("time-quality", 160), ("time-regions", 640)]:
                path = language + "/" + kind + "-" + mode.replace("_", "-") + ".tex"
                assert counts[path] == n
                text = files[path].decode("utf-8")
                assert "SOFTWARE FIXTURE ONLY" in text
                assert tex.translated(("SOFTWARE FIXTURE ONLY -- no experimental evidence.",
                                       "仅合成软件测试数据，不是实验结果。"), language) in text
                assert r"\endfirsthead" in text and r"\endhead" in text


@pytest.mark.parametrize("language", tex.LANGUAGES)
def test_unavailable_values_and_repeated_denominators_are_not_zero(cards, language):
    files, _, _ = module.fragments(cards)
    absolute = files[language + "/absolute-quality-causal-prefix.tex"].decode("utf-8")
    assert "unavailable" in absolute and tex.tex_text("0 / 0 / 0") in absolute
    assert " & -- & -- & -- & -- & --" in absolute
    regions = files[language + "/time-regions-causal-prefix.tex"].decode("utf-8")
    for level in module.LEVELS:
        assert " & " + tex.number(level) + " & -- & --" in regions
    if language == "en":
        assert "not new independent samples" in files[language + "/time-quality-causal-prefix.tex"].decode("utf-8")
        assert "do not multiply" in regions
        assert "not a statistical superiority claim" in absolute


@pytest.mark.parametrize("language", tex.LANGUAGES)
def test_recorded_numbers_exact_rows_and_units_are_only_formatted(cards, language):
    value = computed(cards)
    before = deepcopy(value)
    files, _, exact = module.fragments(value)
    assert value == before
    expected = source.project(value)
    assert exact["accuracy"] == expected["accuracy"]
    assert exact["accuracy_times"] == expected["accuracy_times"]
    absolute = files[language + "/absolute-quality-causal-prefix.tex"].decode("utf-8")
    assert " & 11 & 22 & 33 & 44 & 55" in absolute
    times = files[language + "/time-quality-causal-prefix.tex"].decode("utf-8")
    assert " & 1 & [59, 62] & 12.35 & 2.346" in times
    regions = files[language + "/time-regions-causal-prefix.tex"].decode("utf-8")
    assert " & 0.95 & 0.4568 & 9877" in regions
    assert tex.tex_text("5 / 5 / 0") in absolute and "success: 5" in absolute
    assert r"\mathrm{m}^2" in regions


@pytest.mark.parametrize("fault", ["missing_level", "duplicate_level", "wrong_level", "unordered_time",
                                  "missing_endpoint", "missing_count", "bool_count", "status_count"])
def test_malformed_metric_views_rejected_not_filled_or_clipped(cards, fault):
    value = computed(cards)
    row = value["metric_tables"][0]
    time = row["means"]["by_time"][0]
    if fault == "missing_level":
        time["coverage"].pop()
    elif fault == "duplicate_level":
        time["coverage"][-1]["level"] = .5
    elif fault == "wrong_level":
        time["coverage"][-1]["level"] = .99
    elif fault == "unordered_time":
        time["actual_elapsed_seconds_range"] = [62, 59]
    elif fault == "missing_endpoint":
        time["actual_elapsed_seconds_range"] = [None, 62]
    elif fault == "missing_count":
        row["available_score_rows"] = 4
    elif fault == "bool_count":
        row["expected_forecasts"] = True
    else:
        row["counts_by_status"] = {"success": 4}
    with pytest.raises(ValueError):
        module.fragments(value)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, "not numeric"])
def test_bad_recorded_metric_types_are_not_normalized(cards, value):
    data = computed(cards)
    data["metric_tables"][0]["means"]["by_time"][0]["energy_score_m"] = value
    with pytest.raises(ValueError):
        module.fragments(data)


def test_existing_failed_score_disposition_has_no_success_subset(cards):
    value = deepcopy(cards)
    row = value["metric_tables"][0]
    row.update(expected_forecasts=5, available_score_rows=5, missing_score_rows=0,
               counts_by_status={"success": 4, "failed": 1})
    files, _, _ = module.fragments(value)
    text = files["en/absolute-quality-causal-prefix.tex"].decode("utf-8")
    assert "failed: 1" in text and "success: 4" in text
    assert tex.tex_text("5 / 5 / 0") in text and " & -- & -- & -- & -- & --" in text


@pytest.mark.parametrize("language", tex.LANGUAGES)
def test_literal_region_percent_cannot_comment_out_caption(cards, language):
    files, _, _ = module.fragments(cards)
    text = files[language + "/time-regions-causal-prefix.tex"].decode("utf-8")
    caption = next(line for line in text.splitlines() if line.startswith(r"\caption{"))
    assert r"95\%" in caption
    assert re.search(r"(?<!\\)%", caption) is None


def test_pinned_manifest_exact_values_and_idempotent_missing_only_output(cards, tmp_path):
    data = computed(cards)
    path = tmp_path / "cards.json"
    sha = write_cards(path, data)
    result = module.generate(path, sha, tmp_path / "out", software_fixture=True)
    assert result == module.generate(path, sha, tmp_path / "out", software_fixture=True)
    root = Path(result["output_directory"])
    record = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    manifest = record["payload"]
    assert record["sha256"] == source.digest(manifest) == result["manifest_sha256"]
    assert manifest["source_cards_sha256"] == sha and manifest["scope"] == data["scope"]
    assert len(manifest["files"]) == 18
    assert manifest["exact_projected_rows"] == {
        key: source.project(data)[key] for key in ("accuracy", "accuracy_times")}
    for name, binding in manifest["files"].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == binding["sha256"]
    for key in ("manuscript_written", "scientific_claim_authorized", "human_accepted"):
        assert manifest[key] is False
    for key in ("new_forecasts", "new_fits", "new_scores", "new_resampling"):
        assert manifest[key] == 0
    with pytest.raises(ValueError, match="pinned"):
        module.generate(path, "0" * 64, tmp_path / "wrong")
    assert not (tmp_path / "wrong").exists()


def test_conflicting_output_is_preserved_without_partial_publication(cards, tmp_path):
    path = tmp_path / "cards.json"
    sha = write_cards(path, cards)
    result = module.generate(path, sha, tmp_path / "out", software_fixture=True)
    root = Path(result["output_directory"])
    protected = root / "en/time-quality-causal-prefix.tex"
    protected.write_text("USER CONTENT", encoding="utf-8")
    absent = root / "zh/absolute-quality-point-only.tex"
    absent.unlink()
    with pytest.raises(ValueError, match="no overwrite"):
        module.generate(path, sha, tmp_path / "out", software_fixture=True)
    assert protected.read_text(encoding="utf-8") == "USER CONTENT"
    assert not absent.exists()


@pytest.mark.parametrize("fault", ["acceptance", "missing_mode", "secondary_tests"])
def test_original_card_scope_checks_still_apply(cards, fault):
    value = deepcopy(cards)
    if fault == "acceptance":
        value["human_accepted"] = True
    elif fault == "missing_mode":
        value["family_evidence"].pop("point_only")
    else:
        value["family_evidence"]["known_velocity"]["method-model-structure"]["hypothesis_tests_performed"] = True
    with pytest.raises(ValueError):
        module.fragments(value)
