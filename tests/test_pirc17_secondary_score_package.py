# Historical presentation fixture: exact public release 8cbcb114.
# Old monolithic positions are not current six-document acceptance.
# Current source graph, values and layouts: test_pirc17_revision46.py.
"""Bind the actual descriptive package to the original audited result export."""
import csv
import hashlib
import json
from pathlib import Path

import pytest

from scripts import project_pirc17_secondary_scores as p

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'paper/pirc17/secondary-scores-v1'
CONTENT = 'f0cae23999322c49575e2b95d41b4713836666a5d02f0c55af8cc306167e92ac'
FILE = '47b8ec55940d783012c37b1aa7f1640e15628f280e405fdb500fe976f744d3bc'


def actual():
    data = (PACKAGE / 'projection.json').read_bytes()
    assert hashlib.sha256(data).hexdigest() == FILE
    record = json.loads(data)
    assert record['sha256'] == p.digest(record['payload']) == CONTENT
    return record['payload']


def test_original_source_pin_all120_views_and_all_five_failures_are_retained():
    value = actual()
    assert value['source_export_sha256'] == '29cb892f47301365b3d7b9a2871f3f71d85fe297f7720d0c6489648f8a4d0c50'
    assert value['source_export_file_sha256'] == 'f15578e9da655a2e2df6601427724d11c2ee6effe200e78846bddde54c7fc75e'
    assert value['source_audit_sha256'] == '8ff917ad6db55bb3b058b51412ab2e76154ba8bd38c754dd60829db74e25ec67'
    assert value['source_analysis_sha256'] == 'd1d67a3bf4cd08d46f7e73f0178950b047197275f3f32e29a61f3f699fe5febc'
    assert value['source_score_rows'] == 11368
    assert value['configuration_mode_views'] == len(value['records']) == 120
    assert value['time_views'] == 480
    axes = {(r['origin_mode'], r['matrix'], r['configuration']) for r in value['records']}
    assert axes == {(m, x, c) for m in p.MODES for x, c in p.AXES}
    unavailable = [r for r in value['records'] if r['status'] == 'unavailable']
    assert {(r['origin_mode'], r['configuration']) for r in unavailable} == {
        ('causal_prefix', 'all-terrain'), ('causal_prefix', 'lio-river'),
        ('causal_prefix', 'lio-road'), ('known_velocity', 'arm-03/single_gaussian'),
        ('known_velocity', 'arm-06/dt30')}
    assert all(r['means'] is None and r['counts_by_status']['failed'] == 1 for r in unavailable)
    assert all(r['missing_score_rows'] == 0 for r in value['records'])
    assert sum(r['available_score_rows'] for r in value['records']) == 11368


def test_generated_csvs_and_manifest_match_all_committed_bytes_without_subset_selection():
    value = actual()
    manifest = json.loads((PACKAGE / 'manifest.json').read_bytes())
    assert manifest['sha256'] == p.digest(manifest['payload'])
    assert manifest['payload']['projection_sha256'] == CONTENT
    assert len(manifest['payload']['files']) == 5
    for name, binding in manifest['payload']['files'].items():
        data = (PACKAGE / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == binding['sha256']
        assert len(data) == binding['bytes']
    assert value['projection_code_sha256'] == hashlib.sha256(
        (ROOT / 'scripts/project_pirc17_secondary_scores.py').read_bytes()).hexdigest()
    for name, data in p.tables(value).items():
        assert (PACKAGE / name).read_bytes() == data
        with (PACKAGE / name).open(encoding='utf-8', newline='') as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == (120 if name.startswith('endpoint') else 480)
        bad = [r for r in rows if r['status'] == 'unavailable']
        assert len(bad) == (5 if name.startswith('endpoint') else 20)
        metric = 'fde_m' if name.startswith('endpoint') else 'crps_east_m'
        assert all(r[metric] == '' for r in bad)


def test_actual_full_and_dt300_diagnostics_do_not_confuse_fde_or_quantile_mean():
    value = actual()
    rows = {r['configuration']: r['means'] for r in value['records'] if r['origin_mode'] == 'causal_prefix'}
    full, coarse = rows['arm-01/full'], rows['arm-06/dt300']
    assert full['fde_m'] == pytest.approx(1326.0918029570769, abs=1e-9)
    assert full['mean_within_forecast_endpoint_quantiles_m']['0.95'] == pytest.approx(2346.622655693915)
    assert coarse['mean_within_forecast_endpoint_quantiles_m']['0.95'] > full['mean_within_forecast_endpoint_quantiles_m']['0.95']
    assert coarse['fde_m'] > full['fde_m']
    for name in ('crps_east_m', 'crps_north_m'):
        assert coarse['by_time'][3][name] < full['by_time'][3][name]
    inertial = rows['all']
    assert set(inertial['mean_within_forecast_endpoint_quantiles_m'].values()) == {inertial['fde_m']}
    assert full['by_time'][3]['actual_elapsed_seconds_range'] == [1785.0, 1814.0]


@pytest.mark.parametrize('language', ['en', 'zh'])
def test_real_bilingual_fragment_is_generated_exactly_and_inserted_in_main(language):
    expected = p.manuscript_fragment(actual(), language)
    assert (PACKAGE / language / 'secondary-score-diagnostics.tex').read_bytes() == expected
    assert (ROOT / 'paper/pirc17' / language / 'secondary-score-diagnostics.tex').read_bytes() == expected
    text = (ROOT / 'paper/pirc17' / language / "historical-main-v1.tex").read_text(encoding='utf-8')
    assert text.count(r'\label{sec:secondary-score-diagnostics}') == 1
    assert text.count(r'\input{secondary-score-diagnostics.tex}') == 1
    section = text.split(r'\label{sec:secondary-score-diagnostics}', 1)[1].split(r'\section{', 1)[0]
    for token in ('687.11', '524.07', '737.72', '535.72', '1335.73', '1326.09',
                  '2827.57', '2346.62', '120', '480', '11368', '29cb892f', '8ff917ad', 'd1d67a3b'):
        assert token in section
    assert ('not a promise' if language == 'en' else '不是承诺') in section
    assert ('not radii' if language == 'en' else '也不是以预测均值为中心的圆半径') in section


def test_package_is_descriptive_not_acceptance_and_contains_no_private_point_data():
    value = actual()
    for field in ('new_fits', 'new_forecasts', 'new_scores', 'new_resampling'):
        assert value[field] == 0
    for field in ('hypothesis_tests_performed', 'physical_clock_certified', 'independent_participants_certified',
                  'numerically_qualified', 'scientific_claim_authorized', 'human_accepted'):
        assert value[field] is False
    text = json.dumps(value)
    for field in ('origin_id', 'independent_block_id', 'positions_m', 'coordinates', 'sample_id', 'hostname', 'artifact_path'):
        assert field not in text
    attrs = (ROOT / '.gitattributes').read_text()
    for rule in ('paper/pirc17/secondary-scores-v1/** -text',
                 'paper/pirc17/*/secondary-score-diagnostics.tex -text',
                 'scripts/project_pirc17_secondary_scores.py -text'):
        assert rule in attrs
