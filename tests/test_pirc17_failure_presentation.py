# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Saved metadata/document tests only; no scientific computation."""
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / 'paper/pirc17'
PATH = ROOT / 'failure-description-v1.json'
EVIDENCE = json.loads(PATH.read_text(encoding='utf-8'))


def test_bound_five_failures_and_limited_cause_evidence():
    ledger = json.loads((ROOT/'claim-ledger.json').read_text(encoding='utf-8'))['retained_execution_failure_description']
    assert hashlib.sha256(PATH.read_bytes()).hexdigest() == ledger['projection_sha256']
    assert len(EVIDENCE['failures']) == 5
    assert [r['failure_label'] for r in EVIDENCE['failures']] == ['F01','F02','F03','F04','F05']
    assert [r['configuration'] for r in EVIDENCE['failures']] == ['arm-06/dt30','arm-03/single_gaussian','lio-river','all-terrain','lio-road']
    assert all(not r['model_divergence_established'] and not r['item_exception_available']
               and not r['reply_file_present_in_checked_roots'] for r in EVIDENCE['failures'])
    assert all(r['evidential_scope'] == 'contemporaneous_run_summary_not_item_exception_log'
               for r in EVIDENCE['contemporaneous_history_annotations'])
    assert not ledger['item_specific_exception_or_numerical_divergence_established']


def test_four_families_unavailable_not_successful_intersections():
    rows = EVIDENCE['unavailable_families']
    assert len(rows) == 4
    assert [len(r['affected_contrasts']) for r in rows] == [5,4,4,4]
    assert [r['failed_labels'] for r in rows] == [['F04'],['F03','F05'],['F02'],['F01']]
    assert all(r['disposition'] == 'unavailable_entire_registered_family'
               and not r['successful_subset_inference_allowed'] for r in rows)
    assert not any(r['family'].startswith('method-') and r['origin_mode'] == 'causal_prefix' for r in rows)
    for field in ('new_fits','new_forecasts','new_particle_scores','retries'):
        assert EVIDENCE['scope'][field] == 0
    assert not EVIDENCE['scope']['forecast_arrays_opened']
    assert not EVIDENCE['scope']['independent_saved_output_audit']


@pytest.mark.parametrize('language', ['en','zh'])
def test_bilingual_failure_tables_and_no_unjustified_model_cause(language):
    tex = (ROOT/language/"historical-main-v1.tex").read_text(encoding='utf-8')
    for label in ('tab:retained-failures','tab:failure-family-dispositions'):
        assert tex.count('\\label{'+label+'}') == 1
    assert 'failure-description-v1.json' in tex
    assert all(text in tex for text in ('F01','F02','F03','F04','F05','6440'))
    if language == 'en':
        assert 'not recovered\nitem-level exception traces' in tex
        assert 'not measured prediction times' in tex
        assert 'cannot support the registered overall-terrain' in tex
    else:
        assert '不是恢复出来的逐项异常栈' in tex
        assert '不是预测实测耗时' in tex
        assert '不能支持登记的总体地形或各因素裁定' in tex
