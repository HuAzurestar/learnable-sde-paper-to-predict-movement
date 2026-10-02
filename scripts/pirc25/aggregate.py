"""Validate a frozen shared-runtime matrix and aggregate independent blocks.

Seed repeats are averaged within a block. Missing/failed cells stay in the
denominator and incomplete blocks never silently enter paired inference.
No runtime, training, or trajectory provider is imported by this module.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import random
import tempfile
from statistics import mean

if __package__:
    from .admission import validate_admission
    from .dimensions import comparison_dimensions
    from .costs import validate_cost, summarize_cost
else:
    from admission import validate_admission
    from dimensions import comparison_dimensions
    from costs import validate_cost, summarize_cost


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def fingerprint(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def validate_bundle(bundle, *, formal=False):
    body = {key: value for key, value in bundle.items() if key != "bundle_hash"}
    if bundle.get("schema_version") != "pirc25-evidence-bundle-v1" or bundle.get("bundle_hash") != fingerprint(body):
        raise ValueError("bundle schema/hash mismatch")
    if bundle.get("independent_unit") != "block_id":
        raise ValueError("seed is not an independent sampling unit")
    if formal:
        plan = bundle.get("comparison_plan") or {}
        if (not plan.get("reference_arm_id") or not plan.get("candidate_arm_ids")
                or len(plan.get("preregistration_hash", "")) != 64
                or plan.get("failure_policy") != "retain-and-exclude-incomplete-blocks"):
            raise ValueError("formal comparison requires a frozen preregistered comparison plan")
    expected = {cell["cell_hash"]: cell for cell in bundle["expected_cells"]}
    rows = {cell["cell_hash"]: cell for cell in bundle["cells"]}
    if (not expected or len(expected) != len(bundle["expected_cells"])
            or len(rows) != len(bundle["cells"]) or rows.keys() != expected.keys()):
        raise ValueError("every expected cell needs exactly one explicit disposition")
    compatibility = None
    seen = set()
    cost_sources = set()
    for cell in rows.values():
        validate_cost(cell, bundle, cost_sources)
        if any(cell[key] != expected[cell["cell_hash"]][key] for key in ("arm_id", "block_id", "seed")):
            raise ValueError("cell identity changed")
        dimensions = comparison_dimensions(cell)
        if canonical(dimensions) != canonical(comparison_dimensions(expected[cell["cell_hash"]])):
            raise ValueError("cell comparison dimension identity changed")
        if "registered_cell" in cell:
            registered = cell["registered_cell"]
            if (fingerprint(registered) != cell["cell_hash"] or
                    any(registered[k] != cell[k] for k in ("arm_id", "block_id", "seed")) or
                    canonical(comparison_dimensions(registered)) != canonical(dimensions)):
                raise ValueError("registered cell dimension identity changed")
        key = (cell["arm_id"], cell["block_id"], cell["seed"], canonical(dimensions))
        if key in seen:
            raise ValueError("duplicate block/seed identity")
        seen.add(key)
        if cell["status"] not in {"MISSING", "REGISTERED", "RUNNING", "SUCCEEDED", "FAILED", "INTERRUPTED", "TIMEOUT", "BUDGET_EXHAUSTED", "PREFLIGHT_FAILED", "CANCELLED"}:
            raise ValueError("unknown cell status")
        if cell["status"] != "SUCCEEDED":
            if cell.get("metrics") is not None:
                raise ValueError("failed/missing cell cannot supply successful metrics")
            continue
        if not cell.get("attempt_id") or not cell.get("artifact_id") or not cell.get("run_id"):
            raise ValueError("successful evidence has no immutable attempt/artifact source")
        if formal and cell.get("qualification") != "qualified":
            raise ValueError("fixture or unqualified results cannot enter formal comparison")
        if formal:
            validate_admission(bundle, cell)
        if cell.get("protocol_hash") != bundle["protocol_hash"]:
            raise ValueError("mixed data protocol")
        current = (cell.get("state_order"), cell.get("units"), cell.get("metric_units"))
        if compatibility is not None and compatibility != current:
            raise ValueError("incompatible state, metrics or units")
        compatibility = current
        if not cell.get("metrics") or set(cell["metrics"]) != set(cell["metric_units"]):
            raise ValueError("metric units missing")
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in cell["metrics"].values()):
            raise ValueError("nonfinite/invalid metric")
    if formal:
        source = bundle.get("registered_spec")
        if source is None:
            # Legacy successful receipts already carry the same frozen spec.
            # All-failed legacy bundles cannot prove their original matrix.
            source = next((c.get("admission", {}).get("spec") for c in rows.values()
                           if c["status"] == "SUCCEEDED"), None)
        if not isinstance(source, dict) or fingerprint(source) != bundle["spec_hash"]:
            raise ValueError("formal registered matrix requires its bound source spec/admission")
        if (any(source.get(k) != bundle[k] for k in ("study_id", "code_hash", "data_hash", "protocol_hash")) or
                source.get("comparison_plan") != bundle["comparison_plan"]):
            raise ValueError("formal registered matrix source identity/plan changed")
        registered = {fingerprint(c): c for c in source["cells"]}
        if len(registered) != len(source["cells"]) or registered.keys() != rows.keys():
            raise ValueError("formal registered matrix was clipped or changed")
        for cell_hash, cell in rows.items():
            original = registered[cell_hash]
            if (any(cell[k] != original[k] for k in ("arm_id", "block_id", "seed")) or
                    canonical(comparison_dimensions(cell)) != canonical(comparison_dimensions(original))):
                raise ValueError("formal registered matrix identity/dimensions changed")
    return rows


def aggregate(bundle, *, formal=False, descriptive_intervals=True):
    rows = validate_bundle(bundle, formal=formal)
    strata = defaultdict(list)
    for row in rows.values():
        strata[canonical(comparison_dimensions(row))].append(row)
    arms, comparisons = [], []
    registered_arms = {row["arm_id"] for row in rows.values()}
    plan = bundle.get("comparison_plan") or {}
    baseline = plan.get("reference_arm_id", min(registered_arms))
    candidates = plan.get("candidate_arm_ids", sorted(registered_arms - {baseline}))
    if (baseline not in registered_arms or len(candidates) != len(set(candidates)) or
            any(candidate not in registered_arms or candidate == baseline for candidate in candidates)):
        raise ValueError("comparison plan refers to unregistered or identical arms")
    for key, cells in sorted(strata.items()):
        dimensions = json.loads(key)
        stratum_arms, stratum_comparisons = aggregate_stratum(cells, baseline, candidates,
                                                           descriptive_intervals=descriptive_intervals)
        for summary in [*stratum_arms, *stratum_comparisons]:
            summary.update(comparison_dimensions=dimensions, stratum_id=fingerprint(dimensions))
        arms.extend(stratum_arms)
        comparisons.extend(stratum_comparisons)
    result = {"schema_version": "pirc25-aggregate-v1", "study_id": bundle["study_id"],
              "spec_hash": bundle["spec_hash"], "protocol_hash": bundle["protocol_hash"],
              "data_hash": bundle["data_hash"], "code_hash": bundle["code_hash"], "source_bundle_hash": bundle["bundle_hash"],
              "independent_unit": "block_id", "seed_policy": "average-within-block-not-independent-replication",
              "stratum_policy": "exact-comparison-dimensions-no-cross-stratum-pooling",
              "qualification": "formal" if formal else "engineering-fixture", "arms": arms, "comparisons": comparisons,
              "expected_cell_count": len(rows), "successful_cell_count": sum(c["status"] == "SUCCEEDED" for c in rows.values()),
              "cell_dispositions": list(rows.values()), "disclosure_scope": bundle["disclosure_scope"],
              "visibility": bundle.get("visibility", "restricted")}
    return {**result, "aggregate_hash": fingerprint(result)}


def aggregate_stratum(rows, baseline, candidates, *, descriptive_intervals=True):
    """Average seeds inside a block, then compare only matching strata."""
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["arm_id"]].append(row)
    arms, complete_blocks = [], {}
    for arm_id, cells in sorted(grouped.items()):
        blocks = defaultdict(list)
        for cell in cells:
            blocks[cell["block_id"]].append(cell)
        complete = {block_id: values for block_id, values in blocks.items()
                    if all(c["status"] == "SUCCEEDED" for c in values)}
        block_metrics = {block_id: {metric: mean(c["metrics"][metric] for c in values)
                                   for metric in values[0]["metrics"]} for block_id, values in complete.items()}
        complete_blocks[arm_id] = block_metrics
        successful = [c for c in cells if c["status"] == "SUCCEEDED"]
        metrics = {metric: mean(block[metric] for block in block_metrics.values())
                   for metric in next(iter(block_metrics.values()), {})}
        dispositions = dict(sorted(Counter(c["status"] for c in cells).items()))
        arms.append({"arm_id": arm_id, "expected_cells": len(cells), "successful_cells": len(successful),
                     "cost": summarize_cost(cells),
                     "dispositions": dispositions,
                     "status_rates": {"denominator": len(cells), "denominator_kind": "registered-cells-in-arm-stratum",
                                      "unit": "fraction", "values": {state: count / len(cells) for state, count in dispositions.items()}},
                     "expected_blocks": len(blocks), "independent_n": len(complete),
                     "complete_block_ids": sorted(complete), "incomplete_block_ids": sorted(set(blocks) - complete.keys()),
                     "metrics": metrics, "metric_units": successful[0]["metric_units"] if successful else {},
                     "status": "complete" if len(complete) == len(blocks) else "incomplete"})
    comparisons = []
    # Deterministic reference ordering is explicit in the aggregate, not a claim
    # that alphabetical order constitutes scientific preregistration.
    if candidates:
        for candidate_id in candidates:
            reference_blocks = complete_blocks.get(baseline, {})
            candidate_blocks = complete_blocks.get(candidate_id, {})
            shared = sorted(reference_blocks.keys() & candidate_blocks.keys())
            metrics = {}
            for metric in reference_blocks.get(shared[0], {}) if shared else ():
                differences = [candidate_blocks[b][metric] - reference_blocks[b][metric] for b in shared]
                interval = None
                if descriptive_intervals and len(shared) >= 2:
                    rng = random.Random(20260929)
                    estimates = sorted(mean(rng.choices(differences, k=len(differences))) for _ in range(1000))
                    interval = [estimates[24], estimates[974]]
                metrics[metric] = {"candidate_minus_reference": mean(differences), "interval95": interval}
            comparisons.append({"reference": baseline, "candidate": candidate_id, "paired_block_ids": shared,
                                "status": "comparable" if shared else "no-complete-paired-blocks",
                                "absent_arms": [arm for arm in (baseline, candidate_id) if arm not in grouped],
                                "independent_n": len(shared), "metrics": metrics,
                                "interval_kind": ("paired-block-percentile-bootstrap" if len(shared) >= 2 else "insufficient-independent-blocks")
                                                 if descriptive_intervals else "descriptive-point-only-see-adjudication",
                                "bootstrap_seed": 20260929 if descriptive_intervals else None,
                                "bootstrap_replicates": 1000 if descriptive_intervals else 0})
    return arms, comparisons


def csv_bytes(aggregate_value):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    extra = [name for name in ("adjudication", "computation_ref") if name in aggregate_value]
    writer.writerow(["aggregate_hash", "arm_id", "metric", "value", "unit", "independent_n", "expected_cells", "successful_cells", "status", "stratum_id", "comparison_dimensions", "charged_ms", "reserved_ms", "measured_ms", "cost_unit", "cost_scope", "status_rates", *extra])
    frozen = [canonical(aggregate_value[name]).decode() for name in extra]
    for arm in aggregate_value["arms"]:
        costs = [arm["cost"][key] for key in ("charged_ms", "reserved_ms", "measured_ms", "unit", "scope")]
        rates = canonical(arm.get("status_rates")).decode()
        if not arm["metrics"]:
            writer.writerow([aggregate_value["aggregate_hash"], arm["arm_id"], "", "", "", arm["independent_n"],
                             arm["expected_cells"], arm["successful_cells"], arm["status"], arm["stratum_id"], canonical(arm["comparison_dimensions"]).decode(), *costs, rates, *frozen])
        for metric, value in sorted(arm["metrics"].items()):
            writer.writerow([aggregate_value["aggregate_hash"], arm["arm_id"], metric, value, arm["metric_units"][metric],
                             arm["independent_n"], arm["expected_cells"], arm["successful_cells"], arm["status"], arm["stratum_id"], canonical(arm["comparison_dimensions"]).decode(), *costs, rates, *frozen])
    return stream.getvalue().encode()


def evidence_index(value, csv_content):
    return {"schema_version": "pirc25-paper-evidence-v1", "study_id": value["study_id"],
            "aggregate_hash": value["aggregate_hash"], "table_sha256": hashlib.sha256(csv_content).hexdigest(),
            "code_hash": value["code_hash"], "evidence_status": "active", "relation": None,
            "disclosure_scope": value["disclosure_scope"],
            **{name: value[name] for name in ("adjudication", "computation_ref") if name in value}, "claims": [
                {"claim_id": fingerprint([arm['arm_id'], arm['stratum_id'], metric]), "metric": metric, "value": number,
                 "arm_id": arm["arm_id"], "stratum_id": arm["stratum_id"], "comparison_dimensions": arm["comparison_dimensions"],
                 "evidence_status": arm["status"], "independent_n": arm["independent_n"],
                 "cost": arm["cost"],
                 "unit": arm["metric_units"][metric], "aggregate_hash": value["aggregate_hash"],
                 "attempt_ids": [c["attempt_id"] for c in value["cell_dispositions"]
                                 if c["arm_id"] == arm["arm_id"] and c["status"] == "SUCCEEDED"
                                 and c["block_id"] in arm["complete_block_ids"]
                                 and canonical(comparison_dimensions(c)) == canonical(arm["comparison_dimensions"])]}
                for arm in value["arms"] for metric, number in sorted(arm["metrics"].items())]}


def write_package(bundle, output: Path, *, formal=False):
    value = aggregate(bundle, formal=formal)
    table = csv_bytes(value)
    index = evidence_index(value, table)
    output = output.resolve()
    if any((parent / ".git").exists() for parent in (output, *output.parents)):
        raise ValueError("generated evidence must stay outside Git")
    output.parent.mkdir(parents=True, exist_ok=True)
    files = {"aggregate.json": canonical(value), "metrics.csv": table, "PaperEvidenceIndex.json": canonical(index)}
    files["manifest.json"] = canonical({"schema_version": "pirc25-evidence-package-v1",
        "aggregate_hash": value["aggregate_hash"], "files": {name: hashlib.sha256(content).hexdigest() for name, content in files.items()}})
    if output.exists():
        if any(not (output / name).is_file() or (output / name).read_bytes() != content for name, content in files.items()):
            raise ValueError("evidence package is immutable; choose a new output version")
        return value
    staging = Path(tempfile.mkdtemp(prefix=".evidence-", dir=output.parent))
    for name, content in files.items():
        with (staging / name).open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    staging.rename(output)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--expected-hash", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--formal", action="store_true")
    args = parser.parse_args()
    bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
    if bundle.get("bundle_hash") != args.expected_hash:
        parser.error("unexpected source bundle hash")
    value = write_package(bundle, args.output, formal=args.formal)
    print(json.dumps({"aggregate_hash": value["aggregate_hash"], "expected_cells": value["expected_cell_count"]}))


if __name__ == "__main__":
    main()
