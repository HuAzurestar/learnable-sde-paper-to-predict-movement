"""Frozen-policy paired-block adjudication, without runtime/training imports.

This is a bounded statistical kernel, not a job supervisor. Production compare
must invoke it inside the shared budget boundary. Fixture verdicts remain
engineering-only; formal mode additionally verifies the frozen admission chain.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import math
import random
from statistics import mean

if __package__:
    from .dimensions import comparison_dimensions
    from .costs import summarize_cost
else:
    from dimensions import comparison_dimensions
    from costs import summarize_cost


SCHEMA = "pirc25-adjudication-spec-v1"
REQUIRED = ("schema_version", "primary_metric", "independent_unit", "seed_aggregation",
            "minimum_seeds", "minimum_paired_blocks", "interval", "multiplicity",
            "practical_threshold", "attempt_policy", "missing_policy", "stopping_rule", "quality_gates", "contrasts")
FAILED = frozenset({"FAILED", "INTERRUPTED", "TIMEOUT", "BUDGET_EXHAUSTED", "PREFLIGHT_FAILED", "CANCELLED"})
MAX_OPERATIONS = 20_000_000


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def fingerprint(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError("invalid AdjudicationSpec: " + message)


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def missing_policy_fields(spec):
    if spec is None:
        return ["adjudication_spec"]
    require(isinstance(spec, dict), "policy must be a mapping")
    missing = [key for key in REQUIRED if spec.get(key) is None]
    for key, fields in (("primary_metric", ("name", "definition", "unit", "direction")),
                        ("interval", ("method", "confidence", "replicates", "seed"))):
        if key not in missing:
            require(isinstance(spec[key], dict), key + " must be a mapping")
            missing.extend(key + "." + field for field in fields if spec[key].get(field) is None)
    if "quality_gates" not in missing:
        require(isinstance(spec["quality_gates"], dict), "quality gates must be a mapping")
        missing.extend("quality_gates." + field for field in ("minimum_ess", "maximum_reference_error")
                       if field not in spec["quality_gates"])
    return missing


def validate_policy(spec):
    """Missing decisions are diagnostic, never replaced by test-driven defaults."""
    missing = missing_policy_fields(spec)
    if missing:
        return missing
    require(set(spec) == set(REQUIRED) and spec["schema_version"] == SCHEMA, "schema/unsupported fields")
    metric = spec["primary_metric"]
    require(set(metric) == {"name", "definition", "unit", "direction"}, "primary metric schema")
    require(all(isinstance(metric[k], str) and metric[k].strip() for k in ("name", "definition", "unit")),
            "versioned metric definition and unit required")
    require(metric["direction"] in {"minimize", "maximize"}, "primary direction")
    require(spec["independent_unit"] == "block_id" and spec["seed_aggregation"] == "mean-within-block", "sampling/seed policy")
    require(type(spec["minimum_seeds"]) is int and spec["minimum_seeds"] >= 1, "minimum seeds")
    require(type(spec["minimum_paired_blocks"]) is int and spec["minimum_paired_blocks"] >= 2, "minimum paired blocks")
    interval = spec["interval"]
    require(set(interval) == {"method", "confidence", "replicates", "seed"}, "interval schema")
    require(interval["method"] == "paired-block-percentile-bootstrap", "unsupported interval method")
    require(number(interval["confidence"]) and 0 < interval["confidence"] < 1, "confidence")
    require(type(interval["replicates"]) is int and 200 <= interval["replicates"] <= 10000, "bounded bootstrap replicates")
    require(type(interval["seed"]) is int and 0 <= interval["seed"] < 2**64, "explicit bootstrap seed")
    require(number(spec["practical_threshold"]) and spec["practical_threshold"] >= 0, "nonnegative practical threshold")
    require(spec["attempt_policy"] == "first-successful-attempt", "best-retry selection is prohibited")
    require(spec["missing_policy"] == "exclude-incomplete-paired-blocks", "missing/failure policy")
    require(spec["stopping_rule"] == "fixed-family-no-test-driven-expansion", "fixed stopping rule")
    gates = spec["quality_gates"]
    require(set(gates) == {"minimum_ess", "maximum_reference_error"}, "quality gate schema")
    require(gates["minimum_ess"] is None or (number(gates["minimum_ess"]) and gates["minimum_ess"] > 0), "minimum ESS")
    require(gates["maximum_reference_error"] is None or
            (number(gates["maximum_reference_error"]) and gates["maximum_reference_error"] >= 0), "reference error bound")
    contrasts = spec["contrasts"]
    require(isinstance(contrasts, list) and 0 < len(contrasts) <= 256, "bounded fixed comparison family")
    ids = set()
    for contrast in contrasts:
        require(isinstance(contrast, dict) and set(contrast) == {"comparison_id", "reference", "candidate", "stratum_weights"},
                "contrast schema")
        require(all(isinstance(contrast[k], str) and contrast[k].strip() for k in ("comparison_id", "reference", "candidate")),
                "contrast identities")
        require(contrast["reference"] != contrast["candidate"] and contrast["comparison_id"] not in ids, "duplicate/identical comparison")
        ids.add(contrast["comparison_id"])
        weights = contrast["stratum_weights"]
        require(isinstance(weights, list) and 0 < len(weights) <= 256, "explicit bounded horizon/stratum weights")
        strata = set()
        for item in weights:
            require(isinstance(item, dict) and set(item) == {"comparison_dimensions", "weight"}, "weight schema")
            dimensions = comparison_dimensions(item)
            require(canonical(dimensions) not in strata, "duplicate weighted stratum")
            strata.add(canonical(dimensions))
            require(number(item["weight"]) and item["weight"] > 0, "positive finite weight")
        require(math.isclose(math.fsum(item["weight"] for item in weights), 1, rel_tol=0, abs_tol=1e-12), "weights must sum to one")
    require(spec["multiplicity"] in {"bonferroni", "none"} and
            (spec["multiplicity"] != "none" or len(contrasts) == 1), "multiplicity correction required for a family")
    # A nominal tail smaller than one empirical order statistic would give a
    # false precision claim. Reject it instead of fabricating a 100% interval.
    tail = (1 - interval["confidence"]) / (2 * len(contrasts) if spec["multiplicity"] == "bonferroni" else 2)
    require(tail * interval["replicates"] >= 1, "replicates cannot resolve corrected interval tails")
    return []


def _check_source_policy(bundle, rows, spec, formal):
    plan = bundle["comparison_plan"]
    references = {c["reference"] for c in spec["contrasts"]}
    candidates = {c["candidate"] for c in spec["contrasts"]}
    require(references == {plan.get("reference_arm_id")} and candidates == set(plan.get("candidate_arm_ids", [])),
            "policy family differs from registered comparison plan")
    require(plan.get("failure_policy") == "retain-and-exclude-incomplete-blocks", "plan failure policy")
    for row in rows.values():
        require(type(row["seed"]) is int, "seed must be an integer identity")
        history = row.get("history", [])
        require(isinstance(history, list), "attempt history")
        attempts = set()
        for item in history:
            require(isinstance(item, dict) and isinstance(item.get("attempt_id"), str) and item["attempt_id"] and
                    item.get("state") in FAILED | {"REGISTERED", "RUNNING", "SUCCEEDED"} and
                    item["attempt_id"] not in attempts, "invalid/duplicate attempt history")
            attempts.add(item["attempt_id"])
        if row["status"] == "SUCCEEDED" and history:
            successful = [a for a in history if a.get("state") == "SUCCEEDED"]
            require(bool(successful) and successful[0].get("attempt_id") == row["attempt_id"], "first successful attempt must be selected")
        if row["status"] != "SUCCEEDED":
            continue
        metric = spec["primary_metric"]
        require(metric["name"] in row["metrics"] and row["metric_units"].get(metric["name"]) == metric["unit"],
                "primary metric unit/identity differs")
        require(row.get("metric_definitions", {}).get(metric["name"]) == metric["definition"], "primary metric estimator definition differs")
        if formal:
            # validate_bundle(formal=True) checked receipt identities and that
            # this preregistration's publication preceded completed test reads.
            prereg = row["admission"]["documents"]["preregistration"]
            require(prereg.get("adjudication_spec") == spec, "policy was not frozen in preregistration before exposure")
            require(bool(history), "formal source requires complete attempt history")


def _counts(cells):
    statuses = dict(sorted(Counter(c["status"] for c in cells).items()))
    count = len(cells)
    attempted = sum(bool(c.get("attempt_id") or c.get("history")) for c in cells)
    attempt_statuses = Counter()
    complete = True
    for cell in cells:
        history = cell.get("history", [])
        if history:
            attempt_statuses.update(a["state"] for a in history)
        elif cell.get("attempt_id"):
            attempt_statuses[cell["status"]] += 1
            complete = False  # selected legacy attempts do not prove full history
    return {
        "cell_counts": {"expected": count, "attempted": attempted,
                        "successful": statuses.get("SUCCEEDED", 0),
                        "failed": sum(statuses.get(s, 0) for s in FAILED), "missing": statuses.get("MISSING", 0),
                        "dispositions": statuses},
        "attempt_counts": {"complete_history": complete, "observed": sum(attempt_statuses.values()),
                           "successful": attempt_statuses["SUCCEEDED"],
                           "failed": sum(attempt_statuses[s] for s in FAILED), "dispositions": dict(sorted(attempt_statuses.items()))},
        "status_rates": {"denominator": count, "denominator_kind": "all-registered-cells-in-comparison",
                         "unit": "fraction", "values": {s: n / count for s, n in statuses.items()}},
    }


def _block_values(cells, metric, minimum_seeds):
    blocks = defaultdict(list)
    for cell in cells:
        blocks[cell["block_id"]].append(cell)
    return {block: (mean(c["metrics"][metric] for c in values), frozenset(c["seed"] for c in values))
            for block, values in blocks.items() if len(values) >= minimum_seeds and
            all(c["status"] == "SUCCEEDED" for c in values)}


def _prepare_record(rows, contrast, spec, family_size):
    strata = {canonical(w["comparison_dimensions"]): w["weight"] for w in contrast["stratum_weights"]}
    cells = [c for c in rows.values() if c["arm_id"] in (contrast["reference"], contrast["candidate"]) and
             canonical(comparison_dimensions(c)) in strata]
    record = {"schema_version": "pirc25-compare-record-v1", **contrast, **_counts(cells),
              "primary_metric": spec["primary_metric"], "practical_threshold": spec["practical_threshold"],
              "minimum_paired_blocks": spec["minimum_paired_blocks"], "minimum_seeds": spec["minimum_seeds"],
              "cost": summarize_cost(cells), "family_size": family_size, "multiplicity": spec["multiplicity"],
              "paired_block_ids": [], "independent_n": 0, "candidate_minus_reference": None,
              "effect": None, "interval": None, "interval_conditional_on": "successful-complete-paired-blocks",
              "interval_kind": spec["interval"]["method"], "bootstrap_replicates": spec["interval"]["replicates"],
              "bootstrap_seed": spec["interval"]["seed"], "family_confidence": spec["interval"]["confidence"],
              "interval_confidence": 1 - (1 - spec["interval"]["confidence"]) / (family_size if spec["multiplicity"] == "bonferroni" else 1),
              "unit": spec["primary_metric"]["unit"], "verdict": "INSUFFICIENT_DATA", "stop_expansion": True,
              "equivalence_claim": False, "diagnostics": []}
    gates = spec["quality_gates"]
    for name, threshold in (("ess", gates["minimum_ess"]), ("reference_error", gates["maximum_reference_error"])):
        if threshold is None:
            continue  # explicit predeclared not-applicable, not an inferred default
        for cell in cells:
            if cell["status"] != "SUCCEEDED":
                continue
            value = cell.get("comparison_diagnostics", {}).get(name)
            if (not number(value) or value < 0 or
                    (value < threshold if name == "ess" else value > threshold)):
                record.update(verdict="INAPPLICABLE", diagnostics=[name + " unknown or failed preregistered quality gate"])
                return record, []
    values = {}
    for stratum in strata:
        grouped = {arm: [c for c in cells if c["arm_id"] == arm and canonical(comparison_dimensions(c)) == stratum]
                   for arm in (contrast["reference"], contrast["candidate"])}
        if not all(grouped.values()):
            record.update(verdict="INAPPLICABLE", diagnostics=["registered arm/weighted stratum unavailable"])
            return record, []
        reference = _block_values(grouped[contrast["reference"]], spec["primary_metric"]["name"], spec["minimum_seeds"])
        candidate = _block_values(grouped[contrast["candidate"]], spec["primary_metric"]["name"], spec["minimum_seeds"])
        values[stratum] = {b: candidate[b][0] - reference[b][0] for b in reference.keys() & candidate.keys()
                           if reference[b][1] == candidate[b][1]}
    shared = sorted(set.intersection(*(set(blocks) for blocks in values.values())))
    differences = [math.fsum(strata[s] * values[s][b] for s in strata) for b in shared]
    require(all(math.isfinite(v) for v in differences), "nonfinite block difference")
    record.update(paired_block_ids=shared, independent_n=len(shared),
                  candidate_minus_reference=mean(differences) if differences else None)
    if len(shared) < spec["minimum_paired_blocks"]:
        record["diagnostics"].append("minimum complete paired blocks/seeds not met")
        return record, []
    oriented = [v * (-1 if spec["primary_metric"]["direction"] == "minimize" else 1) for v in differences]
    record["effect"] = mean(oriented)
    return record, oriented


def _percentile(sorted_values, probability):
    index = (len(sorted_values) - 1) * probability
    lower, upper = math.floor(index), math.ceil(index)
    return math.fsum((sorted_values[lower] * (1 - (index - lower)), sorted_values[upper] * (index - lower)))


def _adjudicate(bundle, *, formal=False, max_operations=MAX_OPERATIONS):
    """Compute a content-bound CompareRecord family from its frozen policy.

    No caller-supplied policy override is accepted. Complexity is bounded before
    resampling; each replicate samples blocks, never all pairs of windows.
    """
    if __package__:
        from .aggregate import validate_bundle
    else:
        from aggregate import validate_bundle
    require(isinstance(bundle, dict) and isinstance(bundle.get("cells"), list) and
            len(bundle["cells"]) <= 100_000, "RESOURCE_PLAN_REJECTED cell quota")
    rows = validate_bundle(bundle, formal=formal)
    require(type(max_operations) is int and 0 < max_operations <= MAX_OPERATIONS, "RESOURCE_PLAN_REJECTED operation quota")
    plan = bundle.get("comparison_plan") or {}
    spec = plan.get("adjudication_spec")
    if spec is not None:
        require(plan.get("adjudication_hash") == fingerprint(spec), "policy hash differs from frozen plan")
    missing = validate_policy(spec)
    result = {"schema_version": "pirc25-compare-v1", "study_id": bundle["study_id"],
              "spec_hash": bundle["spec_hash"], "protocol_hash": bundle["protocol_hash"],
              "source_bundle_hash": bundle["bundle_hash"], "adjudication_hash": fingerprint(spec) if spec is not None else None,
              "adjudication_spec": spec,
              "qualification": "formal" if formal else "engineering-fixture", "independent_unit": "block_id",
              "status": "NEEDS_PREREGISTRATION" if missing else "COMPUTED", "diagnostics": missing,
              "family_size": 0 if missing else len(spec["contrasts"]), "records": []}
    if not missing:
        # Bound preparation as well as resampling, before repeatedly grouping
        # any strata. Never construct a windows-by-windows matrix.
        preparation = len(rows) * sum(1 + 2 * len(c["stratum_weights"]) for c in spec["contrasts"])
        require(preparation <= max_operations, "RESOURCE_PLAN_REJECTED preparation operation quota")
        _check_source_policy(bundle, rows, spec, formal)
        prepared = [_prepare_record(rows, contrast, spec, len(spec["contrasts"])) for contrast in spec["contrasts"]]
        operations = spec["interval"]["replicates"] * sum(len(values) for _, values in prepared)
        require(preparation + operations <= max_operations, "RESOURCE_PLAN_REJECTED bootstrap operation quota")
        for record, values in prepared:
            if values:
                # Independent deterministic streams preserve fixed family order;
                # skipping an unavailable contrast never changes another result.
                seed = fingerprint([spec["interval"]["seed"], record["comparison_id"]])
                rng = random.Random(seed)
                estimates = sorted(mean(rng.choices(values, k=len(values))) for _ in range(spec["interval"]["replicates"]))
                tail = (1 - record["interval_confidence"]) / 2
                lower, upper = _percentile(estimates, tail), _percentile(estimates, 1 - tail)
                record["interval"] = [lower, upper]
                threshold = spec["practical_threshold"]
                record["verdict"] = "GAIN" if lower > threshold else "NO_GAIN" if upper <= threshold else "STATISTICALLY_UNCERTAIN"
                # Even a gain does not authorize data-driven expansion. The
                # registered matrix/family remains fixed for every verdict.
            result["records"].append(record)
        result["resource_plan"] = {"preparation_operations": preparation, "bootstrap_operations": operations,
                                   "planned_operations": preparation + operations, "maximum_operations": max_operations,
                                   "complexity": "replicates-times-paired-blocks-times-fixed-contrasts"}
    return {**result, "compare_hash": fingerprint(result)}


def adjudicate(bundle, *, formal=False, max_operations=MAX_OPERATIONS):
    try:
        return _adjudicate(bundle, formal=formal, max_operations=max_operations)
    except (KeyError, TypeError, AttributeError, OverflowError) as exc:
        raise ValueError("malformed adjudication evidence") from exc
