"""Anonymous point-error arithmetic from saved centers and original targets.

No particles, models, maps, raw trajectories, new forecasts or random draws.
This is not the original independent saved-output audit or new inference.
The entire original three-configuration primary grid and inertial reference
must match; missing or inconsistent inputs refuse the whole description.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

from scripts.describe_pirc17_inertial import HORIZONS, SEEDS, digest, read_bound, load_blocks

SUBJECTS = ("arm-01/full", "arm-04/gmm_kernel", "arm-06/dt300")
MODELS = ("Full", "GMM", "dt300", "Inertial")
CONTEXT_SHA = "61354e87858d8dc54e2759e3b11f2501000e27ca9b2898115d72018b2f051f4f"
CONTEXT_FILE_SHA = "7876e24357b1434d9b60fec72dc0b3d66095c816c196f4b3bbb1ab4bc652aff6"
INDEX_SHA = "fc7c9c4492b962763ecd0f13959a43bf00e2141e74d92273c45cf6ca98e7332f"


def unpack(record, expected):
    if (not isinstance(record, dict) or set(record) != {"payload", "sha256"}
            or record["sha256"] != expected or digest(record["payload"]) != expected):
        raise ValueError("original saved context/content binding differs")
    return record["payload"]


def finite(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("finite numeric saved coordinate or metric required")
    return value


def vector(value, length):
    if not isinstance(value, list) or len(value) != length:
        raise ValueError("original saved vector shape required")
    return [finite(v) for v in value]


def targets_from_context(record, scope, expected_context):
    context = unpack(record, expected_context)
    if (context["schema_version"] != "pirc17-closed-input-context-v1"
            or context["truth_passed_to_predictors"] is not False
            or context["raw_sources_independently_reloaded"] is not False
            or any(context[k] != scope[k] for k in
                   ("protocol_sha256", "execution_sha256", "matrix_sha256"))):
        raise ValueError("original input context scope required")
    scoring = unpack(context["scoring_inputs"], scope["scoring_inputs_sha256"])
    population = unpack(context["population"], scope["population_sha256"])
    if (scoring["schema_version"] != "pirc17-formal-scoring-inputs-v1"
            or scoring["partition"] != "final_eval"
            or scoring["truth_passed_to_predictors"] is not False
            or any(scoring[k] != scope[k] for k in
                   ("protocol_sha256", "execution_sha256", "population_sha256"))
            or any(population[k] != scope[k] for k in ("protocol_sha256", "execution_sha256"))):
        raise ValueError("saved scoring target scope required")
    selected = population["selection"]["selected"]
    targets, prefixes = scoring["targets"], context["causal_prefixes"]
    if any(not isinstance(v, list) or len(v) != 46 for v in (selected, targets, prefixes)):
        raise ValueError("entire original46 target population required")
    if (len({r["sample_id"] for r in selected}) != 46
            or len({r["independent_block_id"] for r in selected}) != 46):
        raise ValueError("unique original sample/recording blocks required")
    for target, prefix, member in zip(targets, prefixes, selected):
        if set(target) != {"elapsed_seconds", "independent_block_id", "positions_m",
                          "sample_id", "scoring_frame", "window_sha256"}:
            raise ValueError("original saved target fields required")
        if (member != {"sample_id": target["sample_id"],
                      "independent_block_id": target["independent_block_id"], "split": "final_eval"}
                or any(prefix[k] != target[k] for k in
                       ("sample_id", "independent_block_id", "window_sha256", "scoring_frame"))
                or prefix["score_seconds"] != target["elapsed_seconds"]):
            raise ValueError("saved target population/window/frame/clock differs")
        frame = vector(target["scoring_frame"], 2)
        if abs(frame[0]) > 180 or abs(frame[1]) > 90:
            raise ValueError("original longitude/latitude frame required")
        times = vector(target["elapsed_seconds"], 4)
        if (any(abs(t-h) > 30 or t <= 0 for t,h in zip(times,HORIZONS))
                or any(a >= b for a,b in zip(times,times[1:]))):
            raise ValueError("original ordered target times/tolerance required")
        if not isinstance(target["positions_m"], list) or len(target["positions_m"]) != 4:
            raise ValueError("four original two-dimensional target positions required")
        for position in target["positions_m"]:
            vector(position, 2)
    return targets


def errors_for_row(row, target, baseline):
    if (row["status"] != "success" or row["partition"] != "final_eval"
            or row["origin_mode"] != "causal_prefix"
            or row["scientific"] is not (not baseline)
            or row["sample_id"] != target["sample_id"]
            or row["independent_block_id"] != target["independent_block_id"]
            or row["target_sha256"] != digest(target)):
        raise ValueError("failed or different original target; no successful subset")
    score = row["scores"]
    if (score["particle_count"] != (1 if baseline else 512)
            or score["time_weights"] != [.25]*4
            or score["point_estimator"] != ("deterministic_inertial_path" if baseline
                                             else "ensemble_mean_not_best_of_N")
            or len(score["by_time"]) != 4):
        raise ValueError("original saved mean estimator/weights required")
    errors = []
    for item, time, target_position in zip(score["by_time"], target["elapsed_seconds"], target["positions_m"]):
        region = item["region"]
        if (finite(item["elapsed_seconds"]) != time
                or region["region"] != ("deterministic_point_mass" if baseline
                                        else "ensemble_mean_radial_quantile_disk")):
            raise ValueError("same actual target slot and original center semantics required")
        center = vector(region["center_m"], 2)
        error = math.hypot(center[0]-target_position[0], center[1]-target_position[1])
        finite(error)
        errors.append(error)
    checks = [(mean(errors), finite(score["ade_grid_mean_m"])),
              (mean(errors), finite(score["time_weighted_displacement_error_m"])),
              (errors[-1], finite(score["fde_m"]))]
    if baseline:
        checks += [(e, finite(item["energy_score_m"])) for e,item in zip(errors,score["by_time"])]
    if any(b < 0 or not math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-9) for a,b in checks):
        raise ValueError("point arithmetic does not reproduce original saved ADE/FDE")
    return errors, max(abs(a-b) for a,b in checks)


def summarize(blocks, targets):
    primary = sorted((b for b in blocks if b["origin_mode"] == "causal_prefix"), key=lambda b:b["origin_rank"])
    if [b["origin_rank"] for b in primary] != list(range(46)) or len(targets) != 46:
        raise ValueError("all46 original primary blocks required")
    profiles, gaps, contexts, work_ids = [], [], {}, set()
    for config, model in zip((*SUBJECTS, None), MODELS):
        baseline = config is None
        grouped = []
        for block, target in zip(primary, targets):
            rows = [r for r in block["rows"] if (r["matrix"] == "inertial" if baseline else
                    r["matrix"] == "NEX326-methods" and r["configuration"] == config)]
            if (len(rows) != (1 if baseline else 5)
                    or sorted(r["seed"] for r in rows) != ([None] if baseline else SEEDS)):
                raise ValueError("one original reference/all five original seeds required")
            draws = []
            for row in rows:
                rank = block["origin_rank"]
                if (row["origin_rank"] != rank
                        or row["forecast_work_id"] in work_ids
                        or row["origin_id"] != digest(["pirc17-formal-origin-stream-v1", target["sample_id"], "causal_prefix"])
                        or contexts.setdefault(rank, row["context_sha256"]) != row["context_sha256"]):
                    raise ValueError("exact origin/context/unique forecast pair required")
                work_ids.add(row["forecast_work_id"])
                errors, gap = errors_for_row(row, target, baseline)
                draws.append(errors); gaps.append(gap)
            grouped.append([mean(e[t] for e in draws) for t in range(4)])
        profile = [mean(e[t] for e in grouped) for t in range(4)]
        profiles.append(dict(model=model, configuration=config, recording_hash_blocks=46,
            forecast_rows=46 if baseline else 230, point_error_by_time_m=profile,
            ade_m=mean(profile), fde_m=profile[-1]))
    if len(work_ids) != 736:
        raise ValueError("complete736 saved-forecast identities required")
    times = [t["elapsed_seconds"] for t in targets]
    return dict(profiles=profiles, recording_hash_blocks=46, probabilistic_forecasts=690,
        deterministic_reference_paths=46, saved_forecast_rows_used=736, distinct_target_positions=184,
        nominal_horizon_seconds=HORIZONS, nominal_target_tolerance_seconds=30,
        actual_target_bounds_seconds=[[min(t[i] for t in times),max(t[i] for t in times)] for i in range(4)],
        target_time_vectors_sha256=digest(times),
        maximum_original_ade_fde_consistency_gap_m=max(gaps),
        aggregation="Average five forecast seeds within each original recording-hash block, then equal-weight46 blocks; the deterministic reference is not replicated.")


def project(cache, context_path):
    blocks, scope = load_blocks(cache, INDEX_SHA)
    context = read_bound(context_path, CONTEXT_FILE_SHA)
    targets = targets_from_context(context, scope, CONTEXT_SHA)
    result = summarize(blocks, targets)
    result.update(schema_version="pirc17-saved-center-point-error-description-v1",
        source_scope=scope, source_score_index_sha256=INDEX_SHA, source_cache_sha256=Path(cache).name,
        source_input_context_sha256=CONTEXT_SHA, source_input_context_file_sha256=CONTEXT_FILE_SHA,
        point_error_formula="Euclidean distance between original saved region.center_m and original target.positions_m in the same origin-local scoring frame.",
        new_fits=0, new_forecasts=0, new_particle_scores=0, new_bootstrap_or_tests=0,
        particle_arrays_opened=False, raw_trajectories_opened=False, map_queries=0,
        original_saved_scores_changed=False, independent_saved_output_audit_completed=False,
        scientific_claim_authorized=False, participant_independence_established=False,
        physical_clock_or_utc_certified=False, original_final_figure_inventory_replaced=False,
        private_coordinates_clocks_recording_ids_or_paths_exported=False,
        scope="Post-outcome descriptive saved-center/target arithmetic for the already-bound Full/GMM/dt300 primary comparison and inertial reference, not all28 method configurations or terrain configurations. No confidence intervals, per-horizon significance tests or independent raw-output audit; not the original final analysis/cards or a replacement for the full study.")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-directory", type=Path, required=True)
    parser.add_argument("--input-context", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = project(args.cache_directory,args.input_context)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write((json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+"\n").encode("utf-8"))
    print(json.dumps(result,ensure_ascii=False,allow_nan=False))


if __name__ == "__main__":
    main()
