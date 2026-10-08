"""Saved aggregate metadata and manuscript tests; no simulation or fitting."""
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / 'paper/pirc17'
PATH = ROOT / 'partition-description-v1.json'
EVIDENCE = json.loads(PATH.read_text(encoding='utf-8'))


def test_projection_binding_and_complete_original_identity_population():
    ledger = json.loads((ROOT / 'claim-ledger.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(PATH.read_bytes()).hexdigest() == ledger['recording_partition_description']['projection_sha256']
    rows = EVIDENCE['release_counts']
    assert sum(row['assigned_files'] for row in rows.values()) == 7618
    assert sum(row['assigned_recording_hash_blocks'] for row in rows.values()) == 7449
    assert sum(row['midpoint_windows'] for row in rows.values()) == 72046
    assert sum(row['released_refined_segments'] for row in rows.values()) == 75261
    assert rows['final_eval']['sampled_recording_hash_blocks'] == 1094
    assert EVIDENCE['sample_identity_partition_matches_original_protocol']
    for field in ('release_intersections', 'assignment_intersections', 'global_development_role_intersections'):
        assert all(n == 0 for values in EVIDENCE[field].values() for n in values.values())


def test_full_release_counts_not_actual_task_fit_counts():
    rows = EVIDENCE['global_development_roles']
    assert rows['train']['independent_block_id'] == 4201
    assert rows['adapt']['independent_block_id'] == 1050
    assert rows['train']['segment_id'] == 39272
    assert rows['adapt']['segment_id'] == 10573
    chosen = EVIDENCE['selected_method_roles']
    assert [(chosen[role]['windows'], chosen[role]['recording_hash_blocks'])
            for role in ('train', 'adapt', 'validation')] == [(328, 259), (76, 62), (81, 62)]
    assert not EVIDENCE['scope']['global_role_counts_are_task_qualified_fit_population']


def test_historical_exposure_and_independence_limits_not_erased():
    history = EVIDENCE['historical_exposure']
    assert history['prior_final_eval_exposed']
    assert history['historical_release_final_eval_windows'] == 12370
    assert history['separate_historical_geolife_final_eval_windows'] == 17038
    assert not history['geolife_used_by_this_protocol']
    assert not history['forced_exploratory_downgrade']
    assert not history['new_untouched_holdout_required']
    assert EVIDENCE['legacy_directory_split_report']['independent_blocks_crossing_legacy_splits'] == 74
    for field in ('raw_coordinate_speed_or_clock_values_read', 'raw_recording_hashes_recomputed',
                  'source_point_alignment_rows_reread', 'participant_identifiers_available',
                  'participant_or_near_route_independence_established',
                  'physical_timestamp_provenance_established', 'independent_saved_forecast_audit'):
        assert not EVIDENCE['scope'][field]
    for field in ('new_fits', 'new_forecasts', 'new_particle_scores'):
        assert EVIDENCE['scope'][field] == 0


@pytest.mark.parametrize('language', ['en', 'zh'])
def test_bilingual_denominators_definitions_and_conditional_interpretation(language):
    tex = (ROOT / language / 'main.tex').read_text(encoding='utf-8')
    assert tex.count(r'\label{tab:release-partition-identities}') == 1
    assert 'partition-description-v1.json' in tex
    assert r'\texttt{independent\_block\_id}' in tex
    assert r'\texttt{independent\_blocks}' in tex
    for number in ('5,254', '1,101', '1,094', '39,272', '10,573', '17,038'):
        assert number in tex
    if language == 'en':
        assert 'independent, exchangeable' in tex
        assert 'conditional on that assumption' in tex
        assert 'independent blocks' not in tex
    else:
        assert '以此假定为条件' in tex
        assert '独立块' not in tex
