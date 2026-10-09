# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Document checks only; these do not certify literature claims or run models."""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / 'paper/pirc17'
LEDGER = json.loads((ROOT / 'claim-ledger.json').read_text(encoding='utf-8'))


def related(language):
    tex = (ROOT / language / "historical-main-v1.tex").read_text(encoding='utf-8')
    section = tex.split(r'\label{sec:related-work}', 1)[1].split(r'\section{', 1)[0]
    return tex, section


@pytest.mark.parametrize('language', ['en', 'zh'])
def test_three_themes_and_closest_precedents(language):
    tex, section = related(language)
    assert tex.count(r'\label{sec:related-work}') == 1
    assert section.count(r'\subsection{') == 3
    keys = set()
    for group in re.findall(r'\\cite\{([^}]+)\}', section):
        keys.update(group.split(','))
    assert {'johnson2008', 'ghahramani2000', 'avgar2016',
            'avgar2017correction', 'kidger2021', 'gao2024',
            'gupta2018', 'salzmann2020', 'gneiting2007',
            'gneiting2008', 'kloeden1992', 'holm1979',
            'davison1997', 'nichol2018'} <= keys


@pytest.mark.parametrize('language', ['en', 'zh'])
def test_positioning_not_external_benchmark_or_optimality(language):
    _, section = related(language)
    phrases = {
        'en': ['not evidence that linear models', 'are optimal',
               'saved fit parameters', 'not executed baselines',
               'descriptive same-population comparison',
               'not an independently audited', 'superiority claim',
               'not its likelihood or coefficient formulas',
               'not a new neural architecture'],
        'zh': ['不是线性模型最优的证据', '保存的拟合参数',
               '没有作为本次执行基线', '简单惯性参考已有同人群描述性对比',
               '不是独立核验后的优越性结论',
               '不使用其似然或系数公式', '不是提出新的神经网络架构'],
    }
    for phrase in phrases[language]:
        assert phrase in section
    assert 'MAML' not in section


@pytest.mark.parametrize('language', ['en', 'zh'])
def test_publication_metadata_and_corrigendum(language):
    tex, _ = related(language)
    bib = tex.split(r'\begin{thebibliography}{99}', 1)[1]
    for value in ['89(5), 1208--1215', '12(4), 831--864',
                  '7(5), 619--630', '8(9), 1168',
                  '2255--2264', '12363, 683--700',
                  '10.1890/07-1032.1', '10.1162/089976600300015619',
                  '10.1111/2041-210X.12528', '10.1111/2041-210X.12725',
                  '10.1007/978-3-030-58523-5_40']:
        assert value in bib
    assert r'\emph{arXiv:1803.10892}' not in bib
    assert r'\emph{arXiv:2001.03093}' not in bib


def test_shared_entries_match_between_languages():
    en, _ = related('en')
    zh, _ = related('zh')
    for key in ['johnson2008', 'ghahramani2000', 'avgar2016',
                'avgar2017correction', 'gupta2018', 'salzmann2020']:
        pattern = r'\\bibitem\{' + key + r'\}(.*?)(?=\\bibitem|\\end\{thebibliography\})'
        en_entry = re.search(pattern, en, re.S).group(1)
        zh_entry = re.search(pattern, zh, re.S).group(1)
        assert ' '.join(en_entry.split()) == ' '.join(zh_entry.split())


def test_ledger_keeps_science_and_final_acceptance_unclaimed():
    revision = LEDGER['related_work_revision']
    assert revision['review_items'] == ['P1-26', 'P2-03', 'P2-10']
    assert len(revision['themes']) == 3
    assert revision['issa_corrigendum_checked']
    assert revision['published_social_gan_and_trajectron_bibliography_corrected']
    assert not revision['issa_likelihood_or_coefficient_formulas_used']
    assert not revision['external_models_executed_as_baselines']
    assert not revision['original_inertial_reference_complete']
    assert revision['new_fits_forecasts_or_experiments'] == 0
    assert not revision['all_data_source_references_and_licences_resolved']
    assert not revision['all_review_items_or_paper_complete']
    assert not LEDGER['final_empirical_results_integrated']
    assert not LEDGER['human_accepted']
    sources = {r['citation']: r for r in LEDGER['related_work_sources']}
    assert 'esajournals.onlinelibrary.wiley.com' in sources['johnson2008']['primary_url']
    assert 'cs.toronto.edu/~hinton' in sources['ghahramani2000']['primary_url']
    assert '12528' in sources['avgar2016']['doi']
    assert '12725' in sources['avgar2017correction']['doi']
    assert 'openaccess.thecvf.com' in sources['gupta2018']['primary_url']
    assert 'link.springer.com' in sources['salzmann2020']['primary_url']
