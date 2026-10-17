"""Saved-metadata and analytic document checks; no trajectories or model calls."""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1] / 'paper/pirc17'
PATH = ROOT / 'history-missingness-description-v1.json'
D = json.loads(PATH.read_text(encoding='utf-8'))
L = json.loads((ROOT / 'claim-ledger.json').read_text(encoding='utf-8'))
F = json.loads((ROOT / 'fit-diagnostics-v1.json').read_text(encoding='utf-8'))
C = json.loads((ROOT / 'figures/case-horizons.json').read_text(encoding='utf-8'))


def test_saved_scope_and_cross_projection_diffusion_arithmetic():
    assert D['fit_projection_sha256'] == hashlib.sha256((ROOT / 'fit-diagnostics-v1.json').read_bytes()).hexdigest()
    assert D['new_forecasts_fits_map_queries_or_particle_scores'] == 0
    assert D['terrain_history_tick_seconds'] == 5
    assert D['stable_terrain_secant_span_seconds'] == 10
    assert not D['missing_input_robustness_established']
    assert not D['independent_saved_output_audit_completed']
    assert not D['full_forecast_per_column_mask_rates_available']
    assert not D['full_early_and_late_velocity_drift_distributions_available']
    assert len(D['source_sha256']) == 5
    fits = {r['configuration']: r for r in F['terrain']}
    scales = {r['configuration']: r for r in D['local_diffusion_noise_scales']}
    assert scales.keys() == fits.keys() and len(scales) == 10
    for name, row in scales.items():
        trace = sum(fits[name]['diffusion_eigenvalues_m2_per_s'])
        assert row['original_record_sha256'] == fits[name]['original_record_sha256']
        assert row['diffusion_trace_m2_per_s'] == trace
        assert math.isclose(row['local_secant_rms_10s_mps'], math.sqrt(trace / 10), abs_tol=1e-14)


def test_saved_query_counts_match_existing_cases_without_population_claim():
    rows = D['case_query_counts']
    assert {(r['case_rank'], r['configuration']) for r in rows} == {
        (rank, name) for rank in [0, 3, 4] for name in ['base', 'all-terrain']}
    expected = {0: 185856, 3: 186368, 4: 186368}
    for row in rows:
        assert row['invalid_encoded_rows'] == 0
        assert row['encoded_query_rows'] == expected[row['case_rank']]
        assert row['raw_map_query_rows'] == (0 if row['configuration'] == 'base' else row['encoded_query_rows'])
    for index, rank in enumerate([0, 3, 4]):
        for model in C['cases'][index]['models']:
            row = next(r for r in rows if r['case_rank'] == rank and r['configuration'] == model['subject'])
            assert row['raw_map_query_rows'] == model['raw_map_query_rows']
    assert not C['population_effects_established']


def test_reported_prefix_scope_is_not_training_span_evidence():
    stats = D['prefix_span_summary']
    expected = {'origin_span_seconds': (2, 7, 61),
                'last_gap_seconds': (1, 3, 31),
                'first_tick_span_seconds': (6, 8, 36)}
    for key, triple in expected.items():
        assert stats[key]['count'] == 46
        assert tuple(stats[key][name] for name in ['minimum', 'median', 'maximum']) == triple
    assert stats['original_spans_different_from_stable_10s'] == 46
    assert not D['training_prefix_span_distribution_retained_in_this_projection']
    assert not L['history_and_missing_input_description']['training_prefix_span_distribution_reconstructed']


def test_closed_form_overlap_from_increment_covariance_no_simulation():
    # Two 10-second windows share 5 seconds of Brownian increments.
    q = np.array([[2., .4], [.4, 1.]])
    independent_increment_cov = np.kron(np.eye(3), 5 * q)
    weights = np.array([[1., 1., 0.], [0., 1., 1.]]) / 10
    transform = np.kron(weights, np.eye(2))
    joint = transform @ independent_increment_cov @ transform.T
    assert np.allclose(joint[:2, :2], q / 10)
    assert np.allclose(joint[:2, 2:], q / 20)
    assert D['stable_secant_adjacent_correlation_in_constant_drift_model'] == .5
    assert D['local_frozen_drift_calculation_not_actual_feedback_variance']


def test_fixed_history_zero_imputation_algebra_not_measured_experiment():
    values = np.array([2., -3., 4.])
    weights = np.array([[1., 2.], [3., -1.], [.5, .2]])
    mask_weights = np.array([[.1, .4], [.3, .6], [.7, .8]])
    intercept = np.array([.4, -.2])
    valid = values @ weights + np.ones(3) @ mask_weights + intercept
    kept = np.array([0., 1., 0.])
    invalid = (values * kept) @ weights + kept @ mask_weights + intercept
    dropped = [0, 2]
    delta = -(values[dropped, None] * weights[dropped] + mask_weights[dropped]).sum(axis=0)
    assert np.allclose(invalid - valid, delta)
    assert L['history_and_missing_input_description']['missing_drift_formula_not_measured_counterfactual']


@pytest.mark.parametrize('language', ['en', 'zh'])
def test_bilingual_sections_numbers_and_local_scope(language):
    tex = (ROOT / language / 'main.tex').read_text(encoding='utf-8')
    for label in ['sec:history-feedback', 'tab:history-spans', 'eq:secant-local-noise',
                  'eq:secant-overlap', 'sec:missing-input-scope', 'eq:missing-drift-change']:
        assert tex.count(r'\label{' + label + '}') == 1
    for number in ['2.7387', '2.5077', '0.5233', '0.5008', '185856', '186368']:
        assert number in tex
    for formula in [r'\frac{Q}{T}', r'\frac{(T-s)_+}{T^2}Q',
                    r'-\sum_{j\in J}', r'Q/T+2R_{\rm obs}/T^2']:
        assert formula in tex
    history = tex.split(r'\label{sec:history-feedback}', 1)[1].split(r'\subsection{', 1)[0]
    missing = tex.split(r'\label{sec:missing-input-scope}', 1)[1].split(r'\subsection{', 1)[0]
    assert ('not measured rollout velocity dispersions' if language == 'en' else '不是测得的 rollout 速度离散程度') in history
    assert ('not a fitted sensor model' if language == 'en' else '不是拟合的传感器模型') in history
    assert ('unsupported extrapolation' if language == 'en' else '未经支持的外推') in missing
    assert ('not independent points' if language == 'en' else '不是独立位置') in missing


def test_ledger_binding_and_unclosed_evidence():
    r = L['history_and_missing_input_description']
    assert r['projection_sha256'] == hashlib.sha256(PATH.read_bytes()).hexdigest()
    assert r['review_items'] == ['P1-04', 'P1-05']
    assert r['original_final_prefixes_described'] == 46
    assert r['original_case_forecast_receipts_described'] == 6
    assert r['previously_projected_diffusion_fits_used'] == 10
    assert r['original_source_hashes_matched_to_execution'] == 5
    assert r['new_forecasts_fits_queries_or_particle_scores'] == 0
    assert not r['full_per_column_forecast_rates_and_velocity_traces_integrated']
    assert not r['all_review_items_or_paper_complete']
    assert not L['final_empirical_results_integrated']
    assert not L['human_accepted']
