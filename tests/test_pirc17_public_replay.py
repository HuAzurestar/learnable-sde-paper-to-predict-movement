"""Closed projection boundaries, not synthetic empirical qualification."""
import ast
from dataclasses import is_dataclass
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "pirc17_public_replay", ROOT / "scripts/replay_pirc17_public.py")
REPLAY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPLAY)


def test_exact_closed_source_set_includes_policy_and_every_read_dependency():
    pins = REPLAY.SOURCE_PINS
    assert len(pins) == 23
    assert all(len(h) == 64 and set(h) <= set("0123456789abcdef") for h in pins.values())
    for path in ("experiments/pirc17/formal_export.py",
                 "experiments/pirc17/inference.py",
                 "experiments/pirc17/inference_guard.py",
                 "experiments/pirc17/decision_policy.py",
                 "experiments/pirc17/plans/pre-evaluation-decision-policy-v1.json",
                 "experiments/pirc17/evidence/closed-qualification-v1.json",
                 "experiments/pirc17/plans/full-delivery-policy-v1.json",
                 "experiments/nex326/experiment.json",
                 "experiments/nex326/model.py"):
        assert path in pins


def test_all_hashes_verified_before_any_compiled_definition(tmp_path, monkeypatch):
    source = tmp_path / "source.py"
    source.write_text("raise RuntimeError('must never execute')", encoding="utf-8")
    monkeypatch.setattr(REPLAY, "SOURCE_PINS", {"source.py": "0" * 64})
    monkeypatch.setattr(REPLAY, "_project", lambda *a, **k: pytest.fail("executed changed source"))
    with pytest.raises(ValueError, match="frozen public source differs"):
        REPLAY.load_engine(tmp_path)


def test_source_cannot_escape_explicit_repository(tmp_path, monkeypatch):
    monkeypatch.setattr(REPLAY, "SOURCE_PINS", {"../outside.py": "0" * 64})
    with pytest.raises(ValueError, match="source escapes"):
        REPLAY.verify_sources(tmp_path)


def test_projection_uses_original_body_and_omits_backend_and_cli_execution(tmp_path):
    raw = b"import absent_production_backend\nBASE = 7\ndef keep(x):\n    return x + BASE + supplied\ndef forecast():\n    raise RuntimeError('forbidden')\nraise RuntimeError('CLI must not execute')\n"
    projected = REPLAY._project(tmp_path, {"experiments/pirc17/unit.py": raw},
                               "unit", {"BASE", "keep"}, {"supplied": 2})
    assert projected.keep(3) == 12
    assert not hasattr(projected, "forecast")
    assert projected.keep.__code__.co_filename == "experiments/pirc17/unit.py"
    assert not hasattr(projected, "absent_production_backend")


def test_projection_missing_declared_definition_is_hard_failure(tmp_path):
    with pytest.raises(ValueError, match="selection differs"):
        REPLAY._project(tmp_path, {"experiments/pirc17/unit.py": b"OTHER = 1"},
                        "unit", {"BASE"})


def test_original_dataclass_decoration_has_real_module_identity(tmp_path):
    raw = b"from __future__ import annotations\nfrom dataclasses import dataclass\n@dataclass(frozen=True)\nclass Config:\n    count: int = 5\n"
    projected = REPLAY._project(tmp_path, {"experiments/pirc17/config.py": raw},
                               "config", {"Config"})
    assert is_dataclass(projected.Config)
    assert projected.Config().count == 5


def test_existing_output_rejected_before_input_reads(tmp_path, monkeypatch):
    monkeypatch.setattr(REPLAY, "load_engine", lambda *a: pytest.fail("read sources"))
    with pytest.raises(ValueError, match="never overwrite"):
        REPLAY.replay(tmp_path, tmp_path, tmp_path)


def test_input_reader_must_match_external_pin_before_loading(tmp_path, monkeypatch):
    wrapper = tmp_path / "replay_pirc17_public.py"
    monkeypatch.setattr(REPLAY, "__file__", str(wrapper))
    reader = wrapper.with_name("pirc17_replay_input.py")
    reader.write_text("raise RuntimeError('changed reader executed')", encoding="utf-8")
    with pytest.raises(ValueError, match="package reader differs"):
        REPLAY.read_input(tmp_path)


def test_statistics_are_not_reimplemented_or_experimentally_reconfigured():
    text = (ROOT / "scripts/replay_pirc17_public.py").read_text(encoding="utf-8")
    functions = {n.name for n in ast.parse(text).body if isinstance(n, ast.FunctionDef)}
    assert not functions & {"infer", "infer_guarded", "paired_family", "paired_blocks", "planning_power"}
    assert '"policy_generation_rerun": False' in text
    assert '"full_table_figure_pdf_rebuild_verified": False' in text
    assert REPLAY.NUMPY_VERSION == "1.26.4"
    assert REPLAY.POLICY_CONTENT == "d78238790bbf4486fc26946574640f819afbf8b6dcbdeb65d6215266a8d36177"
    path = ROOT / "scripts/pirc17_replay_input.py"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == REPLAY.PACKAGE_READER_SHA256


def test_actual_published_receipt_binds_current_loader_and_complete_result():
    receipt = json.loads((ROOT / "paper/pirc17/public-paired-replay-v1/receipt.json").read_bytes())
    assert receipt["source_file_sha256"] == REPLAY.SOURCE_PINS
    assert receipt["projection_loader_sha256"] == hashlib.sha256(
        (ROOT / "scripts/replay_pirc17_public.py").read_bytes()).hexdigest()
    assert (receipt["score_rows"], receipt["metric_views"], receipt["comparisons"]) == (11368, 120, 90)
    assert receipt["recomputed_matches_original"] is True
    assert receipt["fixed_statistical_rng_streams_replayed"] is True
    assert receipt["result_content_sha256"] == "17202930fbcbb18c735ae8ef41dcd6030b2f26b04ac9debd1c274c2716f510f4"


def test_arithmetic_receipt_cannot_close_scientific_or_full_paper_scope():
    receipt = json.loads((ROOT / "paper/pirc17/public-paired-replay-v1/receipt.json").read_bytes())
    for key in ("human_accepted", "scientific_claim_authorized",
                "full_table_figure_pdf_rebuild_verified", "raw_trajectory_or_map_inputs_read",
                "production_modules_imported", "policy_generation_rerun"):
        assert receipt[key] is False
    for key in ("new_forecasts", "new_fits", "new_particle_scores"):
        assert receipt[key] == 0
