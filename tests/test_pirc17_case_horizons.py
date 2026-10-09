"""Check authorized local case illustrations, not scientific qualification."""
import hashlib
import json
from pathlib import Path

import fitz
import pytest

ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT/'paper/pirc17'
PATH=PAPER/'figures/case-horizons.json'
DATA=json.loads(PATH.read_text(encoding='utf-8'))


def test_local_scope_does_not_become_public_permission_or_scientific_acceptance():
    assert DATA['local_manuscript_inclusion_requested'] is True
    for key in ('public_distribution_authorized','final_human_accepted',
                'independent_saved_output_audit','population_effects_established'):
        assert DATA[key] is False
    assert DATA['original_science_denominator']==11020 and DATA['primary_independent_blocks']==46
    assert DATA['selected_cases']==3 and DATA['reused_scientific_forecasts']==6
    assert DATA['seed']==20260814 and DATA['particles']==512 and DATA['maximum_step_seconds']==5
    for key in ('new_forecasts','new_fits','new_particle_scores','new_inference_tests'):
        assert DATA[key]==0
    text=PATH.read_text(encoding='utf-8')
    for private in ('center_m','sample_id','independent_block_id','work_id','positions_m','file_id','origin_epoch'):
        assert private not in text


def test_complete_fixed_cases_and_original_targets_are_retained():
    assert [(c['label'],c['country']) for c in DATA['cases']]==[('Boechout','BE'),('Bakewell','GB'),('Zagan','PL')]
    assert [c['actual_scoring_seconds'] for c in DATA['cases']]==[
        [60.,299.,899.,1801.],[61.,302.,907.,1802.],[54.,304.,904.,1805.]]
    for c in DATA['cases']:
        assert [m['subject'] for m in c['models']]==['base','all-terrain']
        assert len(c['figures'])==2
        for m in c['models']:
            assert m['status']=='success' and len(m['horizons'])==4
            assert sum(m['marginal_es_m'])/4==pytest.approx(m['weighted_es_m'])
            assert m['horizons'][-1]['mean_error_m']==pytest.approx(m['fde_m'])
            for h in m['horizons']:
                assert h['covered']==(h['mean_error_m']<=h['radius_m'])


FIGURES=[(case,i,figure) for case in DATA['cases'] for i,figure in enumerate(case['figures'])]


@pytest.mark.parametrize('case,index,figure',FIGURES,ids=[f[2]['pdf'] for f in FIGURES])
def test_image_hashes_four_panels_and_actual_numbers(case,index,figure):
    for extension in ('png','pdf'):
        path=PAPER/'figures'/figure[extension]
        assert hashlib.sha256(path.read_bytes()).hexdigest()==figure[extension+'_sha256']
    with fitz.open(PAPER/'figures'/figure['pdf']) as doc:
        assert len(doc)==1
        text=doc[0].get_text()
        assert text.count('512 predicted positions')==4
        assert 'No predicted trajectory' in text
        assert case['label'] in text
        for slot in (index*2,index*2+1):
            second=case['actual_scoring_seconds'][slot]
            assert f'actual {second:.0f} s' in text
            for model in case['models']:
                h=model['horizons'][slot]
                assert f'Mean error={h["mean_error_m"]:.1f} m' in text
                assert f'R90={h["radius_m"]:.1f} m' in text


def test_bilingual_figures_and_case_table_use_the_bound_diagnostics():
    for language in ('en','zh'):
        source=(PAPER/language/'main.tex').read_text(encoding='utf-8')
        assert '\\label{sec:case-horizons}' in source
        section=source.split('\\label{sec:case-horizons}',1)[1]
        table=section.split('\\label{tab:case-diagnostics}',1)[1].split('\\end{table}',1)[0]
        for case in DATA['cases']:
            label=case['label'] if case['label']!='Zagan' else "\\.{Z}aga\\'{n}"
            for model in case['models']:
                row=f'{label} & {model["subject"]} & {model["weighted_es_m"]:.2f} & {model["fde_m"]:.2f} & {model["original_core_seconds"]:.2f}'
                assert row in table
            for figure in case['figures']:
                assert '../figures/'+figure['pdf'] in section
        assert '90\\%' in section and 'GPX' in section


def test_ledger_matches_images_without_overriding_pending_full_scope():
    ledger=json.loads((PAPER/'claim-ledger.json').read_text(encoding='utf-8'))
    claim=ledger['local_case_horizon_illustrations']
    assert claim['source_sha256']==hashlib.sha256(PATH.read_bytes()).hexdigest()
    assert claim['figure_pairs']==6 and claim['rendered_panels']==24
    assert claim['public_distribution_authorized'] is False
    assert claim['registered_sixteen_table_figure_inventory_replaced'] is False
    assert ledger['human_accepted'] is False and ledger['final_empirical_results_integrated'] is False


@pytest.mark.parametrize('language', ['en', 'zh'])
def test_case_time_table_uses_all24_existing_errors_without_replacing_diagnostics(language):
    text=(PAPER/language/'main.tex').read_text(encoding='utf-8')
    assert text.count(r'\label{tab:case-point-errors}')==1
    table=text.split(r'\label{tab:case-point-errors}',1)[1].split(r'\end{tabular}',1)[0]
    for case in DATA['cases']:
        label=case['label'] if case['label']!='Zagan' else "\\.{Z}aga\\'{n}"
        base, terrain=case['models']
        cells=[f'{a["mean_error_m"]:.1f} / {b["mean_error_m"]:.1f}'
               for a,b in zip(base['horizons'],terrain['horizons'])]
        assert label+' & '+' & '.join(cells)+r'\\' in table
    assert r'e_h=\|\overline{X}_h-y_h\|_2' in text
    section=text.split(r'\label{sec:case-horizons}',1)[1].split(r'\section{',1)[0]
    for en,zh in (("not an average over", "不是参与者均值"),
                  ("not new", "不是新增评分"),
                  ("do not establish the population frequency", "不能确定这种取舍在总体中的频率")):
        assert (en if language=='en' else zh) in section
    assert r'\label{tab:case-diagnostics}' in section


def test_descriptive_case_pattern_is_exactly_the_preserved_three_cases():
    differences=[[b['mean_error_m']-a['mean_error_m']
                  for a,b in zip(c['models'][0]['horizons'],c['models'][1]['horizons'])]
                 for c in DATA['cases']]
    assert [[1 if x>0 else -1 if x<0 else 0 for x in row] for row in differences]==[
        [1,1,1,-1],[1,1,1,-1],[1,-1,-1,-1]]
    assert hashlib.sha256(PATH.read_bytes()).hexdigest()==(
        'bb95e19698632bae6b17c24f5c423e493f599039d14a9982c2a0a82edb0c37c6')


@pytest.mark.parametrize('language',['en','zh'])
def test_all_method_es_is_not_relabelled_as_unretained_point_error(language):
    text=(PAPER/language/'main.tex').read_text(encoding='utf-8')
    for en,zh in (("only the four-target average ADE and last-target FDE", "四目标平均 ADE 与末目标 FDE"),
                  ("ES cannot be converted into them", "ES 也不能转换成它们"),
                  ("not a substitute for all-method accuracy", "不能代替全方法准确性结果")):
        assert (en if language=='en' else zh) in text


def test_case_reading_ledger_does_not_authorize_experiments_or_close_review():
    ledger=json.loads((PAPER/'claim-ledger.json').read_text(encoding='utf-8'))
    entry=ledger['saved_case_point_error_reading_revision']
    assert entry['review_items']==['P1-19'] and entry['existing_point_error_values']==24
    assert entry['source_sha256']==hashlib.sha256(PATH.read_bytes()).hexdigest()
    assert entry['new_fits_forecasts_scores_resampling_or_map_queries']==0
    for name in ('all_method_point_error_profiles_reconstructed',
                 'population_time_tradeoff_or_terrain_effect_established',
                 'original_final_sixteen_figure_inventory_replaced',
                 'independent_saved_output_audit_completed',
                 'public_distribution_authorized','all_review_items_or_paper_complete'):
        assert not entry[name]
