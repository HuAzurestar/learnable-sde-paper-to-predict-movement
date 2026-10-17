"""Summarize already-saved CRPS and endpoint quantiles, without new scoring.

Pure standard-library consumer of one externally pinned anonymous export.
No maps, trajectories, particles, models, fitting, simulation or resampling.
Failed/missing configurations remain unavailable, not successful-subset means.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
import math
from pathlib import Path

VERSION = 'pirc17-secondary-score-projection-v1'
MODES = ('causal_prefix', 'known_velocity', 'point_only')
SEEDS = tuple(range(20260814, 20260819))
TIMES = (60, 300, 900, 1800)
QUANTILES = ('0.5', '0.9', '0.95')
METHODS = ('arm-01/full', 'arm-02/pointwise', 'arm-03/single_gaussian',
    'arm-04/gmm_kernel', 'arm-05/explicit_decomp', 'arm-06/dt30', 'arm-06/dt60',
    'arm-06/dt120', 'arm-06/dt300', 'arm-06/dt600', 'arm-07/full', 'arm-08/qmle',
    'arm-09/mixed', 'arm-09/pure_es', 'arm-10/d2_mc', 'arm-10/d2_closed',
    'arm-11/full', 'arm-12/scratch', 'arm-14/reptile', 'arm-15/drift_only',
    'arm-15/two_step', 'arm-16/full', 'arm-18/full', 'arm-19/em', 'arm-19/euler',
    'arm-20/full', 'arm-21/mc', 'arm-21/crn')
TERRAIN = ('all-terrain', 'base', 'lio-river', 'lio-road', 'lio-surface',
           'lio-worldcover', 'loo-river', 'loo-road', 'loo-surface', 'loo-worldcover')
AXES = (tuple(('NEX326-methods', c) for c in METHODS) +
        tuple(('terrain', c) for c in TERRAIN) +
        (('NEX326-diagnostic', 'diagnostic/full-exact-kernel'), ('inertial', 'all')))
SELECTED = (('Full01', 'NEX326-methods', 'arm-01/full'),
            ('GMM', 'NEX326-methods', 'arm-04/gmm_kernel'),
            ('dt300', 'NEX326-methods', 'arm-06/dt300'), ('Inertial', 'inertial', 'all'))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()


def load_export(path, expected_sha256):
    path = Path(path)
    if path.stat().st_size > 128 * 1024 * 1024:
        raise ValueError('export exceeds the existing 128MiB transport limit')
    record = json.loads(path.read_text(encoding='utf-8'))
    if record['sha256'] != expected_sha256 or digest(record['payload']) != expected_sha256:
        raise ValueError('export differs from externally pinned content hash')
    return record['payload'], hashlib.sha256(path.read_bytes()).hexdigest()


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError('finite nonnegative saved scalar required')
    return float(value)


def block_average(values, population, seeds):
    """Equal seeds within origin, equal origins within block, equal blocks."""
    return math.fsum(math.fsum(math.fsum(values[(origin, seed)] for seed in seeds)
        / len(seeds) for origin in origins) / len(origins)
        for origins in population.values()) / len(population)


def summarize_group(rows, population, seeds):
    origins = {origin: block for block, group in population.items() for origin in group}
    if not population or len(origins) != sum(map(len, population.values())) or any(not x for x in population.values()):
        raise ValueError('unique nonempty registered origin/block membership required')
    expected = {(origin, seed) for origin in origins for seed in seeds}
    keyed = {}
    for row in rows:
        key = (row['origin_id'], row['seed'])
        if key in keyed or key not in expected or row['independent_block_id'] != origins[key[0]]:
            raise ValueError('duplicate, unexpected or misbound origin/seed row')
        if row['status'] not in {'success', 'failed'}:
            raise ValueError('closed original success/failure disposition required')
        if row['status'] == 'failed' and row['scores'] is not None:
            raise ValueError('failed row cannot carry substitute successful scores')
        keyed[key] = row
    counts = dict(sorted(Counter(r['status'] for r in rows).items()))
    result = dict(expected_forecasts=len(expected), available_score_rows=len(rows),
        missing_score_rows=len(expected - keyed.keys()), counts_by_status=counts,
        recording_hash_blocks=len(population), seeds_per_origin=len(seeds),
        status='unavailable', means=None)
    # Validate successful rows even in an unavailable group; never silently omit bad scalars.
    fields = defaultdict(dict)
    elapsed = [[] for _ in TIMES]
    for key, row in keyed.items():
        if row['status'] != 'success':
            continue
        scores = row['scores']
        count = scores['particle_count']
        if type(count) is not int or count < 1:
            raise ValueError('positive integer saved particle count required')
        quantiles = scores['particle_endpoint_error_quantiles_m']
        if set(quantiles) != set(QUANTILES):
            raise ValueError('all three original endpoint quantiles required')
        q = [number(quantiles[level]) for level in QUANTILES]
        if q != sorted(q):
            raise ValueError('ordered within-forecast endpoint quantiles required')
        for level, value in zip(QUANTILES, q):
            fields['endpoint_q' + level][key] = value
        fields['fde_m'][key] = number(scores['fde_m'])
        times = scores['by_time']
        if len(times) != 4:
            raise ValueError('all four original scoring slots required')
        previous = -1
        for i, time in enumerate(times):
            t = number(time['elapsed_seconds'])
            if t <= previous:
                raise ValueError('ordered actual recorded scoring times required')
            previous = t
            elapsed[i].append(t)
            crps = time['marginal_crps_m']
            if not isinstance(crps, list) or len(crps) != 2:
                raise ValueError('both original local-coordinate CRPS values required')
            for axis, value in zip(('east', 'north'), crps):
                fields[f'crps_{i}_{axis}'][key] = number(value)
    if len(keyed) != len(expected) or counts != {'success': len(expected)}:
        return result
    means = {name: block_average(value, population, seeds) for name, value in fields.items()}
    result.update(status='computed', means=dict(
        fde_m=means['fde_m'],
        mean_within_forecast_endpoint_quantiles_m={q: means['endpoint_q' + q] for q in QUANTILES},
        by_time=[dict(nominal_seconds=t, actual_elapsed_seconds_range=[min(elapsed[i]), max(elapsed[i])],
                     crps_east_m=means[f'crps_{i}_east'], crps_north_m=means[f'crps_{i}_north'])
                 for i, t in enumerate(TIMES)]))
    return result


def project(payload, source_sha256):
    inputs = payload['inputs']
    populations = inputs['populations']
    if set(populations) != set(MODES):
        raise ValueError('all three frozen origin modes required')
    for mode, size in zip(MODES, (46, 6, 6)):
        population = populations[mode]
        if len(population) != size or any(len(group) != 1 for group in population.values()):
            raise ValueError('unchanged frozen one-origin recording-block grid required')
    expected_axes = {(mode, matrix, config) for mode in MODES for matrix, config in AXES}
    originals = {}
    for table in payload['recomputed']['metric_tables']:
        key = (table['origin_mode'], table['matrix'], table['configuration'])
        if key in originals or key not in expected_axes:
            raise ValueError('duplicate or unexpected original metric axis')
        originals[key] = table
    if set(originals) != expected_axes:
        raise ValueError('all 120 original configuration/mode axes required')
    grouped, work_ids = defaultdict(list), set()
    for row in inputs['score_rows']:
        key = (row['origin_mode'], row['matrix'], row['configuration'])
        if key not in expected_axes or row['forecast_work_id'] in work_ids:
            raise ValueError('unexpected score axis or duplicate forecast work ID')
        work_ids.add(row['forecast_work_id'])
        grouped[key].append(row)
    records = []
    for mode in MODES:
        for matrix, config in AXES:
            key = (mode, matrix, config)
            group = summarize_group(grouped[key], populations[mode], (None,) if matrix == 'inertial' else SEEDS)
            original = originals[key]
            for name in ('expected_forecasts', 'available_score_rows', 'missing_score_rows', 'counts_by_status', 'status'):
                if group[name] != original[name]:
                    raise ValueError('projection differs from original frozen metric disposition: ' + name)
            if group['means'] is not None:
                if not math.isclose(group['means']['fde_m'], original['means']['fde_m'], abs_tol=1e-9, rel_tol=1e-12):
                    raise ValueError('saved FDE does not reproduce original equal-block summary')
            records.append(dict(origin_mode=mode, matrix=matrix, configuration=config, **group))
    return dict(schema_version=VERSION, source_export_sha256=source_sha256,
        source_audit_sha256=payload['audit_sha256'], source_analysis_sha256=payload['analysis_sha256'],
        source_score_rows=len(inputs['score_rows']), configuration_mode_views=len(records), time_views=4 * len(records),
        aggregation='equal seeds within origin; equal origins within recording-hash block; equal blocks',
        endpoint_quantile_role='mean of saved within-forecast particle endpoint error quantiles; not pooled particle or population FDE quantiles',
        coordinate_role='local east/north marginal CRPS; not rotationally invariant joint ES',
        new_fits=0, new_forecasts=0, new_scores=0, new_resampling=0,
        hypothesis_tests_performed=False, physical_clock_certified=False,
        independent_participants_certified=False, numerically_qualified=False,
        scientific_claim_authorized=False, human_accepted=False, records=records)


def csv_bytes(rows):
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode('utf-8')


def tables(projection):
    endpoints, times = [], []
    for row in projection['records']:
        common = {k: row[k] for k in ('origin_mode', 'matrix', 'configuration', 'status',
            'expected_forecasts', 'available_score_rows', 'missing_score_rows', 'recording_hash_blocks', 'seeds_per_origin')}
        common.update(success_rows=row['counts_by_status'].get('success', 0), failed_rows=row['counts_by_status'].get('failed', 0))
        means = row['means']
        endpoints.append(dict(common, fde_m=None if means is None else means['fde_m'],
            **{'mean_within_forecast_q' + q + '_m': None if means is None else means['mean_within_forecast_endpoint_quantiles_m'][q] for q in QUANTILES}))
        for i, nominal in enumerate(TIMES):
            saved = None if means is None else means['by_time'][i]
            times.append(dict(common, nominal_seconds=nominal,
                actual_seconds_min=None if saved is None else saved['actual_elapsed_seconds_range'][0],
                actual_seconds_max=None if saved is None else saved['actual_elapsed_seconds_range'][1],
                crps_east_m=None if saved is None else saved['crps_east_m'],
                crps_north_m=None if saved is None else saved['crps_north_m']))
    return {'endpoint-quantiles.csv': csv_bytes(endpoints), 'marginal-crps.csv': csv_bytes(times)}


def manuscript_fragment(projection, language):
    rows = {(r['matrix'], r['configuration']): r for r in projection['records'] if r['origin_mode'] == 'causal_prefix'}
    if language == 'en':
        caption = ('Saved marginal CRPS and within-forecast endpoint error quantiles (metres). '
            'Lower CRPS is better for that coordinate; two marginals do not determine joint calibration. '
            'Each stochastic configuration uses 46 recording-hash blocks and five seeds (230 forecasts); '
            'inertial uses the same 46 blocks with one deterministic path each. '
            'Quantile entries are block/seed means of per-forecast particle error quantiles, '
            'not population FDE quantiles, pooled particles or a best-particle path. '
            'All targets retain their original recorded elapsed time; no per-horizon hypothesis test.')
        heads = ('Model', 'Nominal min', 'CRPS east', 'CRPS north')
        lower = ('Model', 'Mean FDE', 'Mean $q_{.50}$', 'Mean $q_{.90}$', 'Mean $q_{.95}$')
    else:
        caption = ('保存的边缘CRPS及单次预测内粒子终点误差分位数，单位米。'
            'CRPS在其坐标上越小越好，两个边缘不确定联合校准。随机配置各使用46个记录哈希块、'
            '五种子，共230次预测；惯性参考在相同46块上各有一条确定性路径。'
            '分位项是每次预测内粒子误差分位数的块／种子均值，不是总体FDE分位数、'
            '合并粒子分位数或最优粒子路径。保留原实际记录时刻，不新增逐时域假设检验。')
        heads = ('模型', '名义分钟', '东坐标CRPS', '北坐标CRPS')
        lower = ('模型', '平均FDE', '均值$q_{.50}$', '均值$q_{.90}$', '均值$q_{.95}$')
    lines = [r'\begin{table}[htbp]', r'\centering\small', r'\caption{' + caption + '}',
             r'\label{tab:crps-endpoint-diagnostics}', r'\begin{tabular}{@{}lrrr@{}}', r'\toprule',
             ' & '.join(heads) + r'\\', r'\midrule']
    for name, matrix, config in SELECTED:
        means = rows[(matrix, config)]['means']
        if means is None:
            raise ValueError('predeclared existing main-text configuration is unavailable')
        for time in means['by_time']:
            lines.append(f"{name} & {time['nominal_seconds']//60} & {time['crps_east_m']:.2f} & {time['crps_north_m']:.2f}" + r'\\')
    lines.extend([r'\bottomrule', r'\end{tabular}', r'\par\medskip',
                  r'\begin{tabular}{@{}lrrrr@{}}', r'\toprule', ' & '.join(lower) + r'\\', r'\midrule'])
    for name, matrix, config in SELECTED:
        means = rows[(matrix, config)]['means']
        values = [means['fde_m']] + [means['mean_within_forecast_endpoint_quantiles_m'][q] for q in QUANTILES]
        lines.append(name + ' & ' + ' & '.join(f'{v:.2f}' for v in values) + r'\\')
    lines.extend([r'\bottomrule', r'\end{tabular}', r'\end{table}', ''])
    return '\n'.join(lines).encode('utf-8')


def generate(input_path, expected_sha256, output_directory):
    payload, file_hash = load_export(input_path, expected_sha256)
    result = project(payload, expected_sha256)
    result['source_export_file_sha256'] = file_hash
    result['projection_code_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    record = dict(payload=result, sha256=digest(result))
    files = tables(result)
    files['projection.json'] = (json.dumps(record, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')
    for language in ('en', 'zh'):
        files[language + '/secondary-score-diagnostics.tex'] = manuscript_fragment(result, language)
    manifest = dict(schema_version=VERSION, source_export_sha256=expected_sha256,
        projection_sha256=record['sha256'], files={name: dict(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
        for name, data in files.items()}, new_forecasts=0, new_scores=0, human_accepted=False)
    files['manifest.json'] = (json.dumps(dict(payload=manifest, sha256=digest(manifest)),
        sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')
    output = Path(output_directory)
    if output.exists() and any(output.iterdir()):
        raise ValueError('choose a new empty projection directory; never overwrite original evidence')
    output.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print(json.dumps(dict(projection_sha256=record['sha256'], source_score_rows=result['source_score_rows'],
        configuration_mode_views=result['configuration_mode_views'], time_views=result['time_views'],
        new_scores=0, new_forecasts=0)))
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--output-directory', type=Path, required=True)
    args = parser.parse_args()
    generate(args.input, args.sha256, args.output_directory)
