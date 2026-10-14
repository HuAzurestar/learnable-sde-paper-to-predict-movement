"""Bounded safe-summary copies and deterministic tables, not a permission issuer.

An authorized shared owner must supply the published, settled source and exact
technical/privacy review. This module never reads a runtime, data set or model,
fits anything, calculates new scores/intervals or grants public access.
"""
from copy import deepcopy
import hashlib
import json
import math
import re

SCHEMA = 'pirc26-reviewed-paper-summary-v1'
ROOTS = ('M1', 'real_comparisons', 'real_diagnostics', 'real_case_status_counts',
         'O2', 'gradient_routes', 'dispositions', 'scientific_qualification')
FORBIDDEN = {'unit_hash', 'segment_hash', 'unit_rows', 'samples', 'query_states', 'gradient',
    'checkpoint', 'optimizer', 'target', 'time_grid', 'initial', 'root', 'brownian_root_id',
    'data_root', 'runtime_root', 'controller_pid', 'helper_pid', 'process_id', 'parent_process_id',
    'authorization', 'authorization_id', 'grant_id', 'input_grant', 'output_grant', 'command',
    'latitude', 'longitude', 'lat', 'lon', 'timestamp', 'timestamps', 'coordinates',
    'position', 'velocity', 'native_rows', 'source_trajectory_id', 'block_id', 'sample_id'}
REF_FIELDS = ('attempt_id', 'artifact_id', 'study_id', 'blueprint_hash', 'charged_ms', 'status')
EPOCHS = {
    '3ce392ca03b649b537c6766e37402e0597fdda7d110243ca16cc386b7fc729cb': 'c0097bb1069131eee87ab45a4daf7ecd538c0a23',
    '578687236fca88752d9332840f8e108c3580d309a32693547ce108095fcc316f': '9ce90059f3611089150928d47aaa0393b699a016',
}


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf8')


def fingerprint(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError('PIRC26_EVIDENCE: ' + message)


def safe_tree(value):
    if type(value) is dict:
        require(len(value) <= 128, 'object size')
        for key, item in value.items():
            require(type(key) is str and key not in FORBIDDEN, 'private field')
            if key in ('fit_rows', 'rollout_rows'):
                require(type(item) is int, 'aggregate count only, not training rows')
            safe_tree(item)
    elif type(value) is list:
        require(len(value) <= 1000, 'list size')
        for item in value:
            safe_tree(item)
    elif type(value) is str:
        require(len(value) <= 4096, 'string size')
        require(not re.search(r'(?i)(?:\b[A-Z]:[\\/]|[\\/]Users[\\/]|[\\/]home[\\/])', value), 'local path')
        require('PRIVATE KEY' not in value and not re.search(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,})', value), 'credential')
    elif type(value) is float:
        require(math.isfinite(value), 'nonfinite number')
    else:
        require(value is None or type(value) in (int, bool), 'unsupported primitive')


def make_summary(source, reference, review):
    require(source.get('schema_version') == 'pirc26-compact-copied-evidence-v1', 'compact schema')
    require(source.get('public_export_authorized') is False, 'source is not a public export')
    require(source.get('statistical_recomputation') is False and source.get('final_test_read') is False, 'source limits')
    require(review.get('decision') == 'APPROVED_SAFE_DERIVATION_ONLY', 'exact owner technical review required')
    require(review.get('source_artifact_id') == reference['artifact_id'], 'review source binding')
    require(review.get('destination') == 'HuAzurestar/learnable-sde-paper-to-predict-movement/paper/pirc26', 'destination')
    require(review.get('raw_model_test_disclosure') is False, 'no raw/model/test authority')
    value = {key: deepcopy(source[key]) for key in ROOTS}
    value.update(schema_version=SCHEMA, source_compact_sha256=reference['artifact_id'],
        source_compact_attempt_id=reference['attempt_id'], review=deepcopy(review),
        review_hash=fingerprint(review), source_catalog={}, cost_snapshot=deepcopy(source['cost_snapshot']),
        environment={'python': '3.10.13', 'platform': 'Windows', 'machine': 'AMD64', 'device': 'cpu',
            'dtype': 'float64', 'threads': 1, 'torch': '2.3.1+cu121', 'numpy': '1.26.4',
            'torchsde': '0.2.6', 'trampoline': '0.1.2'},
        provenance_limits={'public_raw_data_license_claimed': False, 'raw_or_model_export': False,
            'final_test': False, 'scientific_qualification': 'not-established',
            'cost_scope': 'all reserved attempts through compact copy; later builds/validation resolve separate receipts',
            'source_availability': 'safe aggregates public; complete original artifacts controlled, not shipped'})
    for label, src in source['provenance'].items():
        require(src['source_code_hash'] in EPOCHS, 'unknown source epoch')
        value['source_catalog'][label] = {
            'reference': {k: deepcopy(src['reference'][k]) for k in REF_FIELDS if k in src['reference']},
            'source_code_hash': src['source_code_hash'], 'source_code_sha': EPOCHS[src['source_code_hash']],
            'source_protocol_hash': src['source_protocol_hash'], 'source_spec_hash': src['source_spec_hash'],
            'source_body_sha256': src['source_body_sha256'], 'charged_ms': src['charged_ms']}
    require(reference['attempt_id'] not in {c['attempt_id'] for c in value['cost_snapshot']}, 'copy cost not already counted')
    value['cost_snapshot'].append({'arm_id': 'pirc26-m0-o1', 'attempt_id': reference['attempt_id'],
                                   'charged_ms': reference['charged_ms'], 'settled': True})
    value['safe_summary_hash'] = fingerprint(value)
    validate_summary(value)
    return value


def validate_summary(value):
    require(value.get('schema_version') == SCHEMA, 'public schema')
    require(value.get('safe_summary_hash') == fingerprint({k: v for k, v in value.items() if k != 'safe_summary_hash'}), 'summary hash')
    safe_tree(value)
    require(value['review_hash'] == fingerprint(value['review']), 'review hash')
    require(value['review']['source_artifact_id'] == value['source_compact_sha256'], 'review artifact')
    require(value['scientific_qualification'] == 'not-established', 'no global qualification')
    require(set(value['source_catalog']) == {'M1-S', 'M1-R', 'paired', 'diagnostics', 'O2', 'routes'}, 'six exact sources')
    for src in value['source_catalog'].values():
        for sha in (src['source_body_sha256'], src['source_code_hash'], src['source_protocol_hash'], src['source_spec_hash']):
            require(bool(re.fullmatch('[0-9a-f]{64}', sha)), 'source hash')
    for family in ('M0', 'M2'):
        counts = value['real_case_status_counts'][family]
        require(sum(counts.values()) == 282, 'real declared denominator')
        require(counts.get('MEASURED') == 63 and counts.get('NO_CAUSAL_NATIVE_COVERAGE') == 216
                and counts.get('SOURCE_UNAVAILABLE') == 3, 'fixed real outcomes')
        require(sum(n for s, n in counts.items() if s not in ('MEASURED', 'NO_CAUSAL_NATIVE_COVERAGE', 'SOURCE_UNAVAILABLE')) == 0,
                'nonmeasured outcomes must not be silently dropped')
    require([r['horizon_seconds'] for r in value['real_comparisons']] == [10, 30, 60], 'horizon order')
    require([r['paired_original_units'] for r in value['real_comparisons']] == [6, 6, 5], 'unit counts')
    require([r['paired_successful_segments'] for r in value['real_comparisons']] == [26, 17, 20], 'segment counts')
    for row in value['real_comparisons']:
        require(row['candidate_units'] == 7 and row['blind_test'] is False and row['qualification'] == 'not-established', 'conditional scope')
        require(all(m['formal_superiority_claim'] is False for m in row['metrics'].values()), 'no formal ranking')
    for family, rows in value['real_diagnostics'].items():
        require(family in ('M0', 'M2') and [r['horizon_seconds'] for r in rows] == [10, 30, 60], 'diagnostic horizons')
        require(sum(r['declared_rows'] for r in rows) == 282, 'diagnostic denominator')
    for model in value['M1'].values():
        a = model['aggregate']
        require(a['fit_rows'] == a['measured_fits'] == 40 and a['rollout_rows'] == a['measured_rollouts'] == 30, 'M1 population')
        require(a['matched_teacher_rows'] == 20 and a['matched_recovery_passes'] == 12, 'M1 recovery failures retained')
        require(model['calibration']['matched_discrete_teacher_recovery'] == 'NOT_PASSED', 'do not promote M1')
    require([(r['seed'], r['step_seconds']) for r in value['O2']['rows']] == [
        (s, dt) for s in (26101411, 26101412, 26101413) for dt in (.25, .125)], 'six O2 cells')
    for r in value['O2']['rows']:
        require(r['status'] == 'MEASURED' and r['controlled_feasibility_passed'] is True, 'actual O2 outcomes')
        require(r['fit']['steps'] == 12 and r['fit']['status'] == 'MAX_STEPS', 'updates are not convergence')
        require(len(r['gradient_checks']) == 4 and all(c['passed'] for c in r['gradient_checks']), 'four O2 FD checks')
    require([(r['seed'], r['step_seconds'], r['solver']) for r in value['gradient_routes']['rows']] == [
        (s, dt, solver) for s in (26101411, 26101412, 26101413) for dt in (.25, .125)
        for solver in ('reversible_heun', 'midpoint')], 'all twelve route pairs')
    for r in value['gradient_routes']['rows']:
        require(r['status'] == 'MEASURED' and r['controlled_route_passed'] is True, 'route outcomes')
        require(r['forward_matched'] and r['finite_difference_passed'] and r['brownian_paired'] and r['resource_gate_passed'], 'all source gates')
    require(value['dispositions']['whole_unit_gate_n'] == 1 and value['dispositions']['global_winner'] == 'NOT_ESTABLISHED', 'formal limits')
    costs = value['cost_snapshot']
    require(len({r['attempt_id'] for r in costs}) == len(costs) and all(r['settled'] is True for r in costs), 'all-attempt unique settled costs')
    for arm in {r['arm_id'] for r in costs}:
        require(sum(r['charged_ms'] for r in costs if r['arm_id'] == arm) <= 86400000, 'cumulative arm budget')
    return value


def number(value, places=3):
    return '--' if value is None else f'{value:.{places}f}'


def table(columns, rows):
    return '\\begin{tabular}{' + ' '.join('r' for _ in columns) + '}\n\\toprule\n' + ' & '.join(columns) + ' \\\\\n\\midrule\n' + ''.join(' & '.join(map(str, row)) + ' \\\\\n' for row in rows) + '\\bottomrule\n\\end{tabular}\n'


def render_tables(value):
    validate_summary(value)
    files = {}
    rows = []
    for row in value['real_comparisons']:
        e = row['metrics']['energy_score_mean_m']
        interval = e['exploratory_conditional_percentile_95_interval']
        rows.append([row['horizon_seconds'], row['paired_original_units'], row['paired_successful_segments'],
            number(e['M0_unit_mean']), number(e['M2_unit_mean']), number(e['M2_minus_M0_unit_mean']),
            '[' + ', '.join(number(x) for x in interval) + ']'])
    files['real-energy.tex'] = table(['$h$(s)', '$n$', '$C$', 'M0 (m)', 'M2 (m)', '$\\Delta$(m)', 'conditional 95\\% interval'], rows)
    rows = []
    for i, h in enumerate((10, 30, 60)):
        left = value['real_diagnostics']['M0'][i]['equal_original_unit_metrics']
        right = value['real_diagnostics']['M2'][i]['equal_original_unit_metrics']
        rows.append([h, number(left['marginal_x_coverage_0.95'], 6), number(left['marginal_y_coverage_0.95'], 6),
            number(right['marginal_x_coverage_0.95'], 6), number(right['marginal_y_coverage_0.95'], 6),
            number(left['paired_endpoint_position_rms_m']), number(right['paired_endpoint_position_rms_m'])])
    files['real-calibration.tex'] = table(['$h$(s)', 'M0 $c_x$', 'M0 $c_y$', 'M2 $c_x$', 'M2 $c_y$', 'M0 RMS(m)', 'M2 RMS(m)'], rows)
    files['m1-recovery.tex'] = table(['model', 'fits', 'rollouts', 'matched pass', 'matched total', 'condition max'],
        [[family, m['aggregate']['measured_fits'], m['aggregate']['measured_rollouts'], m['aggregate']['matched_recovery_passes'],
          m['aggregate']['matched_teacher_rows'], number(m['aggregate']['condition_number_max'])] for family, m in sorted(value['M1'].items())])
    files['o2-feasibility.tex'] = table(['seed', '$\\Delta t$(s)', 'updates', 'fit(s)', 'lifetime RSS(MiB)', 'FD pass'],
        [[r['seed'], r['step_seconds'], r['fit']['steps'], number(r['fit']['wall_seconds']),
          number(r['resources']['peak_resident_bytes'] / 1048576, 1), sum(c['passed'] for c in r['gradient_checks'])]
         for r in value['O2']['rows']])
    rows = []
    for r in value['gradient_routes']['rows']:
        direct, candidate = r['helpers']['direct'], r['helpers']['candidate']
        rows.append([r['seed'], r['step_seconds'], r['route'], f"{r['gradient_relative_l2']:.3e}",
            number(direct['benchmark_wall_seconds']), number(candidate['benchmark_wall_seconds']),
            number(direct['resources']['peak_resident_bytes'] / 1048576, 1),
            number(candidate['resources']['peak_resident_bytes'] / 1048576, 1)])
    files['gradient-routes.tex'] = table(['seed', '$\\Delta t$', 'route', 'rel.$\\ell_2$', 'direct(s)', 'candidate(s)', 'direct MiB', 'candidate MiB'], rows)
    files['costs.tex'] = table(['arm', 'charged slot-s', 'cap slot-s'], [[arm.replace('_', '\\_'),
        number(sum(r['charged_ms'] for r in value['cost_snapshot'] if r['arm_id'] == arm) / 1000), '86400']
        for arm in sorted({r['arm_id'] for r in value['cost_snapshot']})])
    files['fde-mc.tex'] = table(['$h$(s)', 'M0 FDE(m)', 'M2 FDE(m)', 'M0 point SE(m)', 'M2 point SE(m)'],
        [[r['horizon_seconds'], number(r['metrics']['fde_m']['M0_unit_mean']), number(r['metrics']['fde_m']['M2_unit_mean']),
          number(value['real_diagnostics']['M0'][i]['equal_original_unit_metrics']['mean_pointwise_energy_jackknife_se_m']),
          number(value['real_diagnostics']['M2'][i]['equal_original_unit_metrics']['mean_pointwise_energy_jackknife_se_m'])]
         for i, r in enumerate(value['real_comparisons'])])
    return files


def claim_index(value, tables):
    validate_summary(value)
    links = {'RQ1': ['M1-S', 'M1-R'], 'RQ2': ['paired', 'diagnostics'], 'RQ3': ['O2', 'routes']}
    return {'schema_version': 'pirc26-paper-claim-index-v1', 'safe_summary_hash': value['safe_summary_hash'],
        'source_compact_sha256': value['source_compact_sha256'], 'review_hash': value['review_hash'],
        'claims': {rq: {'source_labels': sources, 'qualification': 'not-established'} for rq, sources in links.items()},
        'tables': {name: hashlib.sha256(body.encode('utf8')).hexdigest() for name, body in tables.items()},
        'no_new_statistical_adjudication': True, 'controlled_full_sources_required_for_full_numeric_rebuild': True}
