"""Pure saved-scalar projection tests; fixtures are not empirical results."""
from copy import deepcopy
import json
import math

import pytest

from scripts import project_pirc17_secondary_scores as p


def row(origin='o', seed=1, block='b', value=10, status='success'):
    return dict(origin_id=origin, seed=seed, independent_block_id=block, status=status,
        scores=None if status == 'failed' else dict(particle_count=512, fde_m=value * 2,
        particle_endpoint_error_quantiles_m={'0.5': value + 1, '0.9': value + 10, '0.95': value + 20},
        by_time=[dict(elapsed_seconds=t, marginal_crps_m=[value, value + 2]) for t in p.TIMES]))


def test_mean_of_within_ensemble_quantiles_keeps_equal_block_origin_seed_weights():
    population = {'a': ['a1', 'a2'], 'b': ['b1']}
    rows = [row(o, s, b, v + s) for b, o, v in [('a', 'a1', 0), ('a', 'a2', 100), ('b', 'b1', 200)]
            for s in (0, 2)]
    result = p.summarize_group(rows, population, (0, 2))
    means = result['means']
    assert means['by_time'][0]['crps_east_m'] == 126
    assert means['mean_within_forecast_endpoint_quantiles_m']['0.5'] == 127
    assert means['fde_m'] == 252
    assert means['by_time'][0]['crps_east_m'] != sum(r['scores']['by_time'][0]['marginal_crps_m'][0] for r in rows) / 6


@pytest.mark.parametrize('rows', [[row()], [row(), row(seed=2, status='failed')]])
def test_missing_or_failed_seed_makes_entire_configuration_unavailable(rows):
    result = p.summarize_group(rows, {'b': ['o']}, (1, 2))
    assert result['status'] == 'unavailable' and result['means'] is None
    assert result['expected_forecasts'] == 2
    assert result['available_score_rows'] + result['missing_score_rows'] == 2
    assert sum(result['counts_by_status'].values()) == len(rows)


def test_one_deterministic_path_has_no_five_seed_duplication():
    result = p.summarize_group([row(seed=None)], {'b': ['o']}, (None,))
    assert result['status'] == 'computed'
    assert result['expected_forecasts'] == result['seeds_per_origin'] == 1


@pytest.mark.parametrize('bad', [row(seed=99), row(block='wrong'), row(origin='wrong')])
def test_wrong_seed_origin_or_block_is_not_a_new_sample(bad):
    with pytest.raises(ValueError):
        p.summarize_group([bad], {'b': ['o']}, (1,))


def test_duplicate_rows_cannot_inflate_sample_size():
    with pytest.raises(ValueError, match='duplicate'):
        p.summarize_group([row(), row()], {'b': ['o']}, (1,))


@pytest.mark.parametrize('value', [math.nan, math.inf, -1, True, None])
def test_successful_rows_require_finite_nonnegative_crps_even_when_other_rows_fail(value):
    good = row()
    good['scores']['by_time'][0]['marginal_crps_m'][1] = value
    with pytest.raises(ValueError):
        p.summarize_group([good, row(seed=2, status='failed')], {'b': ['o']}, (1, 2))


@pytest.mark.parametrize('change', ['missing-coordinate', 'missing-quantile', 'reversed-quantile',
                                  'missing-time', 'reversed-time', 'bad-count', 'failed-substitute'])
def test_no_imputed_coordinates_quantiles_time_slots_or_failed_scores(change):
    value = row()
    scores = value['scores']
    if change == 'missing-coordinate':
        scores['by_time'][0]['marginal_crps_m'].pop()
    elif change == 'missing-quantile':
        scores['particle_endpoint_error_quantiles_m'].pop('0.95')
    elif change == 'reversed-quantile':
        scores['particle_endpoint_error_quantiles_m']['0.5'] = 1000
    elif change == 'missing-time':
        scores['by_time'].pop()
    elif change == 'reversed-time':
        scores['by_time'][1]['elapsed_seconds'] = 1
    elif change == 'bad-count':
        scores['particle_count'] = True
    else:
        value['status'] = 'failed'
    with pytest.raises(ValueError):
        p.summarize_group([value], {'b': ['o']}, (1,))


@pytest.fixture
def full_fixture():
    # Every number below is a software fixture, never the committed empirical projection.
    populations = {m: {f'b{i}': [f'{m}:o{i}'] for i in range(n)}
                   for m, n in zip(p.MODES, (46, 6, 6))}
    rows, originals = [], []
    for mode in p.MODES:
        for matrix, config in p.AXES:
            seeds = (None,) if matrix == 'inertial' else p.SEEDS
            current = []
            for block, origins in populations[mode].items():
                for origin in origins:
                    for seed in seeds:
                        value = row(origin, seed, block)
                        value.update(origin_mode=mode, matrix=matrix, configuration=config,
                                     forecast_work_id=f'{mode}-{matrix}-{config}-{origin}-{seed}')
                        current.append(value)
            summary = p.summarize_group(current, populations[mode], seeds)
            originals.append(dict(origin_mode=mode, matrix=matrix, configuration=config,
                **{k: summary[k] for k in ('status', 'expected_forecasts', 'available_score_rows',
                    'missing_score_rows', 'counts_by_status', 'means')}))
            rows.extend(current)
    return dict(inputs=dict(populations=populations, score_rows=rows),
                recomputed=dict(metric_tables=originals), audit_sha256='a' * 64, analysis_sha256='b' * 64)


def test_complete_original_axes_and_all_time_views_without_new_scores(full_fixture):
    result = p.project(full_fixture, 'c' * 64)
    assert result['source_score_rows'] == 11368
    assert result['configuration_mode_views'] == 120 and result['time_views'] == 480
    assert result['new_fits'] == result['new_forecasts'] == result['new_scores'] == result['new_resampling'] == 0
    assert result['hypothesis_tests_performed'] is result['scientific_claim_authorized'] is result['human_accepted'] is False
    for name, count in [('endpoint-quantiles.csv', 120), ('marginal-crps.csv', 480)]:
        assert len(p.tables(result)[name].decode().splitlines()) == count + 1


@pytest.mark.parametrize('change', ['missing-axis', 'duplicate-axis', 'unexpected-axis', 'duplicate-work',
                                  'wrong-population', 'wrong-denominator', 'wrong-fde'])
def test_full_projection_rejects_changed_frozen_scope_or_original_binding(full_fixture, change):
    tables = full_fixture['recomputed']['metric_tables']
    if change == 'missing-axis':
        tables.pop()
    elif change == 'duplicate-axis':
        tables.append(tables[0])
    elif change == 'unexpected-axis':
        tables[0]['configuration'] = 'new model'
    elif change == 'duplicate-work':
        full_fixture['inputs']['score_rows'][1]['forecast_work_id'] = full_fixture['inputs']['score_rows'][0]['forecast_work_id']
    elif change == 'wrong-population':
        full_fixture['inputs']['populations']['causal_prefix'].pop('b0')
    elif change == 'wrong-denominator':
        tables[0]['expected_forecasts'] -= 1
    else:
        tables[0]['means']['fde_m'] += 1
    with pytest.raises(ValueError):
        p.project(full_fixture, 'c' * 64)


def test_external_input_pin_is_required_and_not_a_self_claim(tmp_path):
    payload = {'fixture': True}
    path = tmp_path / 'fixture.json'
    path.write_text(json.dumps(dict(payload=payload, sha256=p.digest(payload))), encoding='utf-8')
    assert p.load_export(path, p.digest(payload))[0] == payload
    with pytest.raises(ValueError, match='externally pinned'):
        p.load_export(path, '0' * 64)
    altered = dict(payload={'fixture': False}, sha256=p.digest(payload))
    path.write_text(json.dumps(altered), encoding='utf-8')
    with pytest.raises(ValueError, match='externally pinned'):
        p.load_export(path, p.digest(payload))


def test_manuscript_fragment_uses_preexisting_four_models_and_retains_quantile_scope(full_fixture):
    result = p.project(full_fixture, 'c' * 64)
    for language in ('en', 'zh'):
        fragment = p.manuscript_fragment(result, language).decode('utf-8')
        assert fragment.count(r'\label{tab:crps-endpoint-diagnostics}') == 1
        for name in ('Full01', 'GMM', 'dt300', 'Inertial'):
            assert sum(line.startswith(name + ' &') for line in fragment.splitlines()) == 5
        assert ('not population FDE quantiles' if language == 'en' else '不是总体FDE分位数') in fragment
        assert ('two marginals do not determine joint calibration' if language == 'en' else '两个边缘不确定联合校准') in fragment
