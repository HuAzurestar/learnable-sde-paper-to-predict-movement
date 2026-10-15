"""Synthetic saved-event comparison package; no native worker/store access."""
from copy import deepcopy
import csv
import io
import json
from xml.etree import ElementTree as ET

import pytest

from scripts.pirc25.aggregate import canonical, fingerprint
from scripts.pirc25.comparison import compare_package
from scripts.pirc25.computation_plan import comparison_package_plan
from test_resource_usage import fixture
from test_shared_adjudication import evidence
from test_shared_evidence import bundle, seal


def failed_resource_bundle():
    value = bundle()
    row = deepcopy(value['cells'][0])
    observation, _, registered, aid = fixture()
    registered.update(arm_id=row['arm_id'], block_id=row['block_id'], seed=row['seed'])
    spec = {'study_id': value['study_id'], 'code_hash': value['code_hash'], 'cells': [registered]}
    cell_hash, spec_hash = fingerprint(registered), fingerprint(spec)
    observation.update(study_id=value['study_id'], code_hash=value['code_hash'],
        spec_hash=spec_hash, cell_hash=cell_hash, execution_state='FAILED')
    observation['memory']['point'] = 'observer-call'
    row.update(cell_hash=cell_hash, registered_cell=registered, status='FAILED', metrics=None,
        attempt_id=aid, artifact_id=None,
        history=[{'attempt_id': aid, 'state': 'FAILED', 'error_code': 'WORKER_FAILED'}])
    def event(kind, seq, payload):
        body = {'event_kind': kind, 'sequence': seq, 'payload': payload}
        return {**body, 'hash': fingerprint(body)}
    stop = event('WORKER_TREE_STOPPED', 2, {'attempt_id': aid, 'reservation_id': 'synthetic-reservation',
        'confirmation': 'native-job-or-process-group-no-running-descendants'})
    settled = event('SETTLE', 3, {'attempt_id': aid, 'reservation_id': 'synthetic-reservation',
        'run_id': row['run_id'], 'study_id': value['study_id'], 'arm_id': row['arm_id'],
        'settled': True, 'reserved_ms': 300000, 'charged_ms': 123, 'monotonic_elapsed_ms': 123})
    packet_hash = fingerprint(observation)
    metadata = {'artifact_id': packet_hash, 'sha256': packet_hash, 'size_bytes': len(canonical(observation)),
        'role': 'propagation-resource-observation', 'study_id': value['study_id'], 'block_ids': [row['block_id']]}
    published = event('PROPAGATION_RESOURCE_RECORDED', 4, {
        'schema_version': 'pirc27-resource-record-v1', 'attempt_id': aid, 'run_id': row['run_id'],
        'spec_hash': spec_hash, 'cell_hash': cell_hash, 'code_hash': value['code_hash'],
        'policy_hash': fingerprint(registered['resource_observation_policy']), 'attempt_state': 'FAILED',
        'result_artifact_id': None, 'status': 'RECORDED', 'reason': None, 'artifact_id': packet_hash,
        'packet_hash': packet_hash, 'worker_stop_event_hash': stop['hash'], 'settlement_event_hash': settled['hash']})
    row['cost'] = {'unit': 'slot-ms', 'scope': 'all-cell-attempts-including-failures', 'charged_ms': 123,
        'reserved_ms': 0, 'measured_ms': 123, 'missing_attempt_ids': [], 'unknown_attempt_ids': [],
        'pending_attempt_ids': [], 'sources': [settled]}
    row['resource_usage'] = {'schema_version': 'pirc27-resource-history-v1',
        'peak_aggregation': 'not-additive;not-a-phase-delta;not-a-tree-peak', 'attempts': [{
            'attempt_id': aid, 'status': 'RECORDED', 'reason': None, 'artifact': metadata,
            'packet': observation, 'publication_event': published, 'worker_stop_event': stop,
            'settlement_event': settled, 'resume_event': None}]}
    value.update(registered_spec=spec, spec_hash=spec_hash, cells=[row],
        expected_cells=[{k: row[k] for k in ('cell_hash', 'arm_id', 'block_id', 'seed')}])
    return seal(value)


def test_managed_package_opt_in_copies_validated_failed_resources_to_every_output():
    source = failed_resource_bundle()
    original = deepcopy(source)
    output = compare_package(source, {'manifest_id': 'synthetic-resource'}, include_resource_summaries=True)
    assert source == original
    arm = output['aggregate']['arms'][0]
    summary = arm['resource_usage_summary']
    assert arm['successful_cells'] == arm['independent_n'] == 0 and arm['metrics'] == {}
    assert summary['pipeline_wall_ns'] == 100 and summary['pipeline_cpu_ns'] == 150
    assert summary['maximum_observed_self_peak_bytes'] == 4096
    assert arm['cost']['charged_ms'] == 123  # Different units and scope from pipeline ns.
    rows = list(csv.DictReader(io.StringIO(output['metrics_csv'])))
    assert json.loads(rows[0]['resource_usage_summary']) == summary and rows[0]['value'] == ''
    assert output['paper_index']['claims'] == []
    assert output['paper_index']['resource_usage_summaries'][0]['resource_usage_summary'] == summary
    svg = ET.fromstring(next(iter(output['figures'].values())))
    metadata = json.loads(svg.find('{http://www.w3.org/2000/svg}metadata').text)
    assert metadata['strata'][0]['resource_usage_summary'] == summary
    assert output['paper_index']['figure_index_hash'] == fingerprint(output['figure_index'])


def test_joint_resource_work_is_reserved_before_adjudication(monkeypatch):
    from scripts.pirc25 import comparison
    value = failed_resource_bundle()
    legacy = comparison_package_plan(value, 20_000_000)['planned_operation_bound']
    def unexpected(*args, **kwargs):
        pytest.fail('resource work must be rejected before scientific/statistical computation')
    monkeypatch.setattr(comparison, 'adjudicate', unexpected)
    with pytest.raises(ValueError, match='RESOURCE_PLAN_REJECTED'):
        compare_package(value, {'manifest_id': 'fixture'}, max_operations=legacy,
            include_resource_summaries=True)


@pytest.mark.parametrize('flag', [1, None, 'true'])
def test_resource_flag_is_strict_boolean_before_any_computation(flag, monkeypatch):
    from scripts.pirc25 import comparison
    def unexpected(*args, **kwargs):
        pytest.fail('invalid flag must fail before adjudication')
    monkeypatch.setattr(comparison, 'adjudicate', unexpected)
    with pytest.raises(ValueError, match='explicit boolean'):
        compare_package(evidence(), {}, include_resource_summaries=flag)
    with pytest.raises(ValueError, match='explicit boolean'):
        comparison_package_plan(evidence(), 20_000_000, include_resource_summaries=flag)


def test_malformed_resource_history_rejected_by_work_preflight():
    value = failed_resource_bundle()
    value['cells'][0]['resource_usage']['attempts'] = 'not-an-array'
    with pytest.raises(ValueError, match='RESOURCE_PLAN_REJECTED'):
        comparison_package_plan(value, 20_000_000, include_resource_summaries=True)


def test_attempt_count_quota_refuses_before_per_attempt_processing():
    value = failed_resource_bundle()
    value['cells'][0]['resource_usage']['attempts'] = [None]*100_001
    with pytest.raises(ValueError, match='RESOURCE_PLAN_REJECTED'):
        comparison_package_plan(value, 20_000_000, include_resource_summaries=True)


def test_resource_work_is_subtracted_from_statistics_and_added_to_graph_bound():
    source = failed_resource_bundle()
    old = comparison_package_plan(source, 20_000_000)
    new = comparison_package_plan(source, 20_000_000, include_resource_summaries=True)
    assert new['planned_operation_bound'] > old['planned_operation_bound']
    assert new['graph_operation_bound'] > old['graph_operation_bound']
    assert new['descriptive_operation_bound'] > old['descriptive_operation_bound']
    assert new['maximum_analysis_operations'] < old['maximum_analysis_operations']
    assert (new['maximum_analysis_operations'] + new['graph_operation_bound']
            + new['descriptive_operation_bound']) == 20_000_000


def test_resource_packet_tampering_is_not_summarized_as_measured():
    value = failed_resource_bundle()
    value['cells'][0]['resource_usage']['attempts'][0]['packet']['memory']['peak_resident_bytes'] += 1
    with pytest.raises(ValueError, match='resource'):
        compare_package(seal(value), {}, include_resource_summaries=True)


def test_default_comparison_package_bytes_remain_unchanged():
    output = compare_package(evidence(), {'manifest_id': 'synthetic-resource-regression'})
    assert fingerprint(output) == 'c68cc52558566accd39cd4981199bf11d6c9e28186fa17ae488d31e91d2ea7ac'
    assert compare_package(evidence(), {'manifest_id': 'synthetic-resource-regression'},
        include_resource_summaries=False) == output
    assert compare_package(evidence(), {'manifest_id': 'synthetic-resource-regression'},
        include_resource_summaries=True) == output  # Legacy has no invented observations.
