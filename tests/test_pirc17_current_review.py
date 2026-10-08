"""Current author response and prose consistency, not peer-review acceptance."""
from collections import Counter
import json
from pathlib import Path
import re
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper/pirc17'
BASE = '919488cbf3b1d83485c9f6126ffec4fe564eaa6c'


def test_current_author_response_accounts_for_all_original_ids_without_acceptance():
    text = (PAPER / 'review-current-v2.md').read_text(encoding='utf-8')
    rows = re.findall(r'^\| (P[012]-\d{2}) \| ([^|]+) \| (.+) \|$', text, re.M)
    expected = {f'P{p}-{n:02d}' for p, count in ((0, 6), (1, 26), (2, 10))
                for n in range(1, count + 1)}
    assert len(rows) == 42 and {r[0] for r in rows} == expected
    assert Counter(r[1] for r in rows) == {'已补到工作稿': 26, '保留实质证据缺口': 12,
                                          '按限定范围说明': 3, '待真实发表许可': 1}
    assert all(len(r[2]) > 30 for r in rows)
    for token in ('接受项仍为 **0**', '不是论文完成百分比', '457688e8ba81c88b',
                  '不自动新增模型', '不能用成功子集或编造数据', '不关闭REVIEW／ACCEPT／GOAL'):
        assert token in text
    assert 'review-response-v1.json' in text
    registry = json.loads((PAPER / 'review-response-v1.json').read_text(encoding='utf-8'))
    assert registry['accepted_items'] == 0
    assert not any(r['final_review_accepted'] for r in registry['items'])


def test_unavailable_source_evidence_is_not_promoted_by_completed_audit():
    text = (PAPER / 'review-current-v2.md').read_text(encoding='utf-8')
    for identifier in ('P0-03', 'P1-02', 'P1-04', 'P1-05', 'P1-08', 'P1-13',
                       'P1-15', 'P1-18', 'P1-22', 'P1-24', 'P2-02', 'P2-10'):
        assert f'| {identifier} | 保留实质证据缺口 |' in text
    assert '| P1-25 | 待真实发表许可 |' in text
    for token in ('14个有限算法', '全部分辨率不变判断为证据不足', '六份',
                  '物理UTC', 'provider冷不称OS冷', '五条失败'):
        assert token in text


@pytest.mark.parametrize('language', ['en', 'zh'])
def test_current_prose_does_not_still_wait_for_completed_output_audit(language):
    text = (PAPER / language / 'main.tex').read_text(encoding='utf-8')
    # Original historical captions are intentionally preserved and explicitly marked.
    prose = re.sub(r'\\caption\{.*?(?=\\label\{|\n)', '', text, flags=re.S)
    patterns = (r'pending independent saved-output audit', r'output audit remains pending',
                r'output replay is pending', r'saved-output audit is still pending',
                r'independent saved-output replay is\s+still pending',
                r'whole saved-output verification\s+remains pending',
                r'pending saved-forecast audit') if language == 'en' else (
                r'尚待完成的独立保存输出审计', r'独立保存输出审计仍未完成',
                r'独立保存输出复算仍未完成', r'原独立输出复算仍待完成',
                r'完整保存输出复核仍未完成', r'尚待完成的保存预测审计')
    assert not any(re.search(p, prose) for p in patterns)
    for token in ('qualification-v1/', 'replay-input-v1/', 'final-results-v1/', '112', '165', '14'):
        assert token in text
    assert ('global numerical convergence' if language == 'en' else '全局数值收敛') in text
    assert ('human acceptance' if language == 'en' else '真实人工验收') in text


@pytest.mark.parametrize('language', ['en', 'zh'])
def test_status_revision_keeps_every_scientific_block_and_bibliography_exact(language):
    old = subprocess.check_output(['git', 'show', f'{BASE}:paper/pirc17/{language}/main.tex'],
                                  cwd=ROOT).decode('utf-8').replace('\r\n', '\n')
    new = (PAPER / language / 'main.tex').read_text(encoding='utf-8')
    for kind in ('table', 'longtable', 'figure', 'equation', 'align'):
        pattern = r'\\begin\{' + kind + r'\}.*?\\end\{' + kind + r'\}'
        assert re.findall(pattern, old, re.S) == re.findall(pattern, new, re.S), kind
    assert re.findall(r'\\\[.*?\\\]', old, re.S) == re.findall(r'\\\[.*?\\\]', new, re.S)
    assert old.split(r'\begin{thebibliography}', 1)[1] == new.split(r'\begin{thebibliography}', 1)[1]
    assert re.findall(r'\\label\{([^}]+)\}', old) == re.findall(r'\\label\{([^}]+)\}', new)
