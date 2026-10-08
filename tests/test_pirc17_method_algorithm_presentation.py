"""Saved metadata and manuscript checks only; never fit or execute a rollout."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

import pytest
from scripts.pirc17_document_blocks import assert_preserved_blocks


ROOT = Path(__file__).resolve().parents[1] / "paper" / "pirc17"
PATH = ROOT / "method-algorithm-description-v1.json"
EVIDENCE = json.loads(PATH.read_text(encoding="utf-8"))


def test_original_population_and_ledger_bindings():
    ledger = json.loads((ROOT / "claim-ledger.json").read_text(encoding="utf-8"))
    bound = ledger["saved_method_algorithm_description"]
    assert hashlib.sha256(PATH.read_bytes()).hexdigest() == bound["projection_sha256"]
    assert EVIDENCE["inventory_sha256"] == bound["inventory_sha256"]
    assert len(EVIDENCE["methods"]) == 16
    assert sum(len(row["prediction_slots"]) for row in EVIDENCE["methods"]) == 28
    assert len(EVIDENCE["source_sha256"]) == 4
    assert not EVIDENCE["scope"]["independent_saved_forecast_audit"]
    assert not EVIDENCE["scope"]["numerical_or_meta_learning_qualification_added"]
    assert not EVIDENCE["scope"]["pre_meta_and_pre_target_parameters_saved"]
    for name in ("new_fits", "new_forecasts", "new_particle_scores"):
        assert EVIDENCE["scope"][name] == 0


def test_actual_saved_reptile_and_default_hyperparameters():
    meta = next(row for row in EVIDENCE["methods"] if row["representative_slot"] == "arm-14/reptile")
    constants = EVIDENCE["constants"]
    assert constants["RIDGE"] == 1e-6
    assert constants["REPTILE_INITIAL_STEP"] == .35
    assert constants["REPTILE_INNER_RATE"] == meta["meta_inner_rate"] == .5
    assert constants["REPTILE_INNER_STEPS"] == meta["meta_inner_steps"] == 5
    assert constants["REPTILE_META_EPOCHS"] == meta["meta_outer_epochs"] == 4
    assert constants["target_adaptation_weight"] == .65
    assert meta["meta_task_count"] == 30
    assert meta["covariance_scale"] == 1
    assert meta["estimator_drift_fraction"] == 0
    assert not any(EVIDENCE["saved_reptile_and_full_parameter_arrays_exactly_equal"].values())


@pytest.mark.parametrize("language", ["en", "zh"])
def test_bilingual_formula_and_evidence_links(language):
    tex = (ROOT / language / "main.tex").read_text(encoding="utf-8")
    labels = json.loads((ROOT / "claim-ledger.json").read_text(encoding="utf-8"))["saved_method_algorithm_description"]["equation_labels"]
    for label in labels:
        assert tex.count("\\label{" + label + "}") == 1
    assert "method-algorithm-description-v1.json" in tex
    assert "1.595" in tex and "1.260" in tex
    assert r"\frac{0.5}{L_{rm}}" in tex
    assert r"\frac{0.35}{\sqrt{e+1}}" in tex
    assert r"(H^2,(I+H)J_{1/2},H(\Delta Q_m)H^\top)" in tex
    assert r"C_sP_{s,t}^{\top}" in tex


@pytest.mark.parametrize("language", ["en", "zh"])
def test_base_regression_covariance_and_gmm_rules_are_explicit(language):
    tex=(ROOT/language/"main.tex").read_text(encoding="utf-8")
    for label in ("sec:method-base-fit", "sec:residual-mixture-fit",
                  "eq:method-base-ridge", "eq:method-base-covariance",
                  "eq:gmm-residual-partition"):
        assert tex.count(r"\label{"+label+"}")==1
    for formula in (r"\tfrac12\|D_m\Theta-Y_m\|_F^2+\tfrac\rho2\|\Theta\|_F^2",
                    r"(D_m^\top D_m+\rho I_d)^{-1}D_m^\top Y_m",
                    r"\frac1{n_m-1}", r"(e_{mi}-\bar e_m)(e_{mi}-\bar e_m)^\top",
                    r"\widehat\pi_m=n_m/\sum_k n_k", r"\rho/n_m",
                    r"(r_{i,e},r_{i,n},-r_{i,e}-r_{i,n})_j",
                    r"\ell_i=m_{s(i)}+1"):
        assert formula in tex
    phrases = ("including the intercept", "first maximum", "exactly zero",
               "at least two transitions", "without iterative",
               "not its residual-group labels", "not a regression degrees-of-freedom",
               "The pooled coefficients are only used to form labels") if language=="en" else (
               "包括截距", "首个最大项", "零残差", "至少需要两个转移",
               "没有迭代似然优化", "而非残差组标签", "不是回归自由度修正",
               "pooled系数仅用于产生标签")
    normalized=re.sub(r"\s+", " ", tex)
    for phrase in phrases:
        assert phrase in normalized
    assert tex.index(r"\label{eq:gmm-residual-partition}") < tex.index(r"\label{sec:estimator-calibration}")
    assert ("not a matched-component mixture-likelihood calibration" if language=="en" else
            "不是匹配分量的混合似然校准") in normalized


@pytest.mark.parametrize("language", ["en", "zh"])
def test_base_fit_addition_preserves_all_previous_scientific_blocks(language):
    repository=ROOT.parents[1]
    before=subprocess.check_output(["git", "show",
        f"0095cff5dcc58f9c72b3b1443c8854ce0c750ef7:paper/pirc17/{language}/main.tex"],
        cwd=repository).decode("utf-8").replace("\r\n", "\n")
    after=(ROOT/language/"main.tex").read_text(encoding="utf-8")
    for kind in ("table", "longtable", "figure", "equation"):
        pattern=r"\\begin\{"+kind+r"\}.*?\\end\{"+kind+r"\}"
        assert_preserved_blocks(re.findall(pattern,before,re.S),re.findall(pattern,after,re.S),kind)
    current=re.findall(r"\\begin\{align\}.*?\\end\{align\}",after,re.S)
    previous=re.findall(r"\\begin\{align\}.*?\\end\{align\}",before,re.S)
    new_labels=("eq:method-base-ridge", "eq:method-base-covariance", "eq:gmm-residual-partition")
    added=[block for block in current if any(r"\label{"+label+"}" in block for label in new_labels)]
    retained=[block for block in current if block not in added]
    assert retained == previous and len(added) == 2
    assert [label for block in added for label in re.findall(r"\\label\{([^}]+)\}",block)] == [
        "eq:method-base-ridge", "eq:method-base-covariance", "eq:gmm-residual-partition"]
    # The new specification must not undo the earlier Reptile reading revision.
    start = r"\paragraph{Fitting and adaptation scope.}" if language=="en" else r"\paragraph{拟合与适应范围。}"
    end = r"\paragraph{What the finite objective comparison actually changes.}" if language=="en" else r"\paragraph{有限拟合目标比较实际改变了什么。}"
    assert after[after.index(start):after.index(end)] == before[before.index(start):before.index(end)]


def test_new_specification_does_not_claim_missing_fit_diagnostics_or_acceptance():
    ledger=json.loads((ROOT/"claim-ledger.json").read_text(encoding="utf-8"))
    entry=ledger["method_base_fit_specification_revision"]
    assert entry["source_base_commit"]=="0095cff5dcc58f9c72b3b1443c8854ce0c750ef7"
    assert entry["frozen_model_source_sha256"]==EVIDENCE["source_sha256"]["experiments/nex326/model.py"]
    assert entry["base_ridge_is_mean_normalized"] is False
    assert entry["base_ridge_penalizes_intercept"] is True
    assert entry["base_covariance_is_centered"] is True
    assert entry["base_covariance_denominator"]=="n_m-1"
    assert entry["gmm_likelihood_em_executed"] is False
    assert entry["gmm_validation_uses_heading_labels"] is True
    assert entry["gmm_group_counts_reconstructed"] is False
    assert entry["new_fits_forecasts_scores_resampling_or_map_queries"]==0
    assert entry["independent_saved_output_audit_completed"] is False
    assert entry["final_paper_or_review_complete"] is False
    assert ledger["final_empirical_results_integrated"] is False
    assert ledger["human_accepted"] is False
