"""Saved terrain descriptive arithmetic and rhetorical boundaries, no private input."""
import copy
import hashlib
import json
from pathlib import Path
import pytest
from scripts.plot_pirc17_terrain import validate
from scripts.describe_pirc17_terrain import aggregate

ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT/'paper/pirc17'


def data():
    return json.loads((PAPER/'terrain-description-v1/summary.json').read_text(encoding='utf-8'))


def test_original_failures_and_common_subset_are_both_retained():
    d=data()
    validate(d)
    p=d['population']
    assert p['successful_slots']+p['failed_slots']==2300
    assert p['jointly_complete_slots']==43*10*5
    assert p['excluded_blocks']==3
    assert sum(r['full_grid_failed_slots'] for r in d['rows'])==3
    assert all(r['full_grid_expected_slots']==230 and r['common_complete_blocks']==43 for r in d['rows'])
    assert d['scope']['registered_full_family_inference']=='unavailable'
    assert not d['scope']['successful_subset_used_for_confirmatory_inference']


def test_saved_scalar_deltas_and_pairwise_sensitivity():
    rows={r['configuration']:r for r in data()['rows']}
    base=rows['base']['common_complete_profile']
    for row in rows.values():
        control=rows[row['contrast_control']]['common_complete_profile']
        assert row['common_delta_es_m']==pytest.approx(row['common_complete_profile']['es_m']-control['es_m'])
    assert rows['all-terrain']['common_delta_es_m']==pytest.approx(26.980933045466543)
    assert rows['all-terrain']['common_blocks_lower_es']==22
    assert rows['lio-river']['common_delta_es_m']>0>rows['lio-river']['pairwise_delta_es_m']
    river=rows['lio-river']['common_complete_profile']['es_by_horizon_m']
    assert river[2]<base['es_by_horizon_m'][2] and river[3]>base['es_by_horizon_m'][3]
    assert max(r['common_complete_profile']['coverage90_by_horizon'][-1] for r in rows.values())<.53


def test_rendered_values_and_bytes_are_bound_to_anonymous_aggregate():
    folder=PAPER/'figures/terrain-description-v1'
    m=json.loads((folder/'manifest.json').read_text())
    assert m['source_sha256']==hashlib.sha256((PAPER/'terrain-description-v1/summary.json').read_bytes()).hexdigest()
    for path,sha in m['files_sha256'].items():
        assert hashlib.sha256((folder/path).read_bytes()).hexdigest()==sha
    for row,values in zip(data()['rows'],m['displayed']['coverage90_pct']):
        assert values==pytest.approx([100*x for x in row['common_complete_profile']['coverage90_by_horizon']])
    raw=(PAPER/'terrain-description-v1/summary.json').read_text()
    assert all(key not in raw for key in ('origin_id','origin_rank','independent_block_id','center_m','sample_id','target_sha256'))


def test_renderer_rejects_full_population_or_false_inference_relabelling():
    d=copy.deepcopy(data())
    d['population']['jointly_complete_blocks']=46
    with pytest.raises(ValueError): validate(d)
    d=data()
    d['scope']['registered_full_family_inference']='beneficial'
    with pytest.raises(ValueError): validate(d)


def test_aggregation_is_block_equal_after_seeds_not_pooled_unequal_seeds():
    first=aggregate([{'es':0.0},{'es':10.0}])
    second=aggregate([{'es':100.0},{'es':100.0}])
    assert aggregate([first,second])['es']==52.5


@pytest.mark.parametrize('language',['en','zh'])
def test_terrain_evidence_is_in_body_and_conclusion_not_only_unavailable(language):
    main=(PAPER/language/'main.tex').read_text(encoding='utf-8')
    terrain=(PAPER/language/'reader-v6-terrain-results.tex').read_text(encoding='utf-8')
    assert r'\input{reader-v6-terrain-results.tex}' in main
    assert all(v in terrain for v in ('43','2,300','2,297','26.98','69.11','42.51','57.27','40.47','52.09'))
    assert r'\label{fig:terrain-description}' in terrain
    conclusion=main.split(r'\section{Conclusion}' if language=='en' else r'\section{结论}',1)[1]
    assert all(v in conclusion for v in ('26.98','39.00','52.09','RQ2'))
    assert 'post-hoc' in terrain if language=='en' else '事后' in terrain
