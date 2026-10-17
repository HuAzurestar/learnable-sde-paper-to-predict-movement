"""Transport fixtures are software tests; the package tests use real saved data."""
import gzip
import hashlib
import json
from pathlib import Path

import pytest

from scripts import pirc17_replay_input as p
from scripts import project_pirc17_secondary_scores as scores

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'paper/pirc17/replay-input-v1'


@pytest.fixture(scope='module')
def actual():
    return p.read_package(PACKAGE)


def test_actual_archive_decodes_to_exact_original_saved_input(actual):
    data, manifest = actual
    assert len(data) == p.FILE_BYTES == 65494805
    assert hashlib.sha256(data).hexdigest() == p.FILE_SHA256
    value = json.loads(data)
    assert value['sha256'] == p.digest(value['payload']) == p.CONTENT_SHA256
    assert manifest['archive_bytes'] < p.FILE_BYTES
    assert (PACKAGE / p.ARCHIVE).read_bytes()[4:8] == bytes(4)
    assert 'replay-input-v1/** -text' in (ROOT / '.gitattributes').read_text()


def test_actual_all_rows_and_failures_reproduce_current_diagnostics(actual):
    data, _ = actual
    payload = json.loads(data)['payload']
    result = scores.project(payload, p.CONTENT_SHA256)
    original = json.loads((ROOT / 'paper/pirc17/secondary-scores-v1/projection.json').read_bytes())['payload']
    assert len(payload['inputs']['score_rows']) == 11368
    assert result['records'] == original['records']
    assert sum(r['status'] == 'unavailable' for r in result['records']) == 5
    for key in ('raw_trajectories_exported', 'original_identifiers_exported',
                'numerically_qualified', 'scientific_claim_authorized', 'human_accepted'):
        assert payload[key] is False


def test_gzip_is_deterministic_and_preserves_bytes_without_stored_path():
    fixture = b'software fixture, not empirical evidence\n' * 100
    first = p.compress(fixture)
    assert p.compress(fixture) == first
    assert gzip.decompress(first) == fixture
    assert first[3] & 8 == 0  # no FNAME, hence no workstation filename
    assert first[4:8] == bytes(4)


@pytest.mark.parametrize('fixture', [b'', b'{}', b'{"payload": {}, "sha256": "a"}'])
def test_self_consistent_or_partial_json_cannot_replace_frozen_input(fixture):
    with pytest.raises(ValueError, match='FILE pin'):
        p.validate_bytes(fixture)


def test_gzip_expansion_has_a_bounded_output_not_an_unbounded_archive_extract():
    with pytest.raises(ValueError, match='expanded'):
        p.expand(p.compress(b'x' * 10000), limit=100)
    with pytest.raises(ValueError, match='compressed'):
        p.expand(b'x' * 101, limit=100)


def test_corrupt_archive_is_not_a_verified_wait_or_accepted_result():
    fixture = bytearray(p.compress(b'fixture'))
    fixture[-8] ^= 1
    with pytest.raises(OSError):
        p.expand(bytes(fixture))


@pytest.mark.parametrize('field', sorted(p.PRIVATE_FIELDS))
def test_structured_private_fields_are_rejected_even_deeply_nested(field):
    with pytest.raises(ValueError, match='private research field'):
        p.scan_public({'outer': [{'deeper': {field: []}}]})


@pytest.mark.parametrize('value', [chr(67) + ':/' + 'Users/test/data',
    '/' + 'home/test/data', 'ghp_' + 'a' * 21, 'sk-' + 'a' * 21,
    '-----BEGIN ' + 'RSA PRIVATE KEY-----'])
def test_strings_containing_local_paths_or_credentials_are_rejected(value):
    with pytest.raises(ValueError, match='path or credential'):
        p.scan_public({'outer': [value]})


@pytest.mark.parametrize('field,value', [('archive', '../private.json.gz'),
    ('export_sha256', 'f' * 64), ('export_file_sha256', 'f' * 64),
    ('retained_failed_score_rows', 0), ('new_forecasts', 1),
    ('human_accepted', True), ('human_accepted', 0), ('score_rows', 11363),
    ('schema_version', 'unbound'), ('extra', 'unexpected')])
def test_manifest_cannot_control_authority_paths_or_acceptance(tmp_path, field, value):
    fixture = json.loads((PACKAGE / 'manifest.json').read_bytes())
    fixture[field] = value
    (tmp_path / 'manifest.json').write_text(json.dumps(fixture), encoding='utf-8')
    with pytest.raises(ValueError, match='manifest'):
        p.read_package(tmp_path)


def test_unpack_will_not_overwrite_existing_results(tmp_path, monkeypatch):
    # Explicit software seam tests filesystem behavior, not empirical validation.
    monkeypatch.setattr(p, 'read_package', lambda _: (b'fixture', {}))
    target = tmp_path / 'existing.json'
    target.write_bytes(b'original')
    with pytest.raises(FileExistsError):
        p.unpack(tmp_path, target)
    assert target.read_bytes() == b'original'
    new = tmp_path / 'new.json'
    p.unpack(tmp_path, new)
    assert new.read_bytes() == b'fixture'


def test_public_scan_actually_opens_only_the_bound_gzip(monkeypatch, capsys):
    from scripts import check_public_release as release
    monkeypatch.setattr(release, 'candidate_files', lambda: [PACKAGE / p.ARCHIVE])
    assert release.main() == 0
    assert 'passed' in capsys.readouterr().out
    monkeypatch.setattr(release, 'candidate_files', lambda: [ROOT / 'unapproved.gz'])
    assert release.main() == 1
    assert 'unapproved compressed artifact' in capsys.readouterr().out
