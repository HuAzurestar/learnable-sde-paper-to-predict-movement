"""Bind manuscript ES to original execution bytes, never re-score research data."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"
PINS = {"experiments/pirc17/metrics.py": "c00059e40421d5267deb35b73096048f22fd439dc9914801ccaf4fd609885570",
        "experiments/pirc17/formal_scoring.py": "d39adc6de097cd792c5742beca8bc3ebaab1fa5151804e5fe1ac813134170187"}
EXECUTION = "c3e44393f6bc5544aaa21bb273c94eaecb9d0becb4e0590771355c4c0be9b6c2"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def record(psde, bundle, runtime):
    value = json.loads(bundle.read_text(encoding="utf-8"))
    assert digest(value["payload"]) == value["sha256"]
    execution = value["payload"]["execution"]
    assert digest(execution["payload"]) == execution["sha256"] == EXECUTION
    settings = json.loads((runtime / "settings.json").read_text(encoding="utf-8"))
    assert settings["execution_sha256"] == EXECUTION
    assert digest({k: v for k, v in settings.items() if k != "settings_id"}) == settings["settings_id"]
    sources = {}
    for path, pin in PINS.items():
        raw = (psde / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == pin == execution["payload"]["source_sha256"]["PSDE-SDE/"+path]
        sources[path] = raw.decode("utf-8")
    metrics = sources["experiments/pirc17/metrics.py"]
    functions = {n.name: n for n in ast.parse(metrics).body if isinstance(n, ast.FunctionDef)}
    path_calls = {n.func.id for n in ast.walk(functions["score_path"]) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "energy_score" in path_calls
    assert "score_path(" in sources["experiments/pirc17/formal_scoring.py"]
    replay = json.loads((PAPER / "public-paired-replay-v1/receipt.json").read_text(encoding="utf-8"))
    assert replay["source_file_sha256"]["experiments/pirc17/metrics.py"] == PINS["experiments/pirc17/metrics.py"]
    projection = "\n\n".join(ast.get_source_segment(metrics, functions[n]) for n in ("_samples", "energy_score"))
    output = dict(schema_version="pirc17-es-definition-binding-v2", execution_content_sha256=EXECUTION,
                  original_bundle_content_sha256=value["sha256"], source_file_sha256=PINS,
                  runtime_settings_content_sha256=settings["settings_id"],
                  original_public_replay_receipt_sha256=hashlib.sha256((PAPER / "public-paired-replay-v1/receipt.json").read_bytes()).hexdigest(),
                  call_chain=["ScoringConsumers", "score_path", "energy_score"],
                  estimator="ordered-pair U statistic; 2*N*(N-1); zero diagonal",
                  deterministic_reference="direct point-mass distance, not N=1 in the U formula",
                  metric_source_projection=projection,
                  correction="Previous body and checklist N^2 wording was wrong; scientific results remain unchanged.",
                  original_arrays_rescored=False, new_research_scores=0, new_fits_forecasts_or_resampling=0,
                  human_accepted=False)
    destination = PAPER / "reader-v2-score-binding.json"
    if destination.exists():
        raise ValueError("Versioned score binding already exists")
    destination.write_text(json.dumps(output, indent=2)+"\n", encoding="utf-8")
    print("ES call chain matches original execution and public replay source pins.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("psde", "bundle", "runtime"):
        parser.add_argument("--"+name, type=Path, required=True)
    record(**vars(parser.parse_args()))
