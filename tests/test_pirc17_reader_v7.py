"""Explicit user C1-C5 clarity contract; no new scientific calculations."""
import json
import subprocess
from pathlib import Path
import pytest

PAPER=Path(__file__).resolve().parents[1]/'paper/pirc17'


@pytest.mark.parametrize('language',['en','zh'])
def test_conclusions_directly_answer_each_user_point(language):
    body=(PAPER/language/'main.tex').read_text(encoding='utf-8')
    conclusion=body.split(r'\section{Conclusion}' if language=='en' else r'\section{结论}',1)[1]
    assert all(v in conclusion for v in ('CV','HSM-SDE','RDM-SDE','120','300','60','46.52','26.98','39.00','1.64','5.96','RQ1','RQ2'))
    assert 'original training/adaptation procedure' in conclusion if language=='en' else '相对原训练程序' in conclusion
    assert 'no structural winner' not in conclusion and '结构赢家' not in conclusion
    assert 'Inference qualification, not an additional finding' in conclusion if language=='en' else '推断资格，不是另一项研究发现' in conclusion
    assert '1、5分钟CV更好；15、30分钟HSM-SDE更好' in conclusion if language=='zh' else 'CV is better at 1 and 5 minutes;' in conclusion


@pytest.mark.parametrize('language',['en','zh'])
def test_region_metrics_are_explained_in_plain_language(language):
    body=(PAPER/language/'main.tex').read_text(encoding='utf-8')
    assert r'\begin{description}' in body
    assert all(v in body for v in ('512',r'90\%',r'46.52\%'))
    expected=('model-internal proportion','Empirical coverage','entire city','inaccurate centre') if language=='en' else ('模型内部的比例','经验覆盖率','整个城市','圆心偏了')
    assert all(v in body for v in expected)


@pytest.mark.parametrize('language',['en','zh'])
def test_explicit_terrain_findings_and_causal_hypothesis_are_distinct(language):
    body=(PAPER/language/'main.tex').read_text(encoding='utf-8')
    terrain=(PAPER/language/'reader-v6-terrain-results.tex').read_text(encoding='utf-8')
    assert all(v in terrain for v in ('43','42.96','19.87','42.51','57.27','1.64','5.96'))
    assert 'does not identify or validate a specific cause' in body if language=='en' else '未识别或验证具体原因' in body
    assert 'land cover alone lowers average ES' in terrain if language=='en' else '仅加入地表覆盖后，平均ES降低1.64米' in terrain


def test_claim_record_covers_all_points_without_changing_evidence():
    d=json.loads((PAPER/'reader-v7-claims.json').read_text())
    assert [v['id'] for v in d['claims']]==['C1','C2','C3a','C3b','C4','C5.1','C5.2','C5.3','C5.4']
    assert not d['figures_and_numeric_evidence_changed']
    assert d['terrain_interpretation']['status']=='interpretation/hypothesis, not an established cause'


def test_terrain_numeric_content_and_binary_figures_are_unchanged():
    root=PAPER.parents[1]
    paths=subprocess.check_output(['git','ls-tree','-r','--name-only','b31d7c4','--',
        'paper/pirc17/terrain-description-v1','paper/pirc17/figures/terrain-description-v1'],cwd=root,text=True).splitlines()
    assert len(paths)==7
    for path in paths:
        current=(root/path).read_bytes()
        original=subprocess.check_output(['git','show','b31d7c4:'+path],cwd=root)
        # Git's Windows checkout may translate text; numbers and all other
        # content remain exact, while PDF/PNG are byte-identical.
        if Path(path).suffix in {'.json','.csv','.tex'}:
            current=current.replace(b'\r\n',b'\n')
            original=original.replace(b'\r\n',b'\n')
        assert current==original
