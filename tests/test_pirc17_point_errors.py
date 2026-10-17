"""Synthetic whole-pair arithmetic and anonymous saved-description checks."""
from copy import deepcopy
import ast
import hashlib
import json
import math
from pathlib import Path
import re

import pytest

from scripts import describe_pirc17_point_errors as reader


def fixture():
    scope = {k: c*64 for k,c in zip(("protocol_sha256", "execution_sha256", "matrix_sha256"), "abc")}
    targets = [dict(sample_id=f"sample{r}", independent_block_id=f"block{r}", window_sha256="d"*64,
                    scoring_frame=[0.,0.], elapsed_seconds=[60.,300.,900.,1798.],
                    positions_m=[[3.,4.]]*4) for r in range(46)]
    selected = [dict(sample_id=t["sample_id"], independent_block_id=t["independent_block_id"], split="final_eval") for t in targets]
    population = dict(protocol_sha256=scope["protocol_sha256"], execution_sha256=scope["execution_sha256"],
                      selection=dict(selected=selected))
    scope["population_sha256"] = reader.digest(population)
    scoring = dict(schema_version="pirc17-formal-scoring-inputs-v1", **{k:scope[k] for k in
                   ("protocol_sha256", "execution_sha256", "population_sha256")},
                   partition="final_eval", truth_passed_to_predictors=False, targets=targets)
    scope["scoring_inputs_sha256"] = reader.digest(scoring)
    prefixes = [deepcopy({**{k:t[k] for k in ("sample_id","independent_block_id","window_sha256","scoring_frame")},
                 "score_seconds":t["elapsed_seconds"]}) for t in targets]
    context = dict(schema_version="pirc17-closed-input-context-v1", **{k:scope[k] for k in
                   ("protocol_sha256","execution_sha256","matrix_sha256")},
                   scoring_inputs=dict(payload=scoring,sha256=reader.digest(scoring)),
                   population=dict(payload=population,sha256=reader.digest(population)),
                   causal_prefixes=prefixes, truth_passed_to_predictors=False, raw_sources_independently_reloaded=False)
    record = dict(payload=context,sha256=reader.digest(context))
    blocks = []
    for rank,target in enumerate(targets):
        rows = []
        for config_index,config in enumerate((*reader.SUBJECTS,None)):
            baseline = config is None
            for seed in ([None] if baseline else reader.SEEDS):
                # Equal five-seed replication must not multiply a block/reference.
                errors = [float(rank+config_index+t+1) for t in range(4)]
                by_time = [dict(elapsed_seconds=time, energy_score_m=e if baseline else e/2,
                              region=dict(region="deterministic_point_mass" if baseline else "ensemble_mean_radial_quantile_disk",
                                          center_m=[3.+e,4.])) for time,e in zip(target["elapsed_seconds"],errors)]
                scores = dict(particle_count=1 if baseline else 512, time_weights=[.25]*4,
                              point_estimator="deterministic_inertial_path" if baseline else "ensemble_mean_not_best_of_N",
                              by_time=by_time, ade_grid_mean_m=sum(errors)/4,
                              time_weighted_displacement_error_m=sum(errors)/4, fde_m=errors[-1])
                rows.append(dict(matrix="inertial" if baseline else "NEX326-methods", configuration=config,
                                 origin_rank=rank, origin_mode="causal_prefix", partition="final_eval", scientific=not baseline,
                                 sample_id=target["sample_id"], independent_block_id=target["independent_block_id"],
                                 origin_id=reader.digest(["pirc17-formal-origin-stream-v1",target["sample_id"],"causal_prefix"]),
                                 context_sha256=reader.digest(["context",rank]), target_sha256=reader.digest(target),
                                 forecast_work_id=reader.digest([config,rank,seed]), seed=seed, status="success", scores=scores))
        blocks.append(dict(origin_mode="causal_prefix",origin_rank=rank,rows=rows))
    return blocks,targets,record,scope


def test_complete_same_target_grid_and_equal_block_means():
    blocks,targets,record,scope = fixture()
    assert reader.targets_from_context(record,scope,record["sha256"]) == targets
    result = reader.summarize(blocks,targets)
    assert [p["model"] for p in result["profiles"]] == list(reader.MODELS)
    assert [p["forecast_rows"] for p in result["profiles"]] == [230,230,230,46]
    assert result["profiles"][0]["point_error_by_time_m"] == [23.5,24.5,25.5,26.5]
    assert result["profiles"][0]["ade_m"] == 25.
    assert result["maximum_original_ade_fde_consistency_gap_m"] == 0
    assert result["saved_forecast_rows_used"] == 736 and result["distinct_target_positions"] == 184


def test_seed_error_is_averaged_after_distance_not_distance_of_pooled_center():
    blocks,targets,_,_ = fixture()
    row=blocks[0]["rows"][1]
    row["scores"]["by_time"][0]["region"]["center_m"]=[2.,4.]
    # First block now has four +1 centers and one -1 center; its mean
    # individual error remains1, whereas its pooled-center error is0.6.
    assert reader.summarize(blocks,targets)["profiles"][0]["point_error_by_time_m"][0] == 23.5


def test_euclidean_center_error_uses_both_scoring_axes():
    blocks,targets,_,_ = fixture()
    row=blocks[0]["rows"][0]
    row["scores"]["by_time"][0]["region"]["center_m"]=[6.,8.]
    row["scores"]["ade_grid_mean_m"]=3.5
    row["scores"]["time_weighted_displacement_error_m"]=3.5
    errors,gap=reader.errors_for_row(row,targets[0],False)
    assert errors==[5.,2.,3.,4.] and gap==0


@pytest.mark.parametrize("mutation", ["missing_block","duplicate_rank","missing_seed","duplicate_seed","missing_reference",
    "failed","wrong_target","wrong_sample","wrong_block","wrong_context","wrong_origin","duplicate_work","wrong_time",
    "nan_center","bool_center","center_shape","wrong_center_semantics","wrong_estimator","wrong_particles",
    "wrong_weights","wrong_ade","wrong_fde","wrong_weighted_error","negative_ade","wrong_reference_es","wrong_rank"])
def test_missing_or_mismatched_pairs_refuse_whole_projection(mutation):
    blocks,targets,_,_ = fixture()
    rows = blocks[0]["rows"]; row = rows[0]; score = row["scores"]
    if mutation == "missing_block": blocks.pop()
    elif mutation == "duplicate_rank": blocks[-1]["origin_rank"] = 0
    elif mutation == "missing_seed": rows.pop(0)
    elif mutation == "duplicate_seed": rows[1]["seed"] = row["seed"]
    elif mutation == "missing_reference": rows.pop()
    elif mutation == "failed": row["status"] = "failed"
    elif mutation == "wrong_target": row["target_sha256"] = "0"*64
    elif mutation == "wrong_sample": row["sample_id"] = "other"
    elif mutation == "wrong_block": row["independent_block_id"] = "other"
    elif mutation == "wrong_context": rows[1]["context_sha256"] = "0"*64
    elif mutation == "wrong_origin": row["origin_id"] = "0"*64
    elif mutation == "duplicate_work": rows[1]["forecast_work_id"] = row["forecast_work_id"]
    elif mutation == "wrong_time": score["by_time"][0]["elapsed_seconds"] += 1
    elif mutation == "nan_center": score["by_time"][0]["region"]["center_m"][0] = float("nan")
    elif mutation == "bool_center": score["by_time"][0]["region"]["center_m"][0] = True
    elif mutation == "center_shape": score["by_time"][0]["region"]["center_m"].pop()
    elif mutation == "wrong_center_semantics": score["by_time"][0]["region"]["region"] = "best_particle"
    elif mutation == "wrong_estimator": score["point_estimator"] = "best_particle"
    elif mutation == "wrong_particles": score["particle_count"] = 1024
    elif mutation == "wrong_weights": score["time_weights"] = [.1,.2,.3,.4]
    elif mutation == "wrong_ade": score["ade_grid_mean_m"] += .001
    elif mutation == "wrong_fde": score["fde_m"] += .001
    elif mutation == "wrong_weighted_error": score["time_weighted_displacement_error_m"] += .001
    elif mutation == "negative_ade": score["ade_grid_mean_m"] = -1
    elif mutation == "wrong_reference_es": rows[-1]["scores"]["by_time"][0]["energy_score_m"] += 1
    elif mutation == "wrong_rank": row["origin_rank"] = 1
    with pytest.raises(ValueError): reader.summarize(blocks,targets)


@pytest.mark.parametrize("mutation", ["scope","target_hash","missing_target","duplicate_member","frame","window","clock",
    "position_shape","nonfinite_target","bool_target","outside_tolerance","target_partition","truth","raw_reloaded"])
def test_closed_targets_require_original_scope_frame_window_clock_and_population(mutation):
    _,_,record,scope = fixture()
    payload=record["payload"]; scoring=payload["scoring_inputs"]["payload"]; target=scoring["targets"][0]
    if mutation == "scope": payload["execution_sha256"] = "0"*64
    elif mutation == "target_hash": payload["scoring_inputs"]["sha256"] = "0"*64
    elif mutation == "missing_target": scoring["targets"].pop()
    elif mutation == "duplicate_member": payload["population"]["payload"]["selection"]["selected"][-1] = deepcopy(payload["population"]["payload"]["selection"]["selected"][0])
    elif mutation == "frame": target["scoring_frame"][0] = 1
    elif mutation == "window": target["window_sha256"] = "0"*64
    elif mutation == "clock": target["elapsed_seconds"][0] += 1
    elif mutation == "position_shape": target["positions_m"][0].pop()
    elif mutation == "nonfinite_target": target["positions_m"][0][0] = float("inf")
    elif mutation == "bool_target": target["positions_m"][0][0] = True
    elif mutation == "outside_tolerance": target["elapsed_seconds"][0] = 91.; payload["causal_prefixes"][0]["score_seconds"] = target["elapsed_seconds"]
    elif mutation == "target_partition": scoring["partition"] = "train"
    elif mutation == "truth": payload["truth_passed_to_predictors"] = True
    elif mutation == "raw_reloaded": payload["raw_sources_independently_reloaded"] = True
    if mutation == "nonfinite_target":
        with pytest.raises(ValueError): reader.digest(payload)
        return
    # Rebinding synthetic envelopes must not conceal a semantic mismatch.
    if mutation != "target_hash":
        payload["scoring_inputs"]["sha256"] = reader.digest(scoring)
        scope["scoring_inputs_sha256"] = reader.digest(scoring)
    payload["population"]["sha256"] = reader.digest(payload["population"]["payload"])
    scope["population_sha256"] = payload["population"]["sha256"]
    scoring["population_sha256"] = scope["population_sha256"]
    if mutation != "target_hash":
        payload["scoring_inputs"]["sha256"] = reader.digest(scoring)
        scope["scoring_inputs_sha256"] = reader.digest(scoring)
    record["sha256"] = reader.digest(payload)
    with pytest.raises(ValueError): reader.targets_from_context(record,scope,record["sha256"])


def test_actual_anonymous_profile_reproduces_saved_ade_fde_and_target_clocks():
    paper=Path(__file__).resolve().parents[1]/"paper/pirc17"
    value=json.loads((paper/"point-error-horizon-description-v1.json").read_text(encoding="utf-8"))
    original=json.loads((paper/"preliminary-method-statistics-v1.json").read_text(encoding="utf-8"))
    indexed={r["configuration"]:r for r in original["configs"]}
    for profile in value["profiles"][:3]:
        row=indexed[profile["configuration"]]
        assert math.isclose(profile["ade_m"],row["ade_m"],rel_tol=1e-12,abs_tol=1e-9)
        assert math.isclose(profile["fde_m"],row["fde_m"],rel_tol=1e-12,abs_tol=1e-9)
    assert value["maximum_original_ade_fde_consistency_gap_m"] < 1e-12
    assert value["target_time_vectors_sha256"] == json.loads((paper/"target-time-description-v1.json").read_text(encoding="utf-8"))["target_time_vectors_sha256"]
    assert not value["scientific_claim_authorized"] and not value["independent_saved_output_audit_completed"]
    assert not value["private_coordinates_clocks_recording_ids_or_paths_exported"]
    assert not value["particle_arrays_opened"] and not value["raw_trajectories_opened"]
    assert all(value[k]==0 for k in ("new_fits","new_forecasts","new_particle_scores","new_bootstrap_or_tests","map_queries"))
    text=(paper/"point-error-horizon-description-v1.json").read_text()
    assert not any(k in text for k in ('"positions_m":','"sample_id":','"center_m":'))
    assert not re.search(r"[A-Za-z]:[/\\]",text)


def test_reader_imports_no_predictor_model_map_or_random_code():
    tree=ast.parse(Path(reader.__file__).read_text(encoding="utf-8"))
    modules=set()
    for node in ast.walk(tree):
        if isinstance(node,ast.Import): modules.update(a.name for a in node.names)
        elif isinstance(node,ast.ImportFrom): modules.add(node.module)
    assert modules == {"__future__","argparse","hashlib","json","math","pathlib","statistics","scripts.describe_pirc17_inertial"}
