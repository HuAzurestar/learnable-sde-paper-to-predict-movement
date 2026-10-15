"""Post-hoc descriptive terrain summaries from immutable saved score scalars.

No forecast arrays, positions, targets, model code, fits, scoring, random draws
or inferential tests. Original full-family verdicts remain unavailable.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean

from scripts.describe_pirc17_inertial import load_blocks, metrics, finite, SEEDS

CONFIGS = ["base", "all-terrain", "lio-road", "lio-river", "lio-worldcover",
           "lio-surface", "loo-road", "loo-river", "loo-worldcover", "loo-surface"]
INDEX_SHA = "fc7c9c4492b962763ecd0f13959a43bf00e2141e74d92273c45cf6ca98e7332f"
CACHE_SHA = "892bb89b1d39d376c69d5a41570ad1655e50fe6950be6442db7f2b2f492c2878"


def scalar_metrics(row):
    result, _ = metrics(row, False)
    covers, areas = [], []
    for point in row["scores"]["by_time"]:
        region = point["region"]
        if region["region"] != "ensemble_mean_radial_quantile_disk":
            raise ValueError("original mean-centred radial region required")
        levels = [v for v in region["levels"] if v["level"] == .9]
        if len(levels) != 1 or type(levels[0]["covered"]) is not bool:
            raise ValueError("one saved Boolean 90% inclusion required")
        covers.append(float(levels[0]["covered"]))
        areas.append(finite(levels[0]["area_m2"]) / 1e6)
    # Deliberately never reads or exports region centre, origin, target or time.
    return {"es_m": result["weighted_es_m"], "fde_m": result["fde_m"],
            "ade_m": result["ade_m"], "es_by_horizon_m": result["es_by_time_m"],
            "coverage90_by_horizon": covers, "area90_by_horizon_km2": areas}


def aggregate(rows):
    def average(key):
        values = [r[key] for r in rows]
        if isinstance(values[0], list):
            return [mean(v[j] for v in values) for j in range(4)]
        return mean(values)
    return {key: average(key) for key in rows[0]}


def describe(blocks, scope):
    primary = [b for b in blocks if b["origin_mode"] == "causal_prefix"]
    if sorted(b["origin_rank"] for b in primary) != list(range(46)):
        raise ValueError("entire original 46-block primary population required")
    values, success_counts = {}, {c: 0 for c in CONFIGS}
    for b in primary:
        selected = [r for r in b["rows"] if r["matrix"] == "terrain"]
        if len(selected) != 50:
            raise ValueError("all ten configurations and five seed slots required")
        keys = [(r["configuration"], r["seed"]) for r in selected]
        if set(keys) != {(c, s) for c in CONFIGS for s in SEEDS} or len(set(keys)) != 50:
            raise ValueError("missing, duplicate or extra terrain slot")
        if len({r["target_sha256"] for r in selected}) != 1:
            raise ValueError("configuration targets are not matched")
        slots = {}
        for r in selected:
            if (r["partition"] != "final_eval" or r["scientific"] is not True
                    or r["status"] not in {"success", "failed"}):
                raise ValueError("original terminal scientific evaluation required")
            key = (r["configuration"], r["seed"])
            slots[key] = scalar_metrics(r) if r["status"] == "success" else None
            success_counts[key[0]] += r["status"] == "success"
        values[b["origin_rank"]] = slots
    complete = {c: {i for i, v in values.items() if all(v[c, s] is not None for s in SEEDS)} for c in CONFIGS}
    common = set.intersection(*complete.values())
    if not common:
        raise ValueError("no jointly complete block population")

    def profile(c, selected):
        # Exactly five seeds per block, then equal block weights.
        return aggregate([aggregate([values[i][c, s] for s in SEEDS]) for i in sorted(selected)])

    common_profiles = {c: profile(c, common) for c in CONFIGS}
    rows = []
    for c in CONFIGS:
        control = "all-terrain" if c.startswith("loo-") else "base"
        paired = complete[c] & complete[control]
        candidate, reference = profile(c, paired), profile(control, paired)
        block_deltas = [mean(values[i][c, s]["es_m"] - values[i][control, s]["es_m"] for s in SEEDS) for i in sorted(common)]
        rows.append({"configuration": c, "full_grid_expected_slots": 230,
                     "full_grid_successful_slots": success_counts[c],
                     "full_grid_failed_slots": 230 - success_counts[c],
                     "five_seed_complete_blocks": len(complete[c]),
                     "common_complete_blocks": len(common),
                     "common_complete_profile": common_profiles[c],
                     "configuration_complete_profile": profile(c, complete[c]),
                     "contrast_control": control,
                     "common_delta_es_m": common_profiles[c]["es_m"] - common_profiles[control]["es_m"],
                     "common_delta_fde_m": common_profiles[c]["fde_m"] - common_profiles[control]["fde_m"],
                     "common_blocks_lower_es": sum(v < 0 for v in block_deltas),
                     "pairwise_complete_blocks": len(paired),
                     "pairwise_delta_es_m": candidate["es_m"] - reference["es_m"],
                     "pairwise_delta_fde_m": candidate["fde_m"] - reference["fde_m"]})
    return {"schema_version": "pirc17-terrain-posthoc-description-v1", "source_index_sha256": INDEX_SHA,
            "source_cache_sha256": CACHE_SHA, "source_scope": scope,
            "population": {"original_blocks": 46, "seeds_per_block": 5, "configurations": 10,
                           "original_slots": 2300, "successful_slots": sum(success_counts.values()),
                           "failed_slots": 2300 - sum(success_counts.values()), "missing_slots": 0,
                           "jointly_complete_blocks": len(common), "excluded_blocks": 46 - len(common),
                           "jointly_complete_slots": len(common) * 50},
            "selection": "Post-hoc intersection of recording blocks with successful forecasts in all ten configurations and all five seeds; selection uses status only. No imputation. Both the common subset and larger pairwise-complete sensitivities condition on successful execution and do not recover the full-cohort estimand.",
            "weighting": "Five seeds averaged within each complete recording block, then blocks weighted equally. Horizon-average ES weights four saved targets equally. Seed disks share real targets and are not independent participants.",
            "horizons_saved_minutes": [1, 5, 15, 30], "rows": rows,
            "scope": {"posthoc_descriptive_only": True, "registered_full_family_inference": "unavailable",
                      "successful_subset_used_for_confirmatory_inference": False,
                      "raw_prediction_arrays_or_coordinates_exported": False,
                      "new_fits_forecasts_scores_resampling_or_map_queries": 0,
                      "causal_factor_effect_or_population_superiority_established": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-directory", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise ValueError("fresh output directory required")
    if args.cache_directory.name != CACHE_SHA:
        raise ValueError("unchanged original cache required")
    blocks, scope = load_blocks(args.cache_directory, INDEX_SHA)
    result = describe(blocks, scope)
    args.output_dir.mkdir(parents=True)
    result["reader_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (args.output_dir / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    with (args.output_dir / "configurations.csv").open("w", encoding="utf-8", newline="") as stream:
        fields = ["configuration", "common_blocks", "successful_slots", "expected_slots", "es_m", "fde_m", "coverage90_30min_pct", "area90_30min_km2", "contrast_control", "common_delta_es_m", "pairwise_blocks", "pairwise_delta_es_m"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in result["rows"]:
            p = row["common_complete_profile"]
            writer.writerow(dict(zip(fields, [row["configuration"], row["common_complete_blocks"], row["full_grid_successful_slots"], 230, p["es_m"], p["fde_m"], 100*p["coverage90_by_horizon"][-1], p["area90_by_horizon_km2"][-1], row["contrast_control"], row["common_delta_es_m"], row["pairwise_complete_blocks"], row["pairwise_delta_es_m"]])))
    print(json.dumps({"population": result["population"], "rows": [{k: v for k, v in r.items() if not k.endswith("profile")} | {"es_m": r["common_complete_profile"]["es_m"], "fde_m": r["common_complete_profile"]["fde_m"], "cover30_pct":100*r["common_complete_profile"]["coverage90_by_horizon"][-1]} for r in result["rows"]]}, indent=2))


if __name__ == "__main__":
    main()
