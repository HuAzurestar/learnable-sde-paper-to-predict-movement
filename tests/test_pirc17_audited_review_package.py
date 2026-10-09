# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Actual published aggregate bytes and scope; no new experimental work."""
import csv
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "paper/pirc17/final-results-v1"


def record(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    encoded = json.dumps(data["payload"], sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    assert hashlib.sha256(encoded).hexdigest() == data["sha256"]
    return data["payload"]


@pytest.mark.parametrize("folder,count", [
    ("tables", 16), ("figures", 33), ("paired-runtime-tex", 16), ("metric-tex", 18),
])
def test_complete_original_files_match_immutable_manifest(folder, count):
    directory = PACKAGE / folder
    payload = record(directory / "manifest.json")
    assert len(payload["files"]) == count
    for name, entry in payload["files"].items():
        path = (directory / name).resolve()
        assert path.is_relative_to(directory.resolve())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"], name
    assert payload["human_accepted"] is False
    assert payload["scientific_claim_authorized"] is False


def test_actual_cards_are_bound_to_completed_audit_not_a_fixture():
    payload = record(PACKAGE / "cards.json")
    assert payload["scope"]["analysis_sha256"] == (
        "d1d67a3bf4cd08d46f7e73f0178950b047197275f3f32e29a61f3f699fe5febc")
    assert payload["scope"]["audit_sha256"] == (
        "8ff917ad6db55bb3b058b51412ab2e76154ba8bd38c754dd60829db74e25ec67")
    assert payload["source_export_sha256"] == (
        "29cb892f47301365b3d7b9a2871f3f71d85fe297f7720d0c6489648f8a4d0c50")
    for field in ("human_accepted", "scientific_claim_authorized",
                  "test02_qualification_asserted", "numerically_qualified"):
        assert payload[field] is False
    assert payload["new_fits"] == payload["new_forecasts"] == 0
    forbidden = {"positions_m", "coordinates", "target_xy", "target_positions",
                 "hostname", "artifact_path", "raw_gpx", "particle_arrays"}
    todo = [payload]
    while todo:
        value = todo.pop()
        if isinstance(value, dict):
            assert not forbidden.intersection(value)
            for key, child in value.items():
                if key in {"block_id", "independent_block_id"}:
                    assert child.startswith("block-")
                if key == "origin_id":
                    assert ":block-" in child
                todo.append(child)
        elif isinstance(value, list):
            todo.extend(value)


def test_all_comparisons_and_trials_keep_dispositions_and_denominators():
    with (PACKAGE / "tables/comparisons.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 90
    assert {r["origin_mode"] for r in rows} == {"causal_prefix", "known_velocity", "point_only"}
    primary = [r for r in rows if r["origin_mode"] == "causal_prefix"
               and r["family_id"].startswith("method-")]
    assert len(primary) == 21
    assert sum(r["verdict"] == "equivalent" for r in primary) == 14
    assert sum(r["verdict"] == "inconclusive" for r in primary) == 7
    assert all(r["precision_invariant_verdict"] == "inconclusive" for r in primary)
    terrain = [r for r in rows if r["origin_mode"] == "causal_prefix"
               and r["family_id"].startswith("weighted-es-")]
    assert len(terrain) == 9
    assert all(r["verdict"] == "unavailable" for r in terrain)
    for name, expected in (("runtime_trials.csv", 165), ("runtime_conditions.csv", 30),
                           ("accuracy.csv", 120), ("accuracy_times.csv", 480)):
        with (PACKAGE / "tables" / name).open(encoding="utf-8", newline="") as handle:
            assert len(list(csv.DictReader(handle))) == expected


@pytest.mark.parametrize("language", ["en", "zh"])
def test_current_paper_updates_audit_and_retains_limitations(language):
    text = (ROOT / "paper/pirc17" / language / "historical-main-v1.tex").read_text(encoding="utf-8")
    assert text.count(r"\label{sec:audited-review-update}") == 1
    assert text.count(r"\label{tab:audited-review-delivery}") == 1
    assert text.count(r"\label{fig:audited-method-comparisons}") == 1
    section = text.split(r"\label{sec:audited-review-update}", 1)[1].split(r"\section{", 1)[0]
    for token in ("11368", "11659", "261", "165", "1380", "1379", "1150", "1148",
                  "d1d67a3b", "8ff917ad", "29cb892f", "Isolated cold/warm runtime"):
        assert token in section
    assert "paired-methods-causal_prefix.pdf" in section
    assert ("not certification" if language == "en" else "不认证") in section
    assert ("acceptance" if language == "en" else "验收") in section


@pytest.mark.parametrize("kind,label", [
    ("table", "tab:audited-review-delivery"),
    ("figure", "fig:audited-method-comparisons"),
])
def test_named_addition_keeps_every_original_block_and_becomes_immutable(kind, label):
    from scripts.pirc17_document_blocks import assert_preserved_blocks
    added = rf"\begin{{{kind}}}\label{{{label}}}AUDITED\end{{{kind}}}"
    assert_preserved_blocks(["old-a", "old-b"], ["old-a", added, "old-b"], kind)
    for invalid in (["old-b", added, "old-a"], ["old-a", added, "changed"],
                    ["old-a", added, added, "old-b"], ["old-a", "unknown", "old-b"]):
        with pytest.raises(AssertionError):
            assert_preserved_blocks(["old-a", "old-b"], invalid, kind)
    for invalid in (["old-a", "old-b"], ["old-a", added + "edited", "old-b"]):
        with pytest.raises(AssertionError):
            assert_preserved_blocks(["old-a", added, "old-b"], invalid, kind)
