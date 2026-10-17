"""Describe single-block deletion sensitivity of frozen HSM/CV scores.

Standard library only; no fitting, forecasting, particle scoring, bootstrap,
new hypothesis test or replacement cohort. Output contains aggregates only.
"""
from __future__ import annotations

from collections import defaultdict
import json
import math
from pathlib import Path
from statistics import mean
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.pirc17_replay_input import CONTENT_SHA256, read_package

SEEDS = set(range(20260814, 20260819))


def describe(payload):
    grouped = defaultdict(lambda: {"cv": [], "hsm": []})
    for row in payload["inputs"]["score_rows"]:
        if row["origin_mode"] != "causal_prefix":
            continue
        key = ("cv" if row["matrix"] == "inertial" else "hsm"
               if row["matrix"] == "NEX326-methods" and
               row["configuration"] == "arm-01/full" else None)
        if key:
            grouped[row["independent_block_id"]][key].append(row)
    if len(grouped) != 46:
        raise ValueError("all original 46 primary blocks required")
    differences = [[] for _ in range(4)]
    for pair in grouped.values():
        if (len(pair["cv"]) != 1 or len(pair["hsm"]) != 5 or
                {r["seed"] for r in pair["hsm"]} != SEEDS or
                pair["cv"][0]["seed"] is not None):
            raise ValueError("one CV and five original HSM seeds per block required")
        cv = pair["cv"][0]
        times = [v["elapsed_seconds"] for v in cv["scores"]["by_time"]]
        if len(times) != 4:
            raise ValueError("four original matched targets required")
        for row in [cv, *pair["hsm"]]:
            if (row["status"] != "success" or row["partition"] != "final_eval" or
                    row["origin_id"] != cv["origin_id"] or
                    [v["elapsed_seconds"] for v in row["scores"]["by_time"]] != times):
                raise ValueError("complete same-origin, same-target pairs required")
        for j in range(4):
            value = mean(r["scores"]["by_time"][j]["energy_score_m"]
                         for r in pair["hsm"]) - cv["scores"]["by_time"][j]["energy_score_m"]
            if not math.isfinite(value):
                raise ValueError("finite original scores required")
            differences[j].append(value)
    horizons = []
    for seconds, values in zip((60, 300, 900, 1800), differences):
        deletions = [mean(values[:i] + values[i + 1:]) for i in range(46)]
        horizons.append({"nominal_seconds": seconds,
                         "mean_hsm_minus_cv_es_m": mean(values),
                         "single_block_deletion_range_m": [min(deletions), max(deletions)],
                         "hsm_lower_blocks": sum(v < 0 for v in values),
                         "ordering_sign_retained": all(v * mean(values) > 0 for v in deletions)})
    return {"schema_version": "pirc17-cv-block-deletion-description-v1",
            "original_export_content_sha256": CONTENT_SHA256,
            "primary_blocks": 46, "hsm_seeds_per_block": 5,
            "difference": "HSM minus CV; negative favours HSM",
            "horizons": horizons, "original_full_cohort_retained": True,
            "diagnostic_scope": "Post-hoc sensitivity of saved sample means only; not confidence intervals, registered tests or population validation.",
            "new_fits_forecasts_particle_scores_bootstrap_or_hypothesis_tests": 0}


if __name__ == "__main__":
    raw, _ = read_package(ROOT / "paper/pirc17/replay-input-v1")
    print(json.dumps(describe(json.loads(raw)["payload"]), indent=2, allow_nan=False))
