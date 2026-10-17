"""Actual external qualification bytes and complete references, not science."""
from collections import Counter
import hashlib
import json
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'paper/pirc17/qualification-v1'
BINDINGS={
    'test02.json':('bf21d0c83d9300bf5b17d40b68d62c9a4bcce1b89a0d0eea5aa0b54bf379e640',
                  '9d8a049e3b63a52b0d86a43ef0620a552d3ed7ac587352d8b275f54bb66cc1a1'),
    'card-inventory.json':('18c6af3e2fb90d0ce70542b38d3ebd4e1365762dbf03d540db67d98b1916e011',
                          '58629ab75d1b72d3fb20ae2df89874f11858f9803a1a1f46bbebc0f0d21ad78f'),
}


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),
        ensure_ascii=False,allow_nan=False).encode('utf-8')).hexdigest()


def load(name):
    record=json.loads((PACKAGE/name).read_text(encoding='utf-8'))
    assert digest(record['payload'])==record['sha256']==BINDINGS[name][0]
    return record['payload']


@pytest.mark.parametrize('name',BINDINGS)
def test_original_qualification_bytes_and_content_are_pinned(name):
    assert hashlib.sha256((PACKAGE/name).read_bytes()).hexdigest()==BINDINGS[name][1]
    load(name)
    assert 'paper/pirc17/qualification-v1/*.json -text' in (ROOT/'.gitattributes').read_text()


def test_actual_test02_report_scope_and_counts():
    value=load('test02.json')
    assert value['arithmetic_reproducible'] is True
    assert len(value['checks'])==value['actual_evidence_checks']==21
    assert {v['status'] for v in value['checks']}=={'PASS'}
    assert value['software_tests']==104
    assert value['source_cards_sha256']=='0663f7618d80c0882d14d47e2cc8b0995767975b883726b9da87ae5e5d431754'
    assert value['physical_clock_certified'] is value['independent_participants_certified'] is False


def test_all112_qualified_row_references_match_unchanged_original_cards():
    value=load('card-inventory.json')
    cards=json.loads((ROOT/'paper/pirc17/final-results-v1/cards.json').read_text(encoding='utf-8'))
    assert digest(cards['payload'])==cards['sha256']==value['source_cards_sha256']
    assert value['test02_qualification_sha256']==BINDINGS['test02.json'][0]
    assert value['all112_card_or_disposition_references_verified'] is True
    rows=cards['payload']; sources={}
    for kind in ('input_cards','method_slot_cards','method_arm_cards','terrain_cards'):
        sources.update({row['card_id']:row for row in rows[kind]})
    sources.update({'variant:'+row['variant']['variant_id']:row for row in rows['variant_inventory']})
    sources.update({rows[kind]['card_id']:rows[kind] for kind in ('overall_terrain','history')})
    actual={row['card_or_disposition_id']:row for row in value['card_inventory']}
    assert len(actual)==len(value['card_inventory'])==len(sources)==112
    assert set(actual)==set(sources)
    assert all(row['source_row_sha256']==digest(sources[key]) for key,row in actual.items())
    assert dict(Counter(v['kind'] for v in actual.values()))==value['counts_by_kind']
    assert rows['test02_qualification_asserted'] is False


def test_qualification_is_not_new_science_permission_or_private_publication():
    for name in BINDINGS:
        value=load(name)
        assert value['numerically_qualified'] is value['scientific_claim_authorized'] is value['human_accepted'] is False
        assert value['new_forecasts']==value['new_fits']==0
        pending=[value]
        while pending:
            item=pending.pop()
            if isinstance(item,dict):
                assert not {'artifact_path','positions_m','sample_id','coordinates','hostname','raw_gpx'} & item.keys()
                pending.extend(item.values())
            elif isinstance(item,list): pending.extend(item)
            elif isinstance(item,str):
                assert all(drive + ':' + separator not in item
                           for drive in 'EC' for separator in ('/', '\\'))
    readme=(PACKAGE/'README.md').read_text(encoding='utf-8')
    assert 'full manuscript integration remain DEV-06 work' in readme
