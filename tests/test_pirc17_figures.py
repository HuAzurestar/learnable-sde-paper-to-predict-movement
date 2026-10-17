"""SYNTHETIC figure transport, not formal numerical/empirical evidence."""
from copy import deepcopy
import hashlib
import io
import json

from PIL import Image
import pytest

from scripts import plot_pirc17 as module
from tests.test_pirc17_tables import cards,write_cards


def test_full_figure_specification_retains_unavailability_and_separate_claim_classes(cards):
    spec=module.specification(cards)
    assert len(spec['figures'])==16
    assert len([r for r in spec['figures'].values() if r['kind']=='paired'])==6
    assert len(spec['figures']['paired-terrain-causal_prefix']['rows'])==9
    assert len(spec['figures']['paired-methods-causal_prefix']['rows'])==21
    assert len(spec['figures']['terrain-times-causal_prefix']['rows'])==40
    assert len(spec['figures']['mechanisms-causal_prefix']['rows'])==28
    assert len(spec['figures']['runtime-conditions']['rows'])==30
    assert len(spec['figures']['scientific-dispositions']['rows'])==38
    assert spec['new_forecasts']==spec['new_fits']==spec['new_hypothesis_tests']==0
    assert not spec['scientific_claim_authorized'] and not spec['human_accepted'] and not spec['manuscript_written']
    assert all(r['delta_candidate_minus_control_m'] is None for r in spec['figures']['paired-terrain-causal_prefix']['rows'])
    assert all(r['energy_score_m'] is None for r in spec['figures']['terrain-times-causal_prefix']['rows'])


@pytest.mark.parametrize('kind',['paired','times','mechanisms','runtime','dimensions','dispositions','kernel'])
@pytest.mark.parametrize('format',['png','pdf'])
def test_each_kind_renders_missing_evidence_deterministically_without_inventing_zero(cards,kind,format):
    item=next(v for v in module.specification(cards)['figures'].values() if v['kind']==kind)
    before=deepcopy(item)
    first=module.render(item,format)
    assert module.render(item,format)==first and item==before
    if format=='png':
        with Image.open(io.BytesIO(first)) as image:
            assert image.width>500 and image.height>300
            assert image.info['Software']=='PIRC17 public review renderer'
    else:
        assert first.startswith(b'%PDF') and b'/CreationDate' not in first


def test_bootstrap_interval_outside_estimate_is_not_clipped_or_recentered(cards):
    item=module.specification(cards)['figures']['paired-terrain-causal_prefix']
    item['rows'][0].update(delta_candidate_minus_control_m=3,simultaneous_lower_m=-2,simultaneous_upper_m=1,
        verdict='inconclusive')
    before=deepcopy(item)
    assert module.render(item,'png').startswith(b'\x89PNG') and item==before
    item['rows'][0]['simultaneous_lower_m']=2
    with pytest.raises(ValueError,match='ordered'): module.render(item,'png')


def test_available_time_profile_copies_four_original_points_and_registered_region_level(cards):
    item=module.specification(cards)['figures']['terrain-times-causal_prefix']
    rows=[r for r in item['rows'] if r['configuration']=='all-terrain']
    for i,r in enumerate(rows):
        r.update(energy_score_m=10+i,position_entropy_nats=2+i,
            coverage=[dict(level=.95,coverage_rate=.8+i*.02,mean_area_m2=100+i)],status='computed')
    before=deepcopy(item)
    assert module.render(item,'png').startswith(b'\x89PNG') and item==before
    rows[0]['coverage']=[]
    with pytest.raises(ValueError,match='95%'): module.render(item,'png')


def test_available_runtime_and_recorded_kernel_cost_are_different_axes(cards):
    spec=module.specification(cards)
    runtime=spec['figures']['runtime-conditions']
    runtime['rows'][0].update(status='computed',summary=dict(total_latency_p50_ms=100,total_latency_p95_ms=200),
        counts_by_status={'success':4,'failed':1})
    kernel=spec['figures']['recorded-kernel-costs']
    kernel['rows'][0].update(recorded_kernel_mean_seconds=1.25,recorded_timing_count=10,missing_timing_count=280)
    mechanism=spec['figures']['mechanisms-causal_prefix']
    mechanism['rows'][0].update(expected_count=1,available_count=1,passed=False,status='computed')
    for item in (runtime,kernel,mechanism):
        before=deepcopy(item)
        assert module.render(item,'png').startswith(b'\x89PNG') and item==before


def test_full_bundle_rebuild_missing_only_reuse_and_corruption_rejection(cards,tmp_path,monkeypatch):
    source=tmp_path/'SOFTWARE-public-cards.json'
    sha=write_cards(source,cards)
    result=module.generate(source,sha,tmp_path/'first',software_fixture=True)
    assert result['figure_count']==16 and result['image_count']==32
    root=tmp_path/'first'/result['bundle_id']
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))['payload']
    assert manifest['identity']['source_cards_sha256']==sha and len(manifest['files'])==33
    assert manifest['identity']['software_fixture_only'] is True
    for name,binding in manifest['files'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==binding['sha256']
    rebuilt=module.generate(source,sha,tmp_path/'fresh-rebuild',software_fixture=True)
    assert rebuilt['manifest_sha256']==result['manifest_sha256']
    actual_render=module.render
    calls=[]
    def tracked(item,format):
        calls.append((item['kind'],format)); return actual_render(item,format)
    monkeypatch.setattr(module,'render',tracked)
    assert module.generate(source,sha,tmp_path/'first',software_fixture=True)==result and calls==[]
    target=root/'terrain-dimensions.png'
    raw=target.read_bytes(); target.unlink()  # Own generated software-test image.
    assert module.generate(source,sha,tmp_path/'first',software_fixture=True)==result and target.read_bytes()==raw
    assert calls==[('dimensions','png')]
    target.write_bytes(b'SOFTWARE corrupted figure')
    with pytest.raises(ValueError,match='never overwrite'): module.generate(source,sha,tmp_path/'first',software_fixture=True)


def test_changed_forecast_labels_and_wrong_source_pin_are_rejected(cards,tmp_path):
    changed=deepcopy(cards); changed['fixed_forecast']['particles']=1024
    with pytest.raises(ValueError,match='unchanged'): module.specification(changed)
    source=tmp_path/'SOFTWARE-public-cards.json'; write_cards(source,cards)
    with pytest.raises(ValueError,match='pinned'):
        module.generate(source,module.tables.digest('SOFTWARE wrong source'),tmp_path/'absent')
    assert not (tmp_path/'absent').exists()
