"""Describe complete, already-scored primary inertial/Full pairs; never score.

Input hashes bind closed common-score files, not an independent raw-output
audit. Only anonymous aggregate arithmetic is exported. No PSDE imports,
model loads, forecasts, map queries, random draws or significance tests.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

SEEDS = list(range(20260814, 20260819))
MODES = {"causal_prefix": 46, "known_velocity": 6, "point_only": 6}
HORIZONS = [60, 300, 900, 1800]


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def read_bound(path, expected):
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        raise ValueError("explicit lowercase SHA256 required")
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 32 * 1024**2:
        raise ValueError("bounded regular saved JSON required")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("saved file hash mismatch")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate saved JSON key")
            result[key] = value
        return result
    def reject(value):
        raise ValueError("nonfinite saved JSON number")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)


def load_blocks(cache, index_sha256):
    cache = Path(cache).resolve()
    index = read_bound(cache / "progress.json", index_sha256)
    if index["cache_sha256"] != cache.name or len(index["rows"]) != 11368 or len(index["blocks"]) != 58:
        raise ValueError("closed original 11368-row/58-block score index required")
    blocks, identities, shared = [], set(), None
    for binding in index["blocks"].values():
        relative = binding["path"]
        if (not isinstance(relative, str) or "\\" in relative or ":" in relative
                or any(p in {"", ".", ".."} for p in relative.split("/"))):
            raise ValueError("canonical relative score path required")
        path = (cache / relative).resolve()
        if not path.is_relative_to(cache) or path in identities:
            raise ValueError("score path escape or duplicate")
        identities.add(path)
        record = read_bound(path, binding["file_sha256"])
        payload = record["payload"]
        if record["sha256"] != binding["content_sha256"] or digest(payload) != record["sha256"]:
            raise ValueError("common-score content hash mismatch")
        scope = tuple(payload[k] for k in ("protocol_sha256", "execution_sha256",
            "matrix_sha256", "population_sha256", "scoring_inputs_sha256"))
        if shared is None:
            shared = scope
        if (scope != shared or payload["checkpoint_cache_sha256"] != cache.name
                or payload["schema_version"] != "pirc17-formal-common-scores-v1"
                or payload["expected_rows"] != 196 or len(payload["rows"]) != 196):
            raise ValueError("original common-score scope changed")
        blocks.append(payload)
    for mode, count in MODES.items():
        ranks = [b["origin_rank"] for b in blocks if b["origin_mode"] == mode]
        if sorted(ranks) != list(range(count)):
            raise ValueError("entire original mode population required")
    if any(b["origin_mode"] not in MODES for b in blocks):
        raise ValueError("unregistered origin mode")
    return blocks, dict(zip(("protocol_sha256", "execution_sha256", "matrix_sha256",
                            "population_sha256", "scoring_inputs_sha256"), shared))


def finite(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError("finite nonnegative saved metric required")
    return value


def metrics(row, baseline):
    if row["status"] != "success" or row["partition"] != "final_eval":
        raise ValueError("missing/failed selected row; no successful subset")
    scores = row["scores"]
    if (scores["time_weights"] != [.25] * 4 or len(scores["by_time"]) != 4
            or scores["particle_count"] != (1 if baseline else 512)
            or scores["point_estimator"] != ("deterministic_inertial_path" if baseline
                                             else "ensemble_mean_not_best_of_N")):
        raise ValueError("original metric/estimator policy required")
    times = [finite(t["elapsed_seconds"]) for t in scores["by_time"]]
    if times[0] <= 0 or any(a >= b for a, b in zip(times, times[1:])) or any(abs(t - h) > 30 for t, h in zip(times, HORIZONS)):
        raise ValueError("four original ordered target slots required")
    es = [finite(t["energy_score_m"]) for t in scores["by_time"]]
    result = dict(weighted_es_m=finite(row["score_m"]),
                  ade_m=finite(scores["ade_grid_mean_m"]), fde_m=finite(scores["fde_m"]),
                  es_by_time_m=es)
    close = lambda a, b: math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
    if not close(result["weighted_es_m"], mean(es)) or not close(result["weighted_es_m"], scores["time_weighted_energy_score_m"]):
        raise ValueError("saved weighted-score identity mismatch")
    if baseline and (not close(result["weighted_es_m"], result["ade_m"]) or not close(es[-1], result["fde_m"])):
        raise ValueError("point-mass ES must equal displacement error")
    return result, times


def summarize(blocks):
    primary = [b for b in blocks if b["origin_mode"] == "causal_prefix"]
    if sorted(b["origin_rank"] for b in primary) != list(range(46)):
        raise ValueError("all 46 prespecified primary blocks required")
    paired, origins, record_blocks, time_vectors = [], set(), set(), []
    for block in sorted(primary, key=lambda b: b["origin_rank"]):
        base = [r for r in block["rows"] if r["matrix"] == "inertial"]
        full = [r for r in block["rows"] if r["matrix"] == "NEX326-methods" and r["configuration"] == "arm-01/full"]
        if len(base) != 1 or len(full) != 5 or sorted(r["seed"] for r in full) != SEEDS or base[0]["seed"] is not None:
            raise ValueError("one inertial path and all five Full seeds required")
        ref = base[0]
        if ref["scientific"] is not False or any(r["scientific"] is not True for r in full):
            raise ValueError("baseline is not a scientific replication")
        for row in [ref, *full]:
            if (row["origin_rank"] != block["origin_rank"] or row["origin_mode"] != "causal_prefix"
                    or any(row[k] != ref[k] for k in ("origin_id", "sample_id", "independent_block_id", "target_sha256", "context_sha256"))):
                raise ValueError("exact same-origin/target/context pair required")
        if ref["origin_id"] in origins or ref["independent_block_id"] in record_blocks:
            raise ValueError("duplicate primary origin or recording-hash block")
        origins.add(ref["origin_id"]); record_blocks.add(ref["independent_block_id"])
        inertial, times = metrics(ref, True)
        draws = [metrics(row, False) for row in full]
        if any(t != times for _, t in draws):
            raise ValueError("paired actual target times differ")
        time_vectors.append(times)
        average = {k: mean(v[k] for v, _ in draws) for k in ("weighted_es_m", "ade_m", "fde_m")}
        average["es_by_time_m"] = [mean(v["es_by_time_m"][i] for v, _ in draws) for i in range(4)]
        paired.append((inertial, average))
    profiles = []
    for i, name in enumerate(("inertial", "Full")):
        profiles.append(dict(model=name, forecast_rows=46 if i == 0 else 230,
            recording_hash_blocks=46, **{k: mean(p[i][k] for p in paired) for k in ("weighted_es_m", "ade_m", "fde_m")},
            es_by_time_m=[mean(p[i]["es_by_time_m"][t] for p in paired) for t in range(4)]))
    differences = {k: mean(p[1][k] - p[0][k] for p in paired) for k in ("weighted_es_m", "ade_m", "fde_m")}
    return dict(profiles=profiles, full_minus_inertial_m=differences,
        paired_blocks=46, nominal_horizon_seconds=HORIZONS, nominal_target_tolerance_seconds=30,
        actual_target_bounds_seconds=[[min(t[i] for t in time_vectors), max(t[i] for t in time_vectors)] for i in range(4)],
        target_time_vectors_sha256=digest(time_vectors),
        strictly_lower_full_weighted_es_blocks=sum(p[1]["weighted_es_m"] < p[0]["weighted_es_m"] for p in paired),
        aggregation="Average five Full forecast seeds within each block, then equal-weight all46 blocks; inertial is never replicated.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-directory", type=Path, required=True)
    parser.add_argument("--index-sha256", required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    if args.output_directory.exists() and any(args.output_directory.iterdir()):
        raise ValueError("new empty derivative output directory required")
    blocks, scope = load_blocks(args.cache_directory, args.index_sha256)
    result = summarize(blocks)
    result.update(schema_version="pirc17-saved-inertial-primary-description-v1",
        source_score_index_sha256=args.index_sha256, source_cache_sha256=args.cache_directory.name,
        source_scope=scope, auxiliary_inertial_paths_total=58, primary_inertial_paths_used=46,
        primary_full_forecasts_used=230, excluded_support_origins=12,
        new_fits=0, new_forecasts=0, new_particle_scores=0, new_bootstrap_or_tests=0,
        independent_saved_output_audit_completed=False, scientific_claim_authorized=False,
        external_model_superiority_established=False, physical_utc_certified=False,
        participant_independence_established=False,
        interpretation="Post-outcome descriptive saved-score comparison only; lower is better for each reported metric. No confidence interval or significance test. Degenerate point-mass ES equals point error; probabilistic Full ES need not equal ensemble-mean ADE/FDE. Not final audit/cards or a replacement for the original full study.")
    args.output_directory.mkdir(parents=True, exist_ok=True)
    (args.output_directory / "inertial-primary-description-v1.json").write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8", newline="\n")
    with (args.output_directory / "inertial-primary-means.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["model", "forecast_rows", "recording_hash_blocks", "weighted_es_m", "ade_m", "fde_m"])
        writer.writeheader()
        writer.writerows({k: p[k] for k in writer.fieldnames} for p in result["profiles"])
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
