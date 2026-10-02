"""Synthetic contract counterexamples; no research qualification is inferred."""

from copy import deepcopy

import pytest

from scripts.pirc25.aggregate import fingerprint
from test_shared_evidence import bundle, seal


def policy():
    return {
        "schema_version": "pirc25-adjudication-spec-v1",
        "primary_metric": {"name": "error", "definition": "synthetic-error-v1", "unit": "m", "direction": "minimize"},
        "independent_unit": "block_id", "seed_aggregation": "mean-within-block",
        "minimum_seeds": 2, "minimum_paired_blocks": 2,
        "interval": {"method": "paired-block-percentile-bootstrap", "confidence": 0.95, "replicates": 2000, "seed": 19},
        "multiplicity": "bonferroni", "practical_threshold": 0.5,
        "attempt_policy": "first-successful-attempt", "missing_policy": "exclude-incomplete-paired-blocks",
        "stopping_rule": "fixed-family-no-test-driven-expansion",
        "quality_gates": {"minimum_ess": None, "maximum_reference_error": None},
        "contrasts": [{"comparison_id": "primary", "reference": "baseline", "candidate": "candidate",
                       "stratum_weights": [{"comparison_dimensions": {}, "weight": 1.0}]}],
    }


def evidence(spec=None):
    value = bundle()
    spec = policy() if spec is None else spec
    value["comparison_plan"] = {"reference_arm_id": "baseline", "candidate_arm_ids": ["candidate"],
        "failure_policy": "retain-and-exclude-incomplete-blocks", "adjudication_spec": spec,
        "adjudication_hash": fingerprint(spec)}
    for row in value["cells"]:
        row["metric_definitions"] = {"error": "synthetic-error-v1"}
    return seal(value)


def compare(value, **kwargs):
    # Deliberately imported inside each check: baseline has no implementation,
    # so the missing contract is reproduced as test failures, not a skip.
    from scripts.pirc25.adjudication import adjudicate
    return adjudicate(value, **kwargs)


def test_known_effect_is_oriented_and_seeds_remain_inside_blocks():
    value = compare(evidence())
    record = value["records"][0]
    assert record["verdict"] == "GAIN"
    assert record["independent_n"] == 2
    assert record["effect"] == 1 and record["candidate_minus_reference"] == -1
    assert record["interval"] == [1, 1]
    assert record["interval_conditional_on"] == "successful-complete-paired-blocks"
    assert value["qualification"] == "engineering-fixture"
    assert value["source_bundle_hash"] == evidence()["bundle_hash"]
    assert value["compare_hash"] == fingerprint({k: v for k, v in value.items() if k != "compare_hash"})


def test_no_effect_is_not_invented_from_nonsignificance():
    value = evidence()
    for row in value["cells"]:
        if row["arm_id"] == "candidate":
            row["metrics"]["error"] += 1
    record = compare(seal(value))["records"][0]
    assert record["verdict"] == "NO_GAIN" and record["interval"] == [0, 0]
    assert record["stop_expansion"] is True
    assert record["equivalence_claim"] is False


def test_uncertain_effect_is_not_equivalence_or_no_gain():
    value = evidence()
    for row in value["cells"]:
        if row["arm_id"] == "candidate" and row["block_id"] == "block2":
            row["metrics"]["error"] += 2
    assert compare(seal(value))["records"][0]["verdict"] == "STATISTICALLY_UNCERTAIN"


def test_direction_is_preregistered_not_chosen_from_winner():
    spec = policy()
    spec["primary_metric"]["direction"] = "maximize"
    record = compare(evidence(spec))["records"][0]
    assert record["effect"] == -1 and record["verdict"] == "NO_GAIN"


@pytest.mark.parametrize("field", ["practical_threshold", "minimum_seeds", "minimum_paired_blocks", "interval", "stopping_rule"])
def test_missing_threshold_does_not_get_a_default(field):
    spec = policy()
    spec.pop(field)
    value = compare(evidence(spec))
    assert value["status"] == "NEEDS_PREREGISTRATION"
    assert field in value["diagnostics"] and value["records"] == []


def test_missing_policy_does_not_claim_formal_conclusion():
    value = compare(bundle())
    assert value["status"] == "NEEDS_PREREGISTRATION" and not value["records"]


@pytest.mark.parametrize("status", ["FAILED", "TIMEOUT", "MISSING", "RUNNING"])
def test_failures_and_missing_stay_in_full_matrix_denominator(status):
    value = evidence()
    row = value["cells"][0]
    row.update(status=status, metrics=None)
    if status == "MISSING":
        row.update(attempt_id=None, artifact_id=None)
    record = compare(seal(value))["records"][0]
    assert record["verdict"] == "INSUFFICIENT_DATA" and record["interval"] is None
    assert record["independent_n"] == 1
    assert record["cell_counts"]["expected"] == 8 and record["cell_counts"]["successful"] == 7
    assert record["status_rates"]["denominator"] == 8
    assert record["status_rates"]["values"][status] == 1 / 8
    assert record["cost"]["charged_ms"] is None  # legacy cost is unavailable, never free


def test_seed_minimum_cannot_be_replaced_by_more_blocks():
    value = evidence()
    value["cells"] = [row for row in value["cells"] if row["seed"] == 1]
    value["expected_cells"] = [row for row in value["expected_cells"] if row["seed"] == 1]
    record = compare(seal(value))["records"][0]
    assert record["verdict"] == "INSUFFICIENT_DATA" and record["independent_n"] == 0


def test_horizon_weights_are_applied_per_independent_block():
    spec = policy()
    weights = [{"comparison_dimensions": {"horizon": h}, "weight": w} for h, w in ((1, 0.25), (2, 0.75))]
    spec["contrasts"][0]["stratum_weights"] = weights
    value = evidence(spec)
    cells, expected = [], []
    for horizon in (1, 2):
        for original in value["cells"]:
            row = deepcopy(original)
            row["comparison_dimensions"] = {"horizon": horizon}
            row["cell_hash"] = fingerprint([row["arm_id"], row["block_id"], row["seed"], horizon])
            if horizon == 2 and row["arm_id"] == "candidate":
                row["metrics"]["error"] -= 2
            cells.append(row)
            expected.append({k: row[k] for k in ("cell_hash", "arm_id", "block_id", "seed", "comparison_dimensions")})
    value.update(cells=cells, expected_cells=expected)
    record = compare(seal(value))["records"][0]
    assert record["effect"] == 2.5 and record["independent_n"] == 2
    assert record["stratum_weights"] == weights


def test_multiplicity_family_includes_unavailable_contrasts():
    spec = policy()
    spec["contrasts"].append({"comparison_id": "secondary", "reference": "baseline", "candidate": "candidate",
        "stratum_weights": [{"comparison_dimensions": {"horizon": 999}, "weight": 1.0}]})
    value = compare(evidence(spec))
    assert value["family_size"] == 2
    assert value["records"][0]["interval_confidence"] == pytest.approx(0.975)
    assert value["records"][1]["verdict"] == "INAPPLICABLE"
    assert value["records"][0]["family_size"] == 2


@pytest.mark.parametrize("mutation", ["hash", "unit", "definition", "duplicate-family", "negative-weight", "bool-threshold", "no-correction", "oversized-bootstrap"])
def test_invalid_or_unbound_policy_cannot_produce_a_verdict(mutation):
    spec = policy()
    if mutation == "duplicate-family":
        spec["contrasts"].append(deepcopy(spec["contrasts"][0]))
    elif mutation == "negative-weight":
        spec["contrasts"][0]["stratum_weights"][0]["weight"] = -1
    elif mutation == "bool-threshold":
        spec["practical_threshold"] = True
    elif mutation == "no-correction":
        spec["multiplicity"] = "none"
        second = deepcopy(spec["contrasts"][0])
        second["comparison_id"] = "second"
        spec["contrasts"].append(second)
    elif mutation == "oversized-bootstrap":
        spec["interval"]["replicates"] = 100000000
    value = evidence(spec)
    if mutation == "hash":
        value["comparison_plan"]["adjudication_hash"] = "a" * 64
    elif mutation == "unit":
        for row in value["cells"]:
            row["metric_units"]["error"] = "km"
    elif mutation == "definition":
        for row in value["cells"]:
            row["metric_definitions"]["error"] = "another-estimator-v1"
    with pytest.raises(ValueError):
        compare(seal(value))


def test_complete_attempt_history_cannot_select_best_retry():
    value = evidence()
    row = value["cells"][0]
    row["history"] = [{"attempt_id": "earlier-success", "state": "SUCCEEDED"},
                       {"attempt_id": row["attempt_id"], "state": "SUCCEEDED"}]
    with pytest.raises(ValueError, match="first successful"):
        compare(seal(value))


def test_computation_quota_is_checked_before_resampling():
    with pytest.raises(ValueError, match="RESOURCE_PLAN_REJECTED"):
        compare(evidence(), max_operations=1)


@pytest.mark.parametrize("gate,diagnostic,value", [("minimum_ess", "ess", 1.0),
                                                  ("maximum_reference_error", "reference_error", None)])
def test_low_ess_and_unknown_reference_error_are_explicit(gate, diagnostic, value):
    spec = policy()
    spec["quality_gates"][gate] = 2 if gate == "minimum_ess" else 0.1
    evidence_value = evidence(spec)
    for row in evidence_value["cells"]:
        row["comparison_diagnostics"] = {diagnostic: value}
    record = compare(seal(evidence_value))["records"][0]
    assert record["verdict"] == "INAPPLICABLE" and record["interval"] is None
    assert any(diagnostic in message for message in record["diagnostics"])


def test_failed_attempt_before_success_remains_in_attempt_denominator():
    value = evidence()
    row = value["cells"][0]
    row["history"] = [{"attempt_id": "failed-first", "state": "FAILED"},
                       {"attempt_id": row["attempt_id"], "state": "SUCCEEDED"}]
    record = compare(seal(value))["records"][0]
    assert record["verdict"] == "GAIN" and record["attempt_counts"]["failed"] == 1
    assert record["attempt_counts"]["observed"] == 9
    assert record["attempt_counts"]["complete_history"] is False
    assert record["cell_counts"]["failed"] == 0


def test_frozen_policy_and_full_computation_plan_are_in_compare_record():
    value = compare(evidence())
    assert value["adjudication_spec"] == policy()
    assert value["resource_plan"]["planned_operations"] >= value["resource_plan"]["bootstrap_operations"]
    assert value["resource_plan"]["planned_operations"] <= value["resource_plan"]["maximum_operations"]


@pytest.mark.parametrize("mutation", ["duplicate-attempt", "unknown-attempt-state", "corrected-tail-too-small"])
def test_extra_contract_counterexamples_fail_closed(mutation):
    spec = policy()
    if mutation == "corrected-tail-too-small":
        spec["interval"]["confidence"] = 0.99999
    value = evidence(spec)
    if mutation == "duplicate-attempt":
        row = value["cells"][0]
        row["history"] = [{"attempt_id": row["attempt_id"], "state": "SUCCEEDED"}] * 2
    elif mutation == "unknown-attempt-state":
        value["cells"][0]["history"] = [{"attempt_id": "unknown", "state": "UNKNOWN_STATE"}]
    with pytest.raises(ValueError):
        compare(seal(value))


def differing_seeds(value):
    for row, expected in zip(value["cells"], value["expected_cells"]):
        if row["arm_id"] == "candidate":
            row["seed"] += 10
            row["cell_hash"] = fingerprint([row["arm_id"], row["block_id"], row["seed"]])
            expected.update(seed=row["seed"], cell_hash=row["cell_hash"])
    return seal(value)


def test_seed_pairing_must_be_a_frozen_decision():
    spec = policy()
    spec.pop("seed_pairing", None)
    result = compare(evidence(spec))
    assert result["status"] == "NEEDS_PREREGISTRATION" and "seed_pairing" in result["diagnostics"]


@pytest.mark.parametrize("pairing,verdict,n", [("independent-within-block", "GAIN", 2),
                                             ("identical-registered-seeds", "INSUFFICIENT_DATA", 0)])
def test_block_pairing_does_not_silently_impose_seed_pairing(pairing, verdict, n):
    spec = policy()
    spec["seed_pairing"] = pairing
    record = compare(differing_seeds(evidence(spec)))["records"][0]
    assert record["verdict"] == verdict and record["independent_n"] == n
    assert record["seed_pairing"] == pairing
