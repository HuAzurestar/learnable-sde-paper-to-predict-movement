"""Aggregate actual target clocks in already-bound scores; no prediction/scoring."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import statistics

SUBJECTS = ("arm-01/full", "arm-04/gmm_kernel", "arm-06/dt300")
SEEDS = tuple(range(20260814, 20260819))
HORIZONS = (60, 300, 900, 1800)
STAGE_SHA = "8900f3dee68d5fc9cafd5ced2e2394503432d2493251601c0ba9cb771cbefba1"
BINDINGS_SHA = "64ec590c296689ee17f4a8ae4f6e5bec5253c509d8f3fb09e6d3eafc4f836277"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def read_json(path, expected=None):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 32 * 1024 * 1024:
        raise ValueError("bounded regular score metadata required")
    raw = path.read_bytes()
    if expected is not None and hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("original metadata file binding differs")
    value = json.loads(raw, object_pairs_hook=unique_object,
                       parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    canonical(value)
    return value


def unpack(value):
    if (set(value) != {"payload", "sha256"}
            or not isinstance(value["payload"], dict)
            or digest(value["payload"]) != value["sha256"]):
        raise ValueError("saved metadata content binding differs")
    return value["payload"]


def summarize(rows):
    expected = {(subject, rank, seed) for subject in SUBJECTS
                for rank in range(46) for seed in SEEDS}
    seen, blocks, samples, targets, times = set(), {}, {}, {}, {}
    for row in rows:
        axes = row["configuration"], row["origin_rank"], row["seed"]
        if axes not in expected or axes in seen:
            raise ValueError("duplicate or outside original 690-row grid")
        if (row["status"] != "success" or row["matrix"] != "NEX326-methods"
                or row["origin_mode"] != "causal_prefix" or row["partition"] != "final_eval"
                or row["scientific"] is not True):
            raise ValueError("failed or wrong-population row; no successful subset")
        seen.add(axes)
        rank = row["origin_rank"]
        for registry, field in ((blocks, "independent_block_id"), (samples, "sample_id"),
                                (targets, "target_sha256")):
            if registry.setdefault(rank, row[field]) != row[field]:
                raise ValueError("configuration/seed changes original target identity")
        by_time = row["scores"]["by_time"]
        if len(by_time) != 4:
            raise ValueError("four original target times required")
        vector = tuple(t["elapsed_seconds"] for t in by_time)
        if any(type(t) not in (int, float) or not math.isfinite(t) or t <= 0
               or abs(t - nominal) > 30 for t, nominal in zip(vector, HORIZONS)):
            raise ValueError("nonfinite, nonpositive or outside target tolerance")
        if any(a >= b for a, b in zip(vector, vector[1:])):
            raise ValueError("distinct ordered actual target times required")
        if times.setdefault(rank, vector) != vector:
            raise ValueError("configuration/seed changes actual target times")
    if seen != expected or len(set(blocks.values())) != 46 or len(set(samples.values())) != 46:
        raise ValueError("complete original 46-recording-block grid required")
    profiles = []
    for slot, nominal in enumerate(HORIZONS):
        actual = [times[rank][slot] for rank in range(46)]
        offsets = [t - nominal for t in actual]
        profiles.append({
            "nominal_seconds": nominal, "recording_blocks": 46,
            "minimum_seconds": min(actual), "median_seconds": statistics.median(actual),
            "mean_seconds": statistics.mean(actual), "maximum_seconds": max(actual),
            "minimum_offset_seconds": min(offsets), "maximum_offset_seconds": max(offsets),
            "maximum_absolute_offset_seconds": max(map(abs, offsets)),
            "exact_nominal_count": sum(t == nominal for t in actual),
            "earlier_count": sum(t < nominal for t in actual),
            "later_count": sum(t > nominal for t in actual),
        })
    return {
        "schema_version": "pirc17-saved-target-time-description-v1",
        "bound_score_rows": len(seen), "recording_blocks": 46,
        "distinct_targets_across_four_slots": 184,
        "configurations_checked": list(SUBJECTS), "forecast_rng_seeds_checked": 5,
        "nominal_tolerance_seconds": 30,
        "target_time_vectors_sha256": digest([list(times[r]) for r in range(46)]),
        "maximum_actual_stop_seconds": max(t[-1] for t in times.values()),
        "actual_stops_after_1800_seconds": sum(t[-1] > 1800 for t in times.values()),
        "horizons": profiles,
        "scope": {
            "new_fits_predictions_particle_scores_or_resampling": 0,
            "independent_output_audit_completed": False,
            "physical_clock_or_utc_provenance_certified": False,
            "all_method_or_terrain_output_times_audited": False,
            "private_coordinates_absolute_clocks_or_recording_ids_exported": False,
            "description": "Saved-score target-clock description:46 primary recording blocks, not690 independent targets. Same target identities and times across all three bound configurations and five seeds. Original target tolerance and predictions unchanged; does not independently inspect prediction arrays or original sensor clocks.",
        },
    }


def project(cache, bindings_path, stage_path):
    cache = Path(cache)
    bindings = read_json(bindings_path, BINDINGS_SHA)
    stage = read_json(stage_path, STAGE_SHA)
    if cache.name != stage["cache_sha256"] or len(bindings["score_sources"]) != 690:
        raise ValueError("original cache and exact690 bound score identities required")
    origins = {row["rank"]: row for row in bindings["origins"]}
    if len(bindings["origins"]) != 46 or set(origins) != set(range(46)):
        raise ValueError("original46 origin identity mapping required")
    rows = []
    for work_id, expected in bindings["score_sources"].items():
        if len(work_id) != 64 or any(c not in "0123456789abcdef" for c in work_id):
            raise ValueError("invalid bound work identity")
        matches = []
        for path in (cache / "rows" / work_id).glob("*.json"):
            value = unpack(read_json(path))
            if digest(value) != expected:
                continue
            scope = value["scope"]
            if (value["schema_version"] != "pirc17-checkpoint-scoring-v1-row"
                    or scope["cache_sha256"] != cache.name or path.stem != digest(scope)):
                raise ValueError("saved score scope differs")
            matches.append(value["row"])
        if len(matches) != 1:
            raise ValueError("missing/ambiguous original score; no partial projection")
        row = matches[0]
        origin = origins.get(row["origin_rank"])
        if (origin is None or row["forecast_work_id"] != work_id
                or row["sample_id"] != origin["sample_id"]
                or row["independent_block_id"] != origin["independent_block_id"]
                or row["origin_id"] != digest(
                    ["pirc17-formal-origin-stream-v1", origin["sample_id"], "causal_prefix"])):
            raise ValueError("bound origin or stream identity differs")
        rows.append(row)
    return {
        **summarize(rows), "input_bindings_sha256": BINDINGS_SHA,
        "cached_score_records_sha256": digest(bindings["score_sources"]),
        "original_stage_sha256": STAGE_SHA, "cache_sha256": cache.name,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("cache", "bindings", "stage", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = project(args.cache, args.bindings, args.stage)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(canonical(result) + b"\n")
    print(json.dumps({"recording_blocks": 46, "rows_checked": 690,
                      "horizons": result["horizons"],
                      "stops_after1800": result["actual_stops_after_1800_seconds"],
                      "new_predictions": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
