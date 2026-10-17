"""Synthetic card-to-TeX transport tests, never experimental evidence."""
from copy import deepcopy
import hashlib
import json

import pytest

from scripts import render_pirc17_paper_tables as module
from scripts import aggregate_pirc17 as source
from tests.test_pirc17_tables import cards, write_cards


def test_all_original_comparisons_and_cost_denominators_retained(cards):
    before = deepcopy(cards)
    files, counts, rows = module.fragments(cards, software_fixture=True)
    assert cards == before
    assert len(files) == 16
    assert len(rows['comparisons']) == 90
    for language in module.LANGUAGES:
        assert sum(counts[language+'/'+matrix+'-'+mode.replace('_','-')+'.tex']
                   for matrix in ('methods','terrain') for mode in source.MODES) == 90
        assert counts[language+'/kernel-costs.tex'] == 38
        assert counts[language+'/isolated-runtime.tex'] == 30
        assert all('SOFTWARE FIXTURE ONLY' in raw.decode('utf-8')
                   for name,raw in files.items() if name.startswith(language+'/'))
        visible = module.translated(('SOFTWARE FIXTURE ONLY -- no experimental evidence.',
                                     '仅合成软件测试数据，不是实验结果。'),language)
        assert all(r'\paragraph{'+visible+'}' in raw.decode('utf-8')
                   for name,raw in files.items() if name.startswith(language+'/'))
    assert all(r['expected_forecasts']==290 for r in rows['kernel_costs'])
    assert all(r['delta_candidate_minus_control_m'] is None for r in rows['comparisons'])


@pytest.mark.parametrize('language', module.LANGUAGES)
def test_unavailable_and_three_state_flags_do_not_become_zero_or_pass(cards, language):
    files, _, _ = module.fragments(cards, software_fixture=True)
    text = files[language+'/terrain-causal-prefix.tex'].decode('utf-8')
    assert '--'+r'\newline [--, --]' in text
    assert 'unavailable' in text
    assert module.flag(None,language) in text
    assert module.flag(False,language) != module.flag(None,language)
    assert module.flag(True,language) != module.flag(False,language)
    cost = files[language+'/kernel-costs.tex'].decode('utf-8')
    assert '0 / 290 & -- & --' in cost


@pytest.mark.parametrize('language', module.LANGUAGES)
def test_original_asymmetric_interval_sign_roles_reason_and_flags_preserved(cards, language):
    value = deepcopy(cards)
    family = value['family_evidence']['causal_prefix']['method-model-structure']
    family['independent_block_count'] = 46
    family['inference'] = {'results': {'0': {
        'candidate':'all-terrain','control':'loo-road',
        'delta_estimate_m':-60.0,'improvement_m':60.0,
        'simultaneous_interval_m':[-80.0,-55.0],
        'tail_check_passed':True}}}
    family['results']['0'].update(verdict='inconclusive',reason='planning_not_qualified',
                                  planning={'qualified':False},precision_invariant_verdict='inconclusive')
    files, _, rows = module.fragments(value, software_fixture=True)
    text = files[language+'/methods-causal-prefix.tex'].decode('utf-8')
    assert '-60'+r'\newline [-80, -55]' in text
    assert 'all-terrain'+r'\newline / loo-road' in text
    assert module.tex_text('planning_not_qualified') in text
    assert module.flag(True,language) in text and module.flag(False,language) in text
    r = next(r for r in rows['comparisons'] if r['origin_mode']=='causal_prefix'
             and r['family_id']=='method-model-structure' and r['comparison_id']=='0')
    assert r['delta_candidate_minus_control_m']==-60 and r['improvement_m']==60
    assert r['precision_invariant_verdict']=='inconclusive'


@pytest.mark.parametrize('interval', [[None,1],[1,None],[2,1],[float('nan'),1],[False,1]])
def test_bad_recorded_intervals_rejected_without_normalization(cards, interval):
    value = deepcopy(cards)
    value['family_evidence']['causal_prefix']['method-model-structure']['inference'] = {
        'results': {'0': {'delta_estimate_m':0,'simultaneous_interval_m':interval}}}
    with pytest.raises(ValueError):
        module.fragments(value)


@pytest.mark.parametrize('value', [float('nan'),float('inf'),True,'60'])
def test_nonfinite_or_wrong_numeric_types_rejected(value):
    with pytest.raises(ValueError):
        module.number(value)


def test_tex_text_is_literal_and_wraps_machine_identifiers():
    text = module.tex_text(r'\input{private} & 5% $x$ #A_B^~ /')
    assert r'\input{' not in text
    assert r'\textbackslash{}input\{private\}' in text
    assert r'\&' in text and r'5\%' in text and r'\$x\$' in text
    assert r'\_\allowbreak{}' in text and r'/\allowbreak{}' in text


@pytest.mark.parametrize('language', module.LANGUAGES)
def test_caption_retains_scientific_sign_and_scope(cards, language):
    files, _, _ = module.fragments(cards)
    text=files[language+'/methods-known-velocity.tex'].decode('utf-8')
    if language=='en':
        assert 'candidate minus control' in text and 'Secondary tasks are descriptive only' in text
        assert 'not automatically a beneficial terrain factor' in text
    else:
        assert '候选减对照' in text and '次要任务仅作描述' in text
        assert '不自动表示地形因素有益' in text
    assert text.count(r'\endfirsthead')==text.count(r'\endhead')==1
    assert r'\setlength{\LTcapwidth}{\linewidth}' in text
    assert module.translated(('continued','续表'),language) in text


def test_missing_cold_warm_latencies_are_not_recomputed(cards):
    files, _, rows = module.fragments(cards)
    assert all(r['summary'] is None for r in rows['runtime_conditions'])
    text=files['en/isolated-runtime.tex'].decode('utf-8')
    assert 'unavailable & -- & --' in text
    assert 'No quantiles are recomputed' in text and 'Warmup is excluded' in text


def test_recorded_runtime_summary_is_only_formatted_not_reestimated():
    rows=[dict(matrix='terrain',subject='base',condition='runtime_cold',status='computed',
               summary={'total_latency_p50_ms':12.3456,'total_latency_p95_ms':42.7},
               counts_by_status={'success':4,'failed':1})]
    before=deepcopy(rows)
    text=module.runtime_fragment(rows,'en')
    assert '12.35 & 42.7' in text and 'failed: 1'+r'\newline success: 4' in text
    assert rows==before


@pytest.mark.parametrize('language', module.LANGUAGES)
def test_runtime_caption_does_not_certify_uninterrupted_or_cache_isolated_latency(cards, language):
    before = deepcopy(cards)
    files, counts, rows = module.fragments(cards, software_fixture=True)
    text = files[language+'/isolated-runtime.tex'].decode('utf-8')
    if language == 'en':
        assert 'Original isolated cold/warm measurements' not in text
        for phrase in ('provider-cold/resident-warm elapsed times',
                       'not a verified reset of OS or interpreter caches',
                       'host-interruption and clock limitations',
                       'nor unflagged trials certify uninterrupted isolated',
                       'without sleep subtraction, trial exclusion or replacement measurement'):
            assert phrase in text
    else:
        assert '原隔离冷／热计时' not in text
        for phrase in ('提供器冷启动／驻留热启动墙钟耗时', '不认证操作系统或解释器缓存已重置',
                       '主机中断与时钟限制', '未标记试次均不认证',
                       '不扣除休眠时间、排除试次或补做测量'):
            assert phrase in text
    assert counts[language+'/isolated-runtime.tex'] == 30
    assert cards == before
    assert rows['runtime_conditions'] == source.project(before)['runtime_conditions']


@pytest.mark.parametrize('language', module.LANGUAGES)
def test_interruption_exposed_subject_values_and_counts_are_not_repaired(language):
    rows = [dict(matrix='terrain', subject=subject, condition='runtime_cold',
                 status='computed', counts_by_status={'success': 5},
                 summary={'total_latency_p50_ms': elapsed, 'total_latency_p95_ms': elapsed * 2})
            for subject, elapsed in (('all-terrain', 3000463.8613),
                                     ('loo-surface', 2315996.3217))]
    before = deepcopy(rows)
    text = module.runtime_fragment(rows, language)
    for row in before:
        assert module.tex_text(row['subject']) in text
        assert module.number(row['summary']['total_latency_p50_ms']) in text
        assert module.number(row['summary']['total_latency_p95_ms']) in text
    assert text.count('success: 5') == 2
    assert rows == before


def test_pinned_missing_only_generation_and_exact_manifest(cards,tmp_path):
    path=tmp_path/'cards.json';sha=write_cards(path,cards)
    result=module.generate(path,sha,tmp_path/'out',software_fixture=True)
    assert result==module.generate(path,sha,tmp_path/'out',software_fixture=True)
    root=tmp_path/'out'/source.digest({'schema_version':module.VERSION,
        'source_cards_sha256':sha,'renderer_sha256':hashlib.sha256(module.Path(module.__file__).read_bytes()).hexdigest(),
        'software_fixture_only':True})
    record=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    manifest=record['payload']
    assert source.digest(manifest)==record['sha256']==result['manifest_sha256']
    assert len(manifest['files'])==16
    assert manifest['scope']==cards['scope'] and manifest['source_cards_sha256']==sha
    assert len(manifest['exact_projected_rows']['comparisons'])==90
    for name,binding in manifest['files'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==binding['sha256']
    for key in ('manuscript_written','scientific_claim_authorized','human_accepted'):
        assert manifest[key] is False
    for key in ('new_forecasts','new_fits','new_scores','new_resampling'):
        assert manifest[key]==0
    with pytest.raises(ValueError,match='pinned'):
        module.generate(path,'0'*64,tmp_path/'wrong')
    assert not (tmp_path/'wrong').exists()


def test_existing_different_fragment_not_overwritten_or_partially_filled(cards,tmp_path):
    path=tmp_path/'cards.json';sha=write_cards(path,cards)
    result=module.generate(path,sha,tmp_path/'out',software_fixture=True)
    root=module.Path(result['output_directory'])
    protected=root/'en/terrain-causal-prefix.tex'
    protected.write_text('USER CONTENT',encoding='utf-8')
    absent=root/'zh/kernel-costs.tex';absent.unlink()
    with pytest.raises(ValueError,match='no overwrite'):
        module.generate(path,sha,tmp_path/'out',software_fixture=True)
    assert protected.read_text(encoding='utf-8')=='USER CONTENT' and not absent.exists()


@pytest.mark.parametrize('fault',['missing_mode','acceptance','secondary_tests','invented_runtime'])
def test_original_public_card_checks_still_apply(cards,fault):
    value=deepcopy(cards)
    if fault=='missing_mode':value['family_evidence'].pop('point_only')
    elif fault=='acceptance':value['human_accepted']=True
    elif fault=='secondary_tests':value['family_evidence']['known_velocity']['method-model-structure']['hypothesis_tests_performed']=True
    else:value['isolated_runtime_and_replay']['runtime_subjects'][0]['conditions']['runtime_cold']['summary']={}
    with pytest.raises(ValueError):module.fragments(value)
