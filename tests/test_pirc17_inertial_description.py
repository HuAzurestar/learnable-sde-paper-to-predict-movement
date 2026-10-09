"""Synthetic arithmetic/whole-grid checks; never run empirical predictions."""
from copy import deepcopy
import hashlib
import json

import pytest

from scripts import describe_pirc17_inertial as reader


def blocks():
    result = []
    for rank in range(46):
        rows = []
        for seed in [None, *reader.SEEDS]:
            baseline = seed is None
            es = [rank + t + (2 if baseline else 1) for t in range(4)]
            score = sum(es) / 4
            metrics = dict(time_weights=[.25]*4, particle_count=1 if baseline else 512,
                point_estimator="deterministic_inertial_path" if baseline else "ensemble_mean_not_best_of_N",
                by_time=[dict(elapsed_seconds=t, energy_score_m=v) for t, v in zip([60, 300, 900, 1798], es)],
                time_weighted_energy_score_m=score, ade_grid_mean_m=score if baseline else rank+4,
                fde_m=es[-1] if baseline else rank+6)
            rows.append(dict(matrix="inertial" if baseline else "NEX326-methods", configuration="all" if baseline else "arm-01/full",
                origin_rank=rank, origin_mode="causal_prefix", seed=seed, scientific=not baseline,
                origin_id=f"origin{rank}", sample_id=f"sample{rank}", independent_block_id=f"record{rank}",
                target_sha256=f"target{rank}", context_sha256=f"context{rank}", partition="final_eval",
                status="success", scores=metrics, score_m=score))
        result.append(dict(origin_mode="causal_prefix", origin_rank=rank, rows=rows))
    return result


def test_equal_block_arithmetic_does_not_replicate_baseline_or_confuse_metrics():
    value = reader.summarize(blocks())
    assert [p["forecast_rows"] for p in value["profiles"]] == [46, 230]
    assert value["paired_blocks"] == 46
    assert value["full_minus_inertial_m"] == {"weighted_es_m": -1, "ade_m": .5, "fde_m": 1}
    assert value["strictly_lower_full_weighted_es_blocks"] == 46
    assert "inertial is never replicated" in value["aggregation"]


@pytest.mark.parametrize("change", ["missing_block", "duplicate_rank", "missing_seed", "duplicate_seed", "failed_baseline", "failed_full",
    "wrong_target", "wrong_context", "wrong_origin", "duplicate_record", "wrong_times", "outside_original_tolerance", "nan", "wrong_weights", "replicated_point_mass", "wrong_point_identity"])
def test_invalid_complete_pair_is_refused_not_dropped_or_zero_filled(change):
    data = deepcopy(blocks())
    rows = data[0]["rows"]
    if change == "missing_block": data.pop()
    elif change == "duplicate_rank": data[-1]["origin_rank"] = 0
    elif change == "missing_seed": rows.pop()
    elif change == "duplicate_seed": rows[-1]["seed"] = rows[-2]["seed"]
    elif change == "failed_baseline": rows[0]["status"] = "failed"
    elif change == "failed_full": rows[1]["status"] = "failed"
    elif change == "wrong_target": rows[1]["target_sha256"] = "other"
    elif change == "wrong_context": rows[1]["context_sha256"] = "other"
    elif change == "wrong_origin": rows[1]["origin_id"] = "other"
    elif change == "duplicate_record":
        for row in data[-1]["rows"]: row["independent_block_id"] = "record0"
    elif change == "wrong_times": rows[1]["scores"]["by_time"][-1]["elapsed_seconds"] = 1797
    elif change == "outside_original_tolerance": rows[0]["scores"]["by_time"][0]["elapsed_seconds"] = 91
    elif change == "nan": rows[0]["score_m"] = float("nan")
    elif change == "wrong_weights": rows[0]["scores"]["time_weights"] = [.1,.2,.3,.4]
    elif change == "replicated_point_mass": rows[0]["scores"]["particle_count"] = 5
    elif change == "wrong_point_identity": rows[0]["scores"]["fde_m"] += 1
    with pytest.raises(ValueError): reader.summarize(data)


def test_secondary_origins_are_not_promoted_into_the_primary_population():
    data = blocks()
    data.append(dict(origin_mode="known_velocity", origin_rank=0, rows=[]))
    assert reader.summarize(data) == reader.summarize(blocks())


def test_actual_targets_later_than_nominal_remain_valid_under_original_30s_rule():
    data = blocks()
    for row in data[0]["rows"]:
        row["scores"]["by_time"][0]["elapsed_seconds"] = 67
        row["scores"]["by_time"][-1]["elapsed_seconds"] = 1814
    result = reader.summarize(data)
    assert result["actual_target_bounds_seconds"][-1] == [1798, 1814]
    assert result["nominal_target_tolerance_seconds"] == 30


def test_json_hash_and_duplicate_keys_are_checked(tmp_path):
    path = tmp_path / "saved.json"
    raw = b'{"a":1,"a":2}'
    path.write_bytes(raw)
    with pytest.raises(ValueError, match="duplicate"):
        reader.read_bound(path, hashlib.sha256(raw).hexdigest())
    with pytest.raises(ValueError, match="hash mismatch"):
        reader.read_bound(path, "0"*64)


def test_incomplete_closed_cache_cannot_be_consumed(tmp_path):
    path = tmp_path / "progress.json"
    raw = json.dumps(dict(cache_sha256=tmp_path.name, rows={}, blocks={})).encode()
    path.write_bytes(raw)
    with pytest.raises(ValueError, match="11368-row/58-block"):
        reader.load_blocks(tmp_path, hashlib.sha256(raw).hexdigest())


def test_actual_anonymous_projection_matches_existing_full_and_target_clock_descriptions():
    from pathlib import Path
    paper = Path(__file__).resolve().parents[1] / "paper/pirc17"
    result = json.loads((paper / "inertial-primary-description-v1.json").read_text(encoding="utf-8"))
    stage = json.loads((paper / "preliminary-method-statistics-v1.json").read_text(encoding="utf-8"))
    original = next(row for row in stage["configs"] if row["configuration"] == "arm-01/full")
    full = result["profiles"][1]
    assert all(full[key] == original[key] for key in ("weighted_es_m", "ade_m", "fde_m", "es_by_time_m"))
    clock = json.loads((paper / "target-time-description-v1.json").read_text(encoding="utf-8"))
    assert result["target_time_vectors_sha256"] == clock["target_time_vectors_sha256"]
    assert result["paired_blocks"] == 46 and result["primary_inertial_paths_used"] == 46
    assert result["auxiliary_inertial_paths_total"] == 58 and result["excluded_support_origins"] == 12
    assert not result["independent_saved_output_audit_completed"]
    assert not result["scientific_claim_authorized"]
    assert all(result[key] == 0 for key in ("new_fits", "new_forecasts", "new_particle_scores", "new_bootstrap_or_tests"))
    assert hashlib.sha256((paper / "inertial-primary-description-v1.json").read_bytes()).hexdigest() == "80725a94a86bcd58d1bc71f8698221eee5c17e0276e14109425ecdac69f9eb82"


def test_reader_cannot_import_prediction_or_random_draw_code():
    import ast
    from pathlib import Path
    source = Path(reader.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import): roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom): roots.add(node.module.split(".")[0])
    assert roots == {"__future__", "argparse", "csv", "hashlib", "json", "math", "pathlib", "statistics"}
