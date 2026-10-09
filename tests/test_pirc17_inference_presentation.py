# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Existing-record, arithmetic and document checks; no draws or forecasts."""
import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist

import pytest

ROOT = Path(__file__).resolve().parents[1] / 'paper/pirc17'
PATH = ROOT / 'inference-description-v1.json'
EVIDENCE = json.loads(PATH.read_text(encoding='utf-8'))


def test_existing_projection_binding_and_no_new_science():
    ledger = json.loads((ROOT/'claim-ledger.json').read_text(encoding='utf-8'))
    revision = ledger['inference_and_decision_description']
    assert hashlib.sha256(PATH.read_bytes()).hexdigest() == revision['projection_sha256']
    assert revision['review_items'] == ['P1-14','P1-15','P1-16']
    assert len(EVIDENCE['planning']) == revision['planning_comparisons'] == 30
    assert len(EVIDENCE['primary_method_diagnostics']) == 21
    assert len(EVIDENCE['source_sha256']) == 6
    assert EVIDENCE['planning_design']['development_blocks'] == 3
    assert not EVIDENCE['planning_design']['sd_scenarios_are_confidence_bounds']
    assert not EVIDENCE['planning_design']['operational_utility_validated']
    for key in ('new_fits','new_forecasts','new_particle_scores','new_bootstrap_draws'):
        assert EVIDENCE['scope'][key] == 0
    assert not EVIDENCE['scope']['forecast_arrays_opened']
    assert not EVIDENCE['scope']['scientific_claim_authorized']
    assert not revision['all_review_items_or_paper_complete']
    assert not ledger['final_empirical_results_integrated']
    assert not ledger['human_accepted']


def test_frozen_normal_planning_values_without_observed_power():
    rows = EVIDENCE['planning']
    normal = NormalDist()
    config = EVIDENCE['inference_config']
    delta = config['delta_m']
    assert delta == 41.100259
    assert EVIDENCE['planning_design']['assumed_improvement_m'] == 2*delta
    for row in rows:
        sd = row['development_paired_sd_m']
        family_size = sum(r['family_id'] == row['family_id'] for r in rows)
        if sd is None:
            assert not row['planning_at46'] and not row['planning_qualified']
            assert row['planning_reason'] == 'no_comparison_specific_development_SD'
            continue
        z = normal.inv_cdf(1-config['alpha']/(2*family_size))
        for scenario in row['planning_at46']:
            sigma = sd*scenario['sd_multiplier']
            if sigma == 0:
                assert not row['planning_qualified']
                assert row['planning_reason'] == 'zero_development_SD_is_not_power_evidence'
                continue
            power = normal.cdf(delta*math.sqrt(46)/sigma-z)
            required = math.ceil(((z+normal.inv_cdf(.8))*sigma/delta)**2)
            assert scenario['approximate_power'] == pytest.approx(power,abs=1e-14)
            assert scenario['required_blocks_normal_approximation'] == required
    gates = {r['comparison']: r for r in rows}
    assert not gates['arm-06/dt600']['planning_qualified']
    assert gates['arm-06/dt600']['planning_at46'][0]['required_blocks_normal_approximation'] == 47
    assert not gates['arm-10/d2_mc']['planning_qualified']
    assert not gates['arm-10/d2_closed']['planning_qualified']
    assert sum(r['development_paired_sd_m'] is None for r in rows) == 4


def test_all_stage_comparisons_reconcile_and_missing_streams_not_fabricated():
    stage = json.loads((ROOT/'preliminary-method-statistics-v1.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((ROOT/'preliminary-method-statistics-v1.json').read_bytes()).hexdigest() == EVIDENCE['stage_file_sha256']
    rows = {(r['family_id'],r['candidate']): r for r in EVIDENCE['primary_method_diagnostics']}
    assert len(rows) == len(stage['comparisons']) == 21
    for previous in stage['comparisons']:
        actual = rows[previous['family_id'],previous['candidate']]
        for key,value in previous.items():
            assert actual[key] == value
        assert actual['second_stream_interval_m'] is None
        assert actual['interval_finite']
        assert actual['tail_check_max_shift_m'] <= EVIDENCE['inference_config']['delta_m']/4
        assert actual['tail_check_passed']
        raw_count = actual['p_zero_two_sided']*2001
        assert raw_count == pytest.approx(round(raw_count),abs=1e-10)
    assert not EVIDENCE['second_stream_intervals_retained']
    assert not EVIDENCE['bootstrap_draws_or_pivots_retained']


@pytest.mark.parametrize('language', ['en','zh'])
def test_bilingual_planning_diagnostics_and_decision_conditions(language):
    tex = (ROOT/language/"historical-main-v1.tex").read_text(encoding='utf-8')
    for label in ('sec:planning-qualification','eq:planning-power','tab:planning-sensitivity',
                  'sec:bootstrap-resolution','tab:bootstrap-diagnostics','sec:decision-conditions',
                  'eq:decision-roundoff','tab:comparison-conditions','tab:loo-lio-states'):
        assert tex.count('\\label{'+label+'}') == 1
    assert 'inference-description-v1.json' in tex
    diagnostic = tex.split(r'\label{tab:bootstrap-diagnostics}',1)[1].split(r'\end{longtable}',1)[0]
    for row in EVIDENCE['primary_method_diagnostics']:
        assert row['candidate'].replace('_',r'\_') in diagnostic
        assert f"{row['p_zero_two_sided']:.5f}" in diagnostic
        assert f"{row['holm_adjusted_p_zero']:.5f}" in diagnostic
    assert all(number in tex for number in ('20260926','20260927','10.27506475','1/2001'))
    assert r'\texttt{inverted\_cdf}' in tex
    assert r'\#\{s:e_s<-g\}\geq4' in tex
    assert r'\#\{s:|e_s|<\delta-g\}\geq4' in tex
    assert 'B & retain & inconclusive & retain & retain' in tex
    assert 'H & inconclusive & harmful & harmful & harmful' in tex
    assert 'E & redundant & redundant & redundant & redundant' in tex
    assert ('not a validated search-success or rescue-utility' if language == 'en' else '不是已验证的搜救成功率或救援效用') in tex
    assert ('not} second-stream endpoints' if language == 'en' else '没有}保存第二流区间端点') in tex

