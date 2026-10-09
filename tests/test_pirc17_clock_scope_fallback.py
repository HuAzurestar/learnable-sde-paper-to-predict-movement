# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Retained-clock wording/acceptance-branch checks, not source certification."""
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT/'paper/pirc17'
BASE = 'aff75cc52b6f9f177416550b03ef5459d332cb21'
REPLACEMENTS = {
    'en': [
        ('covariance \\(R\\) with a fixed physical increment covariance \\(Q=R\\tau\\), where',
         'covariance \\(R\\) with fixed increment covariance \\(Q=R\\tau\\) in the retained time coordinate, where'),
        ('substep. Solar elevation is recomputed from predicted geography and the\nexplicit UTC clock using the NOAA fractional-year approximation\\cite{noaa};\nit is geometric elevation, not a weather measurement or a refraction model.',
         'substep. Solar elevation is recomputed from predicted geography and the\nretained clock using its model UTC interpretation and the NOAA fractional-year\napproximation\\cite{noaa}. Acquisition UTC is not independently certified\n(Section~\\ref{sec:clock-and-map-provenance}); this is geometric elevation,\nnot a weather measurement or a refraction model.')
    ],
    'zh': [
        ('方法噪声使用速度率残差协方差 \\(R\\)，物理增量协方差为 \\(Q=R\\tau\\)，',
         '方法噪声使用速度率残差协方差 \\(R\\)，保留时间坐标下的增量协方差为 \\(Q=R\\tau\\)，'),
        ('重抽模式，不在每个积分子步重抽。太阳高度角由预测位置和明确 UTC 时钟按 NOAA\nfractional-year 近似重算\\cite{noaa}，是几何高度角，不是天气测量或折射模型。',
         '重抽模式，不在每个积分子步重抽。太阳高度角由预测位置与保留时钟按模型的 UTC 解释及 NOAA\nfractional-year 近似重算\\cite{noaa}；采集时钟的 UTC 来源未获独立认证\n（第~\\ref{sec:clock-and-map-provenance}~节），这里是几何高度角，不是天气测量或折射模型。')
    ]
}


@pytest.mark.parametrize('language', ['en', 'zh'])
def test_model_clock_passages_do_not_imply_source_clock_certification(language):
    before = subprocess.check_output(['git', 'show', BASE+':paper/pirc17/'+language+'/main.tex'],
        cwd=ROOT).decode('utf-8').replace('\r\n', '\n')
    after = (PAPER/language/"historical-main-v1.tex").read_text(encoding='utf-8')
    for old, new in REPLACEMENTS[language]:
        assert before.count(old) == 1
        assert old not in after
        assert after.count(new) == 1


def test_fallback_preserves_all_original_evidence_and_does_not_certify_clock():
    ledger = json.loads((PAPER/'claim-ledger.json').read_text(encoding='utf-8'))
    original = json.loads(subprocess.check_output(['git', 'show', BASE+':paper/pirc17/claim-ledger.json'],
        cwd=ROOT).decode('utf-8'))
    assert original == {key: ledger[key] for key in original}
    revision = ledger['clock_scope_fallback_revision']
    assert revision['source_base_commit'] == BASE
    assert revision['review_items'] == ['P0-04']
    assert revision['model_clock_interpretation_is_not_source_UTC_certification']
    for field in ('original_review_acceptance_criteria_changed',
                  'original_clock_provenance_evidence_or_source_ticks_changed',
                  'source_UTC_sensor_clock_physical_horizon_or_daylight_effect_certified',
                  'independent_saved_output_audit_completed',
                  'human_or_final_review_acceptance_obtained',
                  'final_paper_or_all_review_items_complete'):
        assert revision[field] is False
    assert revision['new_fits_forecasts_scores_resampling_or_map_queries'] == 0
    assert hashlib.sha256((PAPER/'clock-description-v1.json').read_bytes()).hexdigest() == revision['original_clock_projection_sha256']
    clock = json.loads((PAPER/'clock-description-v1.json').read_text(encoding='utf-8'))
    assert len(clock['condition_clock_footers']) == 3
    assert not clock['scope']['full_cohort_footer_audit']
    assert not clock['scope']['utc_or_sensor_clock_source_certified']
    assert not clock['scope']['physical_horizon_or_daylight_effect_certified']
    assert not ledger['final_empirical_results_integrated'] and not ledger['human_accepted']
