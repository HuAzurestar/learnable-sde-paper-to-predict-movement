"""Describe original saved eligibility metadata; run with python -m scripts..."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path

from scripts.describe_pirc17_target_times import canonical, digest, read_json, unpack

ELIGIBILITY_SHA = "d9600487e5e7b2ad7fcca5c955b59b0c255fc51d4a9e729508b987452da0ffc5"
ELIGIBILITY_FILE_SHA = "7ce338a1a2a67ef0642b484497960916004d872686d036ec25facd6a9df44718"
POPULATION_SHA = "7061f44ef8647f7bee55822ca7e494e53d3c058e5973d6198e997893c70bb020"
POPULATION_FILE_SHA = "5748b8903198a462f6145ed6d9d3676d793d90227a1a725bffd2720adad7e53b"
PARTITION_SHA = "e767f97c0cf856cd9559edcc11207147d211617ff3214ce3c9692cfb73cdd9e0"
PROTOCOL_SHA = "2267ab84fa77ff4039234a61e8f44be1c3713317d8ad2d1bb4ced9af0c5b293a"
EXECUTION_SHA = "c3e44393f6bc5544aaa21bb273c94eaecb9d0becb4e0590771355c4c0be9b6c2"
RULE_SHA = "35426b655f9032106ce7537ad153b984389501d1c51b9c0ebc3ea1e97791038d"
METADATA = {
    "invalid-integer-point-metadata", "incomplete-or-duplicate-original-indexes",
    "alignment-identity-mismatch", "invalid-or-duplicate-source-indexes",
    "timestamp-outside-int64",
}
TEMPORAL = {
    "insufficient-visible-prefix", "nonpositive-observation-gap",
    "observation-gap-exceeds-60s", "followup-shorter-than-1800s",
    "missing-distinct-original-score-targets",
}
COVERAGE = {f"invalid-{group}-coverage-origin-through-target-end"
            for group in ("surface", "road", "river", "worldcover", "history")}


def summarize(rows, selection):
    """Count each denominator member once; overlap counts are separate."""
    fields = {"sample_id", "segment_id", "independent_block_id", "split",
              "eligible", "reasons", "window_sha256"}
    seen, groups = set(), defaultdict(list)
    metadata_ok, temporal_ok, eligible = [], [], []
    first, overlapping, exclusive = Counter(), Counter(), Counter()
    for row in rows:
        if (set(row) != fields or row["split"] != "final_eval"
                or type(row["eligible"]) is not bool
                or any(not isinstance(row[k], str) or not row[k]
                       for k in ("sample_id", "segment_id", "independent_block_id"))
                or row["sample_id"] in seen):
            raise ValueError("unique original final denominator metadata required")
        seen.add(row["sample_id"])
        reasons = row["reasons"]
        if (not isinstance(reasons, list) or any(not isinstance(x, str) for x in reasons)
                or len(set(reasons)) != len(reasons)
                or set(reasons) - METADATA - TEMPORAL - COVERAGE
                or row["eligible"] != (not reasons)
                or (row["window_sha256"] is None) == row["eligible"]):
            raise ValueError("explicit consistent original dispositions required")
        if reasons:
            first[reasons[0]] += 1
            overlapping.update(reasons)
        if METADATA.intersection(reasons):
            exclusive["metadata"] += 1
            continue
        metadata_ok.append(row)
        if TEMPORAL.intersection(reasons):
            exclusive["temporal"] += 1
            continue
        temporal_ok.append(row)
        if COVERAGE.intersection(reasons):
            exclusive["coverage_after_temporal"] += 1
            continue
        eligible.append(row)
        groups[row["independent_block_id"]].append(row["sample_id"])
    order = sorted(groups, key=lambda b: (digest(["pirc17-final-block-order-v1", b]), b))
    selected = [{"independent_block_id": b, "sample_id": min(groups[b]), "split": "final_eval"}
                for b in order[:46]]
    if (selection["selected"] != selected
            or selection["secondary_selected"] != selected[:6]
            or selection["eligible_block_count"] != len(order)
            or selection["requested_blocks"] != 46
            or selection["selection_sha256"] != digest(selected)):
        raise ValueError("original outcome-blind block order or selected origin differs")
    def count(values):
        return {"windows": len(values), "recording_hash_blocks":
                len({r["independent_block_id"] for r in values})}
    return {
        "schema_version": "pirc17-saved-final-cohort-description-v1",
        "stages": {"released": count(rows), "metadata_complete": count(metadata_ok),
                   "temporal_support": count(temporal_ok), "joint_feature_validity": count(eligible),
                   "selected_primary": count(selected)},
        "mutually_exclusive_exclusions": dict(sorted(exclusive.items())),
        "first_recorded_reason_counts": dict(sorted(first.items())),
        "overlapping_reason_counts": dict(sorted(overlapping.items())),
        "eligible_windows_per_block_histogram": dict(sorted(Counter(
            len(v) for v in groups.values()).items())),
        "eligible_blocks_not_selected": len(order) - len(selected),
        "eligible_windows_not_selected_as_origins": len(eligible) - len(selected),
        "selected_block_eligible_windows": sum(len(groups[r["independent_block_id"]]) for r in selected),
        "secondary_blocks_reused_per_mode": len(selected[:6]),
        "selection_sha256": digest(selected),
        "scope": {"new_fits_forecasts_particle_scores_or_map_queries": 0,
                  "original_eligibility_recomputed_from_raw_points": False,
                  "private_sample_segment_block_ids_or_coordinates_exported": False,
                  "independent_saved_output_audit_completed": False,
                  "participant_or_near_route_independence_established": False,
                  "included_excluded_geographic_speed_duration_distributions_available": False},
    }


def project(eligibility_path, population_path, partition_path):
    eligibility = unpack(read_json(eligibility_path, ELIGIBILITY_FILE_SHA))
    population = unpack(read_json(population_path, POPULATION_FILE_SHA))
    partition = read_json(partition_path, PARTITION_SHA)
    if (digest(eligibility) != ELIGIBILITY_SHA or digest(population) != POPULATION_SHA
            or population["eligibility_sha256"] != ELIGIBILITY_SHA
            or any(value["protocol_sha256"] != PROTOCOL_SHA
                   or value["execution_sha256"] != EXECUTION_SHA
                   or value["prior_performance_reads"] != 0 for value in (eligibility, population))
            or eligibility["eligibility_rule_sha256"] != RULE_SHA
            or eligibility["schema_version"] != "pirc17-final-eligibility-report-v1"):
        raise ValueError("original sealed eligibility/population scope differs")
    rows = eligibility["rows"]
    names = ("sample_id", "segment_id", "independent_block_id")
    identities = {k: sorted({r[k] for r in rows}) for k in names}
    if (digest(identities) != population["full_population_identity_sha256"]
            or digest(sorted([r[k] for k in names] for r in rows)) !=
            population["full_population_row_identity_sha256"]
            or len(rows) != partition["release_counts"]["final_eval"]["midpoint_windows"]):
        raise ValueError("complete original release denominator required; no successful subset")
    result = summarize(rows, population["selection"])
    expected = {"released": (12370, 1094), "temporal_support": (127, 89),
                "joint_feature_validity": (106, 73), "selected_primary": (46, 46)}
    if any(result["stages"][k] != {"windows": n, "recording_hash_blocks": b}
           for k, (n, b) in expected.items()):
        raise ValueError("saved original final cohort counts differ")
    result["bindings"] = {"eligibility_content_sha256": ELIGIBILITY_SHA,
                          "eligibility_file_sha256": ELIGIBILITY_FILE_SHA,
                          "population_content_sha256": POPULATION_SHA,
                          "population_file_sha256": POPULATION_FILE_SHA,
                          "partition_description_sha256": PARTITION_SHA,
                          "protocol_sha256": PROTOCOL_SHA, "execution_sha256": EXECUTION_SHA,
                          "eligibility_rule_sha256": RULE_SHA}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("eligibility", "population", "partition", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = project(args.eligibility, args.population, args.partition)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(canonical(result) + b"\n")
    print(canonical(result).decode("utf-8"))


if __name__ == "__main__":
    main()
