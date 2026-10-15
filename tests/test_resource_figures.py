"""Frozen synthetic metadata only; no scientific replay or native observation."""
from copy import deepcopy
import json
from xml.etree import ElementTree as ET

import pytest

from scripts.pirc25.aggregate import aggregate, fingerprint
from scripts.pirc25.figures import comparison_figures
from scripts.pirc25.resource_usage import summarize_resources
from test_resource_summary import measured_cell
from test_shared_evidence import bundle


def render(summary):
    value = aggregate(bundle())
    value['arms'][0]['resource_usage_summary'] = summary
    value['aggregate_hash'] = fingerprint({k: v for k, v in value.items() if k != 'aggregate_hash'})
    before = deepcopy(value)
    result = comparison_figures(value)
    assert value == before  # Rendering cannot recompute or mutate the analysis.
    tree = ET.fromstring(next(iter(result['figures'].values())))
    metadata = json.loads(tree.find('{http://www.w3.org/2000/svg}metadata').text)
    labels = '\n'.join(n.text or '' for n in tree.findall('{http://www.w3.org/2000/svg}text'))
    return result, metadata, labels


def test_all_attempt_resource_sources_and_units_reach_frozen_figure():
    summary = summarize_resources([measured_cell()])
    _, metadata, labels = render(summary)
    assert metadata['strata'][0]['resource_usage_summary'] == summary
    assert 'observed wall=40 ns; CPU=80 ns; complete' in labels
    assert 'self-process lifetime RSS maximum=200 bytes; complete' in labels
    assert 'not solver-only; not tree peak; not additive' in labels
    assert 'observed attempts=2' in labels and 'includes failed/resumed attempts' in labels


def test_partial_unknown_duration_is_not_complete_or_zero():
    summary = summarize_resources([measured_cell(missing=True)])
    _, _, labels = render(summary)
    assert 'observed wall=40 ns; CPU=80 ns; partial' in labels
    assert 'self-process lifetime RSS maximum=200 bytes; partial' in labels
    assert 'unavailable attempts=1' in labels
    assert 'full totals unknown' in labels


def test_unattempted_and_legacy_sources_remain_unavailable():
    summary = summarize_resources([measured_cell(peaks=(), walls=()), bundle()['cells'][1]])
    _, _, labels = render(summary)
    assert 'observed wall=unavailable; CPU=unavailable; partial' in labels
    assert 'self-process lifetime RSS maximum=unavailable; partial' in labels
    assert 'unattempted cells=1' in labels and 'legacy-unavailable cells=1' in labels


def test_missing_memory_does_not_hide_known_duration_in_figure():
    row = measured_cell(peaks=(100,), walls=(10,))
    row['resource_usage']['attempts'][0]['packet']['memory'].update(
        status='UNAVAILABLE', peak_resident_bytes=None)
    _, _, labels = render(summarize_resources([row]))
    assert 'observed wall=10 ns; CPU=20 ns; complete' in labels
    assert 'self-process lifetime RSS maximum=unavailable; partial' in labels


def test_resource_sources_count_toward_operation_quota_before_encoding(monkeypatch):
    from scripts.pirc25 import figures
    value = aggregate(bundle())
    legacy_operations = 256 + sum(8 + 8*len(arm['metrics']) for arm in value['arms'])
    assert comparison_figures(value, maximum_operations=legacy_operations)['figures']
    summary = summarize_resources([measured_cell()])
    value['arms'][0]['resource_usage_summary'] = summary
    def refuse_encoding(*args):
        pytest.fail('quota must reject before metadata serialization/drawing')
    monkeypatch.setattr(figures, '_encoded', refuse_encoding)
    # The exact old graph fits; the same allowance cannot hide added provenance.
    with pytest.raises(ValueError, match='RESOURCE_PLAN_REJECTED'):
        comparison_figures(value, maximum_operations=legacy_operations)


def test_resource_metadata_stays_in_failed_stratum_without_inventing_quality():
    value = aggregate(bundle())
    arm = value['arms'][0]
    arm.update(metrics={}, successful_cells=0, independent_n=0, status='incomplete')
    summary = summarize_resources([measured_cell()])
    arm['resource_usage_summary'] = summary
    output = comparison_figures(value)
    svg = next(iter(output['figures'].values()))
    assert 'No complete metric; missing/failed cells retained' in svg
    assert 'observed wall=40 ns; CPU=80 ns; complete' in svg
    assert 'n=0' in svg and 'self-process lifetime RSS maximum=200 bytes' in svg
    with pytest.raises(ValueError, match='RESOURCE_PLAN_REJECTED'):
        comparison_figures(value, maximum_total_bytes=1)


def test_legacy_figure_bytes_do_not_change_without_resource_summary():
    result = comparison_figures(aggregate(bundle()))
    assert fingerprint(result['figure_index']) == '015ab24d123e7b36332543942239d983a3752181731aa03ff180717627a11265'
    assert [e['sha256'] for e in result['figure_index']['figures']] == [
        'd82a3b406b6349bdc0688605a8e2eb554fc7c300974cba1f007365a46a484e2f']
