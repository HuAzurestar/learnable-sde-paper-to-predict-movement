# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Check document claims against existing stage projections; no new analyses."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / 'paper/pirc17'
STAGE = json.loads((ROOT/'preliminary-method-statistics-v1.json').read_text(encoding='utf-8'))
LEDGER = json.loads((ROOT/'claim-ledger.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('language', ['en','zh'])
def test_scientific_questions_and_temporal_not_effect_causality(language):
    tex = (ROOT/language/"historical-main-v1.tex").read_text(encoding='utf-8')
    title = tex.split(r'\title{',1)[1].split(r'\author',1)[0]
    assert 'Causal Stochastic' not in title and '因果初始化' not in title
    assert tex.count(r'\label{sec:research-questions}') == 1
    intro = tex.split(r'\section{Introduction}' if language == 'en' else r'\section{引言}',1)[1]
    intro = intro.split(r'\section{',1)[0]
    assert 'RQ1' in intro and 'RQ2' in intro
    assert 'PIRC' not in intro and 'NEX' not in intro
    assert ('causal effect of terrain' if language == 'en' else '地形对行为的因果效应') in intro
    assert ('not treated as model novelty' if language == 'en' else '不作为模型创新') in intro


@pytest.mark.parametrize('language', ['en','zh'])
def test_current_conclusion_uses_existing_results_not_future_todo(language):
    tex = (ROOT/language/"historical-main-v1.tex").read_text(encoding='utf-8')
    conclusion = tex.split(r'\section{Conclusion}' if language == 'en' else r'\section{结论}',1)[1].split(r'\appendix',1)[0]
    configs = {r['configuration']: r for r in STAGE['configs']}
    full, dt = configs['arm-01/full'], configs['arm-06/dt300']
    for number in (full['weighted_es_m'], full['fde_m'], dt['fde_m'],
                   100*full['coverage_90_by_time'][-1], 100*dt['coverage_90_by_time'][-1]):
        assert f'{number:.2f}' in conclusion
    contrasts = {r['candidate']: r for r in STAGE['comparisons']}
    assert '32.95' in conclusion
    assert f"{contrasts['arm-04/gmm_kernel']['delta_estimate_m']:.2f}" in conclusion
    assert f"{-contrasts['arm-06/dt300']['delta_estimate_m']:.2f}" in conclusion
    assert 'RQ1' in conclusion and 'RQ2' in conclusion
    assert ('unavailable inferential answer' if language == 'en' else '推断答案不可用') in conclusion
    assert 'The final conclusion will state' not in conclusion
    assert '最终结论将从完整复核卡片撰写' not in conclusion
    assert not STAGE['independent_raw_output_audit_completed']
    assert not LEDGER['final_empirical_results_integrated']
    assert not LEDGER['human_accepted']


@pytest.mark.parametrize('language', ['en','zh'])
def test_unavailable_not_merely_waiting_and_execution_details_in_appendix(language):
    tex = (ROOT/language/"historical-main-v1.tex").read_text(encoding='utf-8')
    opening = tex.split(r'\begin{quote}',1)[1].split(r'\end{quote}',1)[0]
    assert ('Reported:' if language == 'en' else '已报告：') in opening
    assert ('Unavailable under' if language == 'en' else '不可用：') in opening
    assert ('Pending:' if language == 'en' else '未完成：') in opening
    assert r'\ref{tab:failure-family-dispositions}' in opening
    body, appendix = tex.split(r'\appendix',1)
    assert r'\ref{sec:execution-reconstruction}' in body
    assert r'\label{sec:execution-reconstruction}' not in body
    assert appendix.count(r'\label{sec:execution-reconstruction}') == 1
    assert '11368' in appendix and '58' in appendix
    assert ('Reproduction has three distinct scopes' if language == 'en' else '复现分为三个不同范围') in appendix
    assert ('Reproduction has three distinct scopes' if language == 'en' else '复现分为三个不同范围') not in body


def test_reframing_not_claimed_full_review_or_new_model():
    revision = LEDGER['scientific_narrative_revision']
    assert revision['review_items'] == ['P1-01','P2-01','P2-02','P2-09']
    assert not revision['new_neural_architecture_estimator_or_convergence_theorem_claimed']
    assert revision['new_forecasts_fits_or_inference_tests'] == 0
    assert not revision['final_paper_or_all_review_items_complete']


@pytest.mark.parametrize('language', ['en', 'zh'])
def test_opening_closing_revision_changes_only_summary_prose(language):
    import re
    import subprocess
    base = '0ce0a107b8695635fb45a06205ed17ad790145c1'
    before = subprocess.check_output([
        'git', 'show', base + ':paper/pirc17/' + language + '/main.tex'
    ], cwd=ROOT.parents[1]).decode('utf-8').replace('\r\n', '\n')
    # This is a historical claim about the delivered opening/closing unit,
    # not a prohibition on later reviewed body revisions.
    after = subprocess.check_output([
        'git', 'show', '0976683b342e91e15a0f528476d7e1003eb70b34:paper/pirc17/' + language + '/main.tex'
    ], cwd=ROOT.parents[1]).decode('utf-8').replace('\r\n', '\n')
    heading = r'\section{Conclusion}' if language == 'en' else r'\section{结论}'
    def outside_summary(text):
        text = re.sub(r'(\\begin\{abstract\}).*?(\\end\{abstract\})',
                      r'\1<summary>\2', text, flags=re.S)
        start = text.index(heading) + len(heading)
        end = text.index(r'\appendix', start)
        return text[:start] + '<conclusion>\n' + text[end:]
    assert outside_summary(before) == outside_summary(after)
    abstract = after.split(r'\begin{abstract}', 1)[1].split(r'\end{abstract}', 1)[0]
    old_abstract = before.split(r'\begin{abstract}', 1)[1].split(r'\end{abstract}', 1)[0]
    if language == 'en':
        assert len(abstract.split()) < len(old_abstract.split())
        assert 'ES; lower is better' in abstract
        assert 'nominal\nrecorded-clock horizons' in abstract
    else:
        assert len(abstract) < len(old_abstract)
        assert 'ES，越低越好' in abstract
        assert '保留记录时钟' in abstract


@pytest.mark.parametrize('language', ['en', 'zh'])
def test_three_conclusion_topics_do_not_hide_unavailable_or_qualification_scope(language):
    tex = (ROOT/language/"historical-main-v1.tex").read_text(encoding='utf-8')
    heading = r'\section{Conclusion}' if language == 'en' else r'\section{结论}'
    conclusion = tex.split(heading, 1)[1].split(r'\appendix', 1)[0]
    assert conclusion.count(r'\paragraph{') == 3
    for en, zh in [('Method components:', '方法组件：'),
                   ('Predictive uncertainty:', '预测不确定性：'),
                   ('Terrain information:', '地形信息：'),
                   ('not a zero effect', '不等于零效应'),
                   ('working draft', '工作稿')]:
        assert (en if language == 'en' else zh) in conclusion
    for value in ('477.85', '1326.09', '32.95', '-2.83', '23.40',
                  '1335.73', '46.52', '64.35', '21.74', '79.13'):
        assert value in conclusion


def test_summary_reorganization_does_not_close_final_results_or_original_review():
    import subprocess
    revision = LEDGER['opening_closing_reader_synthesis_revision']
    assert revision['source_base_commit'] == '0ce0a107b8695635fb45a06205ed17ad790145c1'
    assert revision['review_items'] == ['P2-02', 'P2-09']
    assert revision['revised_prose_only'] == ['abstract', 'conclusion']
    assert revision['new_fits_forecasts_scores_resampling_or_map_queries'] == 0
    for key in ('original_protocol_selection_parameters_or_scientific_values_changed',
                'independent_saved_output_audit_completed',
                'full_manuscript_reader_or_human_acceptance_obtained',
                'final_paper_or_all_review_items_complete'):
        assert revision[key] is False
    before = json.loads(subprocess.check_output([
        'git', 'show', revision['source_base_commit'] + ':paper/pirc17/claim-ledger.json'
    ], cwd=ROOT.parents[1]).decode('utf-8'))
    assert before == {key: LEDGER[key] for key in before}
    assert not LEDGER['final_empirical_results_integrated'] and not LEDGER['human_accepted']


@pytest.mark.parametrize('language', ['en', 'zh'])
def test_saved_all28_horizon_limits_reach_abstract_discussion_and_conclusion(language):
    """Check reporting of existing means; not a new empirical test."""
    configs = {row['configuration']: row for row in STAGE['configs']}
    assert len(configs) == 28
    coverage = [100 * row['coverage_90_by_time'][-1] for row in configs.values()]
    assert all(value < 90 for value in coverage)
    endpoints = [f'{min(coverage):.2f}', f'{max(coverage):.2f}']
    full = configs['arm-01/full']['es_by_time_m']
    mixture = configs['arm-04/gmm_kernel']['es_by_time_m']
    assert mixture[1] < full[1] and mixture[2] < full[2] and mixture[3] > full[3]
    tex = (ROOT/language/"historical-main-v1.tex").read_text(encoding='utf-8')
    abstract = tex.split(r'\begin{abstract}', 1)[1].split(r'\end{abstract}', 1)[0]
    discussion_heading = r'\section{Discussion and limitations}' if language == 'en' else r'\section{讨论与局限}'
    conclusion_heading = r'\section{Conclusion}' if language == 'en' else r'\section{结论}'
    discussion = tex.split(discussion_heading, 1)[1].split(conclusion_heading, 1)[0]
    conclusion = tex.split(conclusion_heading, 1)[1].split(r'\appendix', 1)[0]
    for section in (abstract, discussion, conclusion):
        assert all(value in section for value in endpoints)
        assert '28' in section and '90' in section
        assert ('thirty' if language == 'en' else '30') in section
    for value in (*full[1:], *mixture[1:]):
        assert f'{value:.2f}' in discussion
    assert r'\ref{tab:all-method-horizons}' in discussion
    assert ('not a population interval' if language == 'en' else '不是人群区间') in discussion
    assert ('limited to the previously illustrated' if language == 'en' else '仍仅绑定此前展示') in discussion
    assert ('unavailable inferential answer' if language == 'en' else '推断答案不可用') in conclusion
    assert ('working draft' if language == 'en' else '工作稿') in conclusion


def test_horizon_synthesis_preserves_original_evidence_and_nonacceptance():
    import hashlib
    revision = LEDGER['horizon_scientific_synthesis_revision']
    assert revision['source_base_commit'] == '54ead9cb08125b7f8cbf0f397afbea6bf4c84ca7'
    assert revision['review_items'] == ['P1-19', 'P1-20', 'P2-09']
    saved = ROOT/'method-horizon-description-v1.json'
    assert hashlib.sha256(saved.read_bytes()).hexdigest() == revision['original_horizon_projection_sha256']
    assert revision['configuration_mean_range_is_not_population_interval_or_new_model_test']
    assert revision['joint_area_block_diagnostics_remain_three_model_scope']
    assert revision['new_fits_forecasts_scores_resampling_or_map_queries'] == 0
    assert not revision['independent_saved_output_audit_completed']
    assert not revision['final_paper_or_all_review_items_complete']
