# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Whole anonymous descriptive-table transport, not scientific acceptance."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from scripts import render_pirc17_point_error_tables as renderer

PAPER=Path(__file__).resolve().parents[1]/"paper/pirc17"


def projection():
    return renderer.read_bound(PAPER/"point-error-horizon-description-v1.json",renderer.SHA)


@pytest.mark.parametrize("language",["en","zh"])
def test_exact_complete_bilingual_inputs_values_definition_and_limits(language):
    text=renderer.tex(projection(),language)
    assert (PAPER/language/"point-error-horizons.tex").read_text(encoding="utf-8")==text
    assert text.count(r"\begin{table}")==1 and text.count(r"\begin{equation}")==1
    for v in ("73.77","332.31","812.26","1326.09","71.92","1299.11","75.88","1335.73","31.17","2095.78"):
        assert v in text
    main=(PAPER/language/"historical-main-v1.tex").read_text(encoding="utf-8")
    assert main.count(r"\input{point-error-horizons.tex}")==1
    assert main.index(r"\input{inertial-primary-comparison.tex}") < main.index(r"\input{point-error-horizons.tex}") < main.index(r"\label{sec:terrain-results}")
    assert "10^{-12}" in text and "dt300" in text


@pytest.mark.parametrize("field",["recording_hash_blocks","probabilistic_forecasts","deterministic_reference_paths",
    "saved_forecast_rows_used","distinct_target_positions","nominal_target_tolerance_seconds"])
def test_changed_denominator_is_refused(field):
    value=deepcopy(projection()); value[field]-=1
    with pytest.raises(ValueError): renderer.tex(value,"en")


@pytest.mark.parametrize("field",["new_fits","new_forecasts","new_particle_scores","new_bootstrap_or_tests",
    "particle_arrays_opened","raw_trajectories_opened","map_queries","original_saved_scores_changed",
    "independent_saved_output_audit_completed","scientific_claim_authorized","participant_independence_established",
    "physical_clock_or_utc_certified","original_final_figure_inventory_replaced","private_coordinates_clocks_recording_ids_or_paths_exported"])
def test_no_new_empirical_work_or_evidence_promotion(field):
    value=deepcopy(projection()); value[field]=True
    with pytest.raises(ValueError): renderer.tex(value,"zh")


@pytest.mark.parametrize("mutation",["missing_model","swapped_models","missing_time","nan","bool","negative","changed_ade","changed_fde","gap","times"])
def test_invalid_or_unmatched_statistics_fail_whole_table(mutation):
    value=deepcopy(projection())
    if mutation=="missing_model": value["profiles"].pop()
    elif mutation=="swapped_models": value["profiles"].reverse()
    elif mutation=="missing_time": value["profiles"][0]["point_error_by_time_m"].pop()
    elif mutation=="nan": value["profiles"][0]["point_error_by_time_m"][0]=float("nan")
    elif mutation=="bool": value["profiles"][0]["point_error_by_time_m"][0]=True
    elif mutation=="negative": value["profiles"][0]["point_error_by_time_m"][0]=-1
    elif mutation=="changed_ade": value["profiles"][0]["ade_m"]+=1
    elif mutation=="changed_fde": value["profiles"][0]["fde_m"]+=1
    elif mutation=="gap": value["maximum_original_ade_fde_consistency_gap_m"]=.01
    elif mutation=="times": value["actual_target_bounds_seconds"][0][0]+=1
    with pytest.raises(ValueError): renderer.tex(value,"en")


def test_new_ledger_pins_exact_files_and_retains_every_previous_root_and_review_boundary():
    root=PAPER.parents[1]
    new=json.loads((PAPER/"claim-ledger.json").read_text(encoding="utf-8"))
    # Pin every historical root without requiring private Git history in CI.
    old={k:v for k,v in new.items() if k!="point_error_horizon_manuscript_revision"}
    canonical=json.dumps(old,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")
    assert hashlib.sha256(canonical).hexdigest()=="1a239b88b68ff6c756bf2761860bc45dcdc679840eb69ceeb6b754a1f61e7c55"
    entry=new["point_error_horizon_manuscript_revision"]
    for field in ("projection","reader","renderer","shared_closed_score_reader"):
        assert hashlib.sha256((root/entry[field]).read_bytes()).hexdigest()==entry[field+"_sha256"]
    for language in ("en","zh"):
        assert hashlib.sha256((PAPER/language/"point-error-horizons.tex").read_bytes()).hexdigest()==entry["bilingual_tex_sha256"][language]
    review=json.loads((PAPER/"review-response-v1.json").read_text(encoding="utf-8"))
    assert review["accepted_items"]==0 and not review["all_review_items_or_paper_complete"]
    assert review["status_counts"]=={"draft_checked":20,"partial":14,"awaiting_original_results":7,"permission_unverified":1}
    # Original81 paths remain; both individually bound timing disclosures are additive.
    original=[row for row in review["evidence_files"]
              if row["path"] not in {"paper/pirc17/runtime-interruption-disclosure-v1.json",
                                     "paper/pirc17/runtime-interruption-census-v1.json"}]
    assert len(original)==81
    assert len(review["evidence_files"])==83
    added=[row for row in review["evidence_files"] if row not in original]
    assert added==[{
        "path":"paper/pirc17/runtime-interruption-census-v1.json",
        "sha256":"ba0725440ee723507c65ae9b56441d694bb4bf73b5ece3537ba5f01d43b2edf7",
    },{
        "path":"paper/pirc17/runtime-interruption-disclosure-v1.json",
        "sha256":"27cf48830386bf67b6fcf9e78e72b8ab53b8b7533562e6e33d8d497868de721d",
    }]
    assert "paper/pirc17/terrain-family-completeness-v1.json" in {f["path"] for f in review["evidence_files"]}
