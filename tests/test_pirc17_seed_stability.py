"""Saved aggregate arithmetic/presentation only, not empirical qualification."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.describe_pirc17_seed_stability import SOURCES, summarize, table_tex, display

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"


def inputs():
    return tuple(json.loads((PAPER/name).read_text(encoding="utf-8")) for name in SOURCES)


def test_complete_original_projection_and_controls_are_exact():
    inference, stage = inputs()
    result = summarize(inference, stage)
    assert result["direction_row_counts"] == {"all_positive": 6, "all_negative": 7,
                                              "mixed_or_zero": 6, "all_exact_zero": 2}
    assert result["seed_ids"] == stage["forecast_seeds"]
    assert len(result["comparisons"]) == 21
    for new, old in zip(result["comparisons"], stage["comparisons"]):
        for field in ("family_id", "candidate", "control", "seed_delta_m"):
            assert new[field] == old[field]
        assert new["original_simultaneous_interval_m"] == old["simultaneous_interval_m"]
        assert sum(new["sign_counts"].values()) == 5
        assert new["seed_range_m"] == max(old["seed_delta_m"])-min(old["seed_delta_m"])
    for name, digest in SOURCES.items():
        assert hashlib.sha256((PAPER/name).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "control", "seed_missing",
                                    "nan", "boolean", "mismatch", "mean", "seed_order", "rows", "audit"])
def test_malformed_or_incomplete_inputs_fail_not_silently_drop(mutation):
    a, b = deepcopy(inputs())
    rows = a["primary_method_diagnostics"]
    if mutation == "missing": rows.pop()
    elif mutation == "duplicate": rows[-1] = deepcopy(rows[0])
    elif mutation == "control": rows[0]["control"] = "arm-07/full"
    elif mutation == "seed_missing": rows[0]["seed_delta_m"].pop()
    elif mutation == "nan": rows[0]["seed_delta_m"][0] = float("nan")
    elif mutation == "boolean": rows[0]["seed_delta_m"][0] = True
    elif mutation == "mismatch": rows[0]["seed_delta_m"][0] += 1
    elif mutation == "mean":
        rows[0]["delta_estimate_m"] += 1
        b["comparisons"][0]["delta_estimate_m"] += 1
    elif mutation == "seed_order": b["forecast_seeds"].reverse()
    elif mutation == "rows": b["primary_method_rows"] -= 1
    elif mutation == "audit": b["independent_raw_output_audit_completed"] = True
    with pytest.raises(ValueError):
        summarize(a, b)


def test_seed_agreement_does_not_relabel_intervals_or_aliases():
    result = summarize(*inputs())
    rows = {r["candidate"]: r for r in result["comparisons"]}
    for candidate, direction in (("arm-04/gmm_kernel", "all_negative"),
                                 ("arm-05/explicit_decomp", "all_positive")):
        assert rows[candidate]["direction_summary"] == direction
        low, high = rows[candidate]["original_simultaneous_interval_m"]
        assert low < 0 < high
    assert rows["arm-19/em"]["seed_delta_m"] == rows["arm-19/euler"]["seed_delta_m"]
    for candidate in ("arm-10/d2_mc", "arm-10/d2_closed"):
        assert rows[candidate]["sign_counts"]["exact_zero"] == 5
    assert rows["arm-21/crn"]["sign_counts"]["negative"] == 5
    assert not result["seed_range_is_confidence_interval"]
    assert not result["scientific_claim_authorized"]
    assert not result["independent_saved_output_audit_completed"]
    assert not result["forecast_arrays_opened"]
    assert all(result[k] == 0 for k in ("new_fits", "new_forecasts", "new_particle_scores", "new_resampling_draws"))


def test_display_does_not_round_small_nonzero_effects_to_zero():
    assert display(0) == "0"
    assert display(-.000051) == "-5.10e-5"
    assert display(.02542) == "0.02542"
    assert display(-4.999764832066935) == "-5.00"


@pytest.mark.parametrize("language", ["en", "zh"])
def test_generated_table_is_bilingual_complete_and_in_appendix(language):
    result = summarize(*inputs())
    tex = (PAPER/language/"main.tex").read_text(encoding="utf-8")
    table = table_tex(result, language)
    assert (PAPER/language/"method-seed-stability.tex").read_text(encoding="utf-8") == table
    assert table.count(" & Full") == 21
    assert table.count(r"\textit{") == 5
    assert r"\label{tab:method-seed-stability}" in table
    assert tex.index(r"\label{sec:method-seed-stability}") < tex.index(r"\appendix")
    assert tex.index(r"\label{sec:method-seed-table}") > tex.index(r"\appendix")
    assert tex.count(r"\input{method-seed-stability.tex}") == 1
    assert "20260814--20260818" in table
    assert "Full18" in table and "Full20" in table


def test_committed_projection_and_ledger_are_descriptive_only():
    expected = summarize(*inputs())
    projection = PAPER/"method-seed-stability-v1.json"
    assert json.loads(projection.read_text(encoding="utf-8")) == expected
    ledger = json.loads((PAPER/"claim-ledger.json").read_text(encoding="utf-8"))
    record = ledger["original_five_seed_description"]
    assert record["projection_sha256"] == hashlib.sha256(projection.read_bytes()).hexdigest()
    assert record["comparison_rows"] == 21 and record["review_items"] == ["P1-19"]
    assert not record["final_qualification_or_review_complete"]
    assert not ledger["final_empirical_results_integrated"] and not ledger["human_accepted"]
