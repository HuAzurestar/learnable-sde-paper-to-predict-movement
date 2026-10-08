"""Saved metadata and static arithmetic only; no fitting, score replay or rollout."""
import hashlib
import json
import math
from pathlib import Path
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1] / 'paper/pirc17'
PATH = ROOT / 'estimator-calibration-description-v1.json'
D = json.loads(PATH.read_text(encoding='utf-8'))
F = json.loads((ROOT / 'fit-diagnostics-v1.json').read_text(encoding='utf-8'))
S = json.loads((ROOT / 'preliminary-method-statistics-v1.json').read_text(encoding='utf-8'))
L = json.loads((ROOT / 'claim-ledger.json').read_text(encoding='utf-8'))


def test_four_original_saved_fit_joins_no_new_science():
    assert D['inventory_sha256'] == F['inventory_sha256']
    for name, key in [('fit-diagnostics-v1.json', 'fit_projection_sha256'),
                      ('preliminary-method-statistics-v1.json', 'stage_projection_sha256')]:
        assert D[key] == hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    assert len(D['source_sha256']) == 8
    assert len(D['models']) == 4
    assert D['new_fits_forecasts_validation_scores_or_map_queries'] == 0
    assert not D['independent_saved_output_audit_completed']
    assert not D['all_review_items_or_paper_complete']
    assert not D['grid_scores_or_validation_fit_weights_retained_in_this_projection']
    for row in D['models']:
        old = next(x for x in F['methods'] if x['representative_slot'] == row['representative_slot'])
        assert row['original_record_file_sha256'] == old['original_record_sha256']
        assert row['transitions'] == old['transitions'] == {'train': 26009, 'adapt': 5762, 'validation': 6149}
        assert row['windows'] == old['windows'] == {'train': 328, 'adapt': 76, 'validation': 81}
        assert row['covariance_scale'] == old['selected_covariance_scale'] == 1.
        assert row['estimator_drift_fraction'] == old['selected_estimator_drift_fraction']


def test_grid_choices_and_selected_in_sample_objectives():
    assert D['constants']['ESTIMATOR_SCALE_CANDIDATES'] == [.55, .75, 1., 1.3, 1.7]
    assert D['constants']['ESTIMATOR_DRIFT_FRACTIONS'] == [0., .1, .25, .5]
    assert D['constants']['COVARIANCE_JITTER'] == 1e-8
    assert D['gauss_hermite_nodes_per_axis'] == 10
    rows = {r['estimator_method']: r for r in D['models']}
    assert rows['crps_energy']['estimator_candidate_count'] == 5
    assert rows['qmle']['estimator_candidate_count'] == 0
    for name in ['mixed', 'pure_es']:
        assert rows[name]['estimator_candidate_count'] == 20
        assert rows[name]['estimator_drift_fraction'] == .5
        assert rows[name]['validation_objective_after'] < rows[name]['validation_objective_before']
    assert rows['mixed']['objective_lambda'] == .5
    assert rows['pure_es']['objective_lambda'] == 'infinity'
    assert rows['mixed']['validation_objective_before'] == 1.
    assert rows['crps_energy']['validation_objective_before'] == rows['pure_es']['validation_objective_before']
    assert rows['qmle']['validation_objective_before'] == rows['qmle']['validation_objective_after']
    assert D['reported_validation_objectives_are_selected_in_sample']


def test_parameter_equality_not_score_equality_or_loss_advantage():
    eq = D['saved_parameter_equalities']
    keys = ['saved_weights_exactly_equal', 'saved_covariances_exactly_equal', 'saved_mode_probabilities_exactly_equal']
    assert len(eq) == 3 and all(eq[i][key] for i in [0, 1] for key in keys)
    assert not eq[2]['saved_weights_exactly_equal']
    assert eq[2]['saved_covariances_exactly_equal'] and eq[2]['saved_mode_probabilities_exactly_equal']
    assert D['parameter_equality_not_independent_final_output_audit']
    for row in D['stage_comparisons']:
        old = next(x for x in S['comparisons'] if x['candidate'] == row['candidate'])
        assert row == {key: old[key] for key in row}
        assert row['control'] == 'arm-07/full'
        assert row['simultaneous_interval_m'][0] < 0 < row['simultaneous_interval_m'][1]
    assert D['stage_comparisons'][1]['delta_estimate_m'] != D['stage_comparisons'][2]['delta_estimate_m']


def test_static_gaussian_rate_and_mixed_normalization_arithmetic():
    residuals, covariance = np.array([[1., 2.], [-1., 0.]]), np.diag([2., 4.])
    quadratic = np.mean(np.einsum('ni,ij,nj->n', residuals, np.linalg.pinv(covariance), residuals))
    nll = .5 * (2 * math.log(2 * math.pi) + np.linalg.slogdet(covariance)[1] + quadratic)
    assert math.isclose(quadratic, 1.)
    assert math.isclose(nll, math.log(2 * math.pi) + .5 * math.log(8) + .5)
    e0, n0 = .7, 2.4
    assert .5 * e0/max(e0, 1e-12) + .5 * n0/max(n0, 1e-12) == 1.
    assert np.array_equal(.5 * residuals + .5 * (2*residuals), 1.5 * residuals)
    # Hermite weights represent covariance I/2; both Gaussian factors match.
    c, node_cov = np.diag(np.sqrt([2., 4.])), .5 * np.eye(2)
    assert np.allclose(2*c @ node_cov @ c.T, covariance)
    assert np.allclose(4*c @ node_cov @ c.T, 2*covariance)


@pytest.mark.parametrize('language', ['en', 'zh'])
def test_bilingual_actual_objectives_and_interpretation(language):
    tex = (ROOT / language / 'main.tex').read_text(encoding='utf-8')
    for label in ['sec:estimator-calibration', 'eq:estimator-drift-grid',
                  'eq:estimator-validation-surrogates', 'eq:estimator-objectives',
                  'tab:estimator-calibration']:
        assert tex.count(r'\label{' + label + '}') == 1
    for token in [r'R_m(s)=s^2R_m^0', r'\pi_m=\pi_m^0', r'\log\det S_s',
                  r'\max(E_0,10^{-12})', r'\max(N_0,10^{-12})',
                  'estimator-calibration-description-v1.json', 'score-only',
                  '0.7317', '0.7214', '0.9885', '2.4534']:
        assert token in tex
    if language == 'en':
        assert 'not a mixture' in tex and 'selected in-sample values' in tex
        normalized = ' '.join(tex.split())
        assert 'Equal seed' in normalized and 'not make those streams identical' in normalized
    else:
        assert '不是混合似然' in tex and '选择后的样本内数值' in tex
        assert '种子数值相同不使这些流相同' in tex


def test_ledger_does_not_close_remaining_empirical_work():
    entry = L['saved_estimator_calibration_description']
    assert entry['projection_sha256'] == hashlib.sha256(PATH.read_bytes()).hexdigest()
    assert entry['original_saved_fits_described'] == 4
    assert entry['original_source_hashes_verified'] == 8
    assert entry['new_fits_forecasts_validation_scores_or_map_queries'] == 0
    assert not entry['candidate_grid_or_validation_fit_parameters_recomputed']
    assert not entry['independent_saved_output_audit_completed']
    assert not entry['all_review_items_or_paper_complete']
