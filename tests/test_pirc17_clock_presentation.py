"""Clock evidence and document checks only; no fitting or forecasting."""
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / 'paper/pirc17'
PATH = ROOT / 'clock-description-v1.json'
EVIDENCE = json.loads(PATH.read_text(encoding='utf-8'))


def test_bound_clock_projection_and_limited_footer_scope():
    ledger = json.loads((ROOT / 'claim-ledger.json').read_text(encoding='utf-8'))['clock_provenance_description']
    assert hashlib.sha256(PATH.read_bytes()).hexdigest() == ledger['projection_sha256']
    assert len(EVIDENCE['source_sha256']) == 5
    rows = EVIDENCE['condition_clock_footers']
    assert len(rows) == 3
    assert [r['selection_ordinal'] for r in rows] == [0, 1, 2]
    assert [r['physical_parquet_rows'] for r in rows] == [951, 550, 794]
    assert all(r['clock_type'] == 'timestamp[ns]' and r['clock_timezone'] is None for r in rows)
    assert not EVIDENCE['scope']['full_cohort_footer_audit']
    assert not ledger['source_UTC_or_sensor_clock_provenance_certified']


def test_original_fits_and_source_units_not_reinterpreted():
    constants = EVIDENCE['solar_constants']
    assert constants['NANOSECONDS'] == 1_000_000_000
    assert constants['SOLAR_POLICY'] == 'noaa-fractional-year-geometric-utc-subsecond-v1'
    assert len(EVIDENCE['saved_method_clock_policies']) == 16
    assert all(r['condition_names'] == ['solar_elev'] and r['solar_policy'] == constants['SOLAR_POLICY']
               for r in EVIDENCE['saved_method_clock_policies'])
    assert EVIDENCE['release_alignment_semantics']['exact_time_field'] == 'alignment.jsonl.absolute_epoch_ns'
    assert not EVIDENCE['release_segment_semantics']['original_gpx_tracksegment']


def test_reported_release_reconciliation_is_not_fresh_selected_target_audit():
    counts = EVIDENCE['reported_release_reconciliation']
    assert counts['source_condition_points'] == 19647139
    assert counts['aligned_refined_points'] == 14738300
    assert counts['total_condition_points_not_aligned'] == 4908839
    assert counts['duplicate_timestamp_intervals'] == 37957
    assert counts['segments_with_duplicate_timestamps'] == 1387
    assert counts['backward_timestamp_intervals_causing_split'] == 166
    assert counts['long_gap_timestamp_intervals_causing_split'] == 10052
    for field in ('coordinate_speed_or_timestamp_values_decoded', 'reported_reconciliation_recomputed_from_points',
                  'utc_or_sensor_clock_source_certified', 'physical_horizon_or_daylight_effect_certified',
                  'stored_historical_solar_generator_parity_certified', 'independent_saved_forecast_audit'):
        assert not EVIDENCE['scope'][field]
    for field in ('new_fits', 'new_forecasts', 'new_particle_scores'):
        assert EVIDENCE['scope'][field] == 0


@pytest.mark.parametrize('language', ['en', 'zh'])
def test_bilingual_clock_table_formula_and_reconciliation(language):
    tex = (ROOT / language / 'main.tex').read_text(encoding='utf-8')
    assert tex.count(r'\label{tab:clock-use}') == 1
    assert tex.count(r'\label{eq:solar-condition}') == 1
    assert 'clock-description-v1.json' in tex
    for text in ('37,957', '1,387', '10,052', '4,908,839', r'\operatorname{round}(10^9s)',
                 '0.040849', '0.399912', r'\cos\phi\cos\delta\cos H_\odot'):
        assert text in tex
    if language == 'en':
        assert 'no\ntimezone annotation' in tex
        assert 'does not establish\nthat convention' in tex
        assert 'do not establish a physically\nvalidated daylight' in tex
    else:
        assert '没有时区标注' in tex
        assert '页脚不能证明该约定' in tex
        assert '不证明经物理验证的日光' in tex
