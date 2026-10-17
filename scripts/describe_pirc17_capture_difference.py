"""Reconcile two existing aggregate captures, not individual forecast identities.

Reads saved JSON counts only. No arrays, maps, scoring, resampling or producer
state are read or changed. An aggregate net difference is NOT an item set.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "paper/pirc17/preliminary-method-statistics-v1.json"
STAGE_SHA = "8900f3dee68d5fc9cafd5ced2e2394503432d2493251601c0ba9cb771cbefba1"
EXECUTION_SHA = "e736ea70f79f147e00e460b827a2f214368fc68da77a32c0086227df225557b2"
MODES = {"causal_prefix": 46, "known_velocity": 6, "point_only": 6}


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def integer(value):
    if type(value) is not int or value < 0:
        raise ValueError("nonnegative integer counts required")
    return value


def reconcile(stage, earlier, later):
    if (earlier["captured_utc"] != stage["captured_utc"]
            or earlier["score_index_sha256"] != stage["score_index_sha256"]
            or earlier["captured_rows_sha256"] != stage["captured_rows_sha256"]
            or earlier["cache_sha256"] != stage["cache_sha256"]
            or earlier["settings_id"] != stage["settings_id"]
            or later["settings_id"] != stage["settings_id"]
            or earlier["captured_utc"] >= later["captured_utc"]):
        raise ValueError("same original settings and distinct ordered capture bindings required")
    indexed = []
    for source in (earlier, later):
        rows = source["configurations"]
        keys = [(r["matrix"], r["origin_mode"], r["configuration"]) for r in rows]
        if len(rows) != 114 or len(set(keys)) != 114:
            raise ValueError("complete unique 114-cell count inventory required")
        indexed.append(dict(zip(keys, rows)))
    old, new = indexed
    if old.keys() != new.keys():
        raise ValueError("capture cell identities differ")
    configurations = {matrix: {k[2] for k in old if k[0] == matrix}
                      for matrix in ("NEX326-methods", "terrain")}
    expected = {(matrix, mode, config) for matrix, configs in configurations.items()
                for mode in MODES for config in configs}
    if (len(configurations["NEX326-methods"]) != 28
            or len(configurations["terrain"]) != 10 or set(old) != expected):
        raise ValueError("original 28 method and ten terrain configurations in three modes required")
    cells = []
    for key in sorted(old):
        a, b = old[key], new[key]
        denominator = MODES[key[1]] * 5
        if integer(a["expected"]) != denominator or integer(b["expected"]) != denominator:
            raise ValueError("original block-mode and five-seed denominator required")
        if set(a["counts"]) - {"success", "failed"}:
            raise ValueError("unknown earlier scoring disposition")
        first = {"success": integer(a["counts"].get("success", 0)),
                 "failed": integer(a["counts"].get("failed", 0)),
                 "missing": integer(a["missing"])}
        second = {"success": integer(b["forecast_success"]),
                  "failed": integer(b["forecast_failed"]),
                  "missing": integer(b["forecast_runnable"])}
        if sum(first.values()) != denominator or sum(second.values()) != denominator:
            raise ValueError("cell counts do not exhaust the registered denominator")
        if (b["score_index_success"] != second["success"]
                or b["score_index_failed"] != second["failed"]
                or b["score_index_missing"] != second["missing"]
                or any(b[k] != 0 for k in ("score_index_invalid", "score_index_unavailable"))):
            raise ValueError("later forecast and score-index count alignment not established")
        cells.append(dict(matrix=key[0], origin_mode=key[1], configuration=key[2],
                          expected=denominator, earlier=first, later=second,
                          net_success_count_change=second["success"]-first["success"]))
    groups = []
    for matrix in configurations:
        for mode in MODES:
            selected = [c for c in cells if (c["matrix"], c["origin_mode"]) == (matrix, mode)]
            group = dict(matrix=matrix, origin_mode=mode,
                         expected=sum(c["expected"] for c in selected))
            for capture in ("earlier", "later"):
                group[capture] = {k: sum(c[capture][k] for c in selected)
                                  for k in ("success", "failed", "missing")}
            group["net_success_count_change"] = group["later"]["success"]-group["earlier"]["success"]
            groups.append(group)
    totals = {capture: {k: sum(g[capture][k] for g in groups)
                       for k in ("success", "failed", "missing")}
              for capture in ("earlier", "later")}
    if (sum(g["expected"] for g in groups) != 11020
            or totals["earlier"] != {"success": stage["row_status_counts"]["success"],
                                      "failed": stage["row_status_counts"]["failed"],
                                      "missing": 11020-stage["captured_scientific_rows"]}
            or totals["later"] != {"success": later["scientific"]["forecast_success"],
                                    "failed": later["scientific"]["forecast_failed"],
                                    "missing": later["scientific"]["forecast_runnable"]}):
        raise ValueError("full aggregate totals differ from the pinned captures")
    return dict(schema_version="pirc17-aggregate-capture-reconciliation-v1",
        earlier_capture={k: earlier[k] for k in ("captured_utc", "settings_id", "score_index_sha256",
                                               "predictor_index_sha256", "captured_rows_sha256")},
        later_capture={k: later[k] for k in ("captured_utc", "settings_id", "score_index_sha256",
                                           "predictor_index_sha256")},
        scientific_expected=11020, totals=totals, matrix_modes=groups, configurations=cells,
        changed_count_cells=sum(c["earlier"] != c["later"] for c in cells),
        net_success_count_change=totals["later"]["success"]-totals["earlier"]["success"],
        method_count_cells_unchanged=all(c["earlier"] == c["later"] for c in cells
                                       if c["matrix"] == "NEX326-methods"),
        individual_work_id_sets_retained_in_these_sources=False,
        individual_identity_difference_reconstructed=False,
        no_replacements_within_a_cell_established=False,
        independent_saved_output_audit_completed=False,
        original_method_statistics_changed=False,
        new_forecasts_fits_scores_resampling_or_map_queries=0,
        interpretation="Exact net count differences on the same saved 114-cell grid; not individual work-ID set differences, proof of monotonic membership, payload validation, or final scientific qualification.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scoring-summary", type=Path, required=True)
    parser.add_argument("--execution-summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    stage = json.loads(STAGE.read_text(encoding="utf-8"))
    if (file_hash(STAGE) != STAGE_SHA
            or file_hash(args.scoring_summary) != stage["private_derivative_file_sha256"]
            or file_hash(args.execution_summary) != EXECUTION_SHA):
        raise ValueError("original immutable capture bytes required; no live-state substitution")
    if args.output.resolve() in {STAGE.resolve(), args.scoring_summary.resolve(), args.execution_summary.resolve()}:
        raise ValueError("output must not overwrite saved inputs")
    result = reconcile(stage, json.loads(args.scoring_summary.read_text(encoding="utf-8")),
                       json.loads(args.execution_summary.read_text(encoding="utf-8")))
    result["source_file_sha256"] = dict(stage=STAGE_SHA,
        scoring_summary=file_hash(args.scoring_summary), execution_summary=EXECUTION_SHA,
        generator=file_hash(__file__))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: result[k] for k in ("net_success_count_change", "changed_count_cells",
                                           "method_count_cells_unchanged", "matrix_modes")}))


if __name__ == "__main__":
    main()
