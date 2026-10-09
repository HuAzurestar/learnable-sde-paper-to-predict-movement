"""Package the original anonymous saved-score export, never raw research data.

Standard library only. The content AND file hashes are external, frozen pins.
Gzip is a transport encoding, not an experiment, re-score or recovery gate.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import io
import json
from pathlib import Path
import re

CONTENT_SHA256 = '29cb892f47301365b3d7b9a2871f3f71d85fe297f7720d0c6489648f8a4d0c50'
FILE_SHA256 = 'f15578e9da655a2e2df6601427724d11c2ee6effe200e78846bddde54c7fc75e'
FILE_BYTES = 65494805
ANALYSIS_SHA256 = 'd1d67a3bf4cd08d46f7e73f0178950b047197275f3f32e29a61f3f699fe5febc'
AUDIT_SHA256 = '8ff917ad6db55bb3b058b51412ab2e76154ba8bd38c754dd60829db74e25ec67'
LIMIT = 128 * 1024 * 1024
ARCHIVE = 'export.json.gz'
VERSION = 'pirc17-anonymous-replay-input-v1'
PRIVATE_FIELDS = frozenset(('positions_m', 'coordinates', 'center_m', 'target_xy',
    'target_positions', 'hostname', 'artifact_path', 'sample_id', 'latitude',
    'longitude', 'raw_gpx', 'model_parameters', 'particle_arrays'))
PRIVATE_TEXT = re.compile(
    r'(?i)(?:\b[A-Z]:[\\/]|[\\/]Users[\\/][^\\/]+|[\\/]home[\\/][^\\/]+'
    r'|-----BEGIN [A-Z ]*PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,})')


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode('utf-8'))


def scan_public(value):
    """Inspect structured keys and all strings, including compressed input data."""
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            if PRIVATE_FIELDS.intersection(item):
                raise ValueError('private research field in anonymous input')
            pending.extend(item.keys())
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
        elif isinstance(item, str) and PRIVATE_TEXT.search(item):
            raise ValueError('private path or credential in anonymous input')


def validate_bytes(data):
    if len(data) != FILE_BYTES or sha256(data) != FILE_SHA256:
        raise ValueError('input differs from frozen original FILE pin')
    record = json.loads(data)
    if set(record) != {'payload', 'sha256'}:
        raise ValueError('original export envelope required')
    payload = record['payload']
    if record['sha256'] != CONTENT_SHA256 or digest(payload) != CONTENT_SHA256:
        raise ValueError('input differs from frozen original CONTENT pin')
    scan_public(record)
    for key in ('raw_trajectories_exported', 'original_identifiers_exported',
                'numerically_qualified', 'scientific_claim_authorized', 'human_accepted'):
        if payload[key] is not False:
            raise ValueError('original privacy and non-acceptance flags required')
    if payload['new_fits'] != 0 or payload['new_forecasts'] != 0:
        raise ValueError('transport cannot authorize new experiments')
    if (payload['analysis_sha256'], payload['audit_sha256']) != (ANALYSIS_SHA256, AUDIT_SHA256):
        raise ValueError('original analysis and saved-output audit binding required')
    rows = payload['inputs']['score_rows']
    if len(rows) != 11368 or Counter(r['status'] for r in rows) != {'success': 11363, 'failed': 5}:
        raise ValueError('all original rows and retained failures required')
    return record


def compress(data):
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, mode='wb', filename='', mtime=0,
                       compresslevel=6) as stream:
        stream.write(data)
    return output.getvalue()


def expand(archive, limit=LIMIT):
    if len(archive) > limit:
        raise ValueError('compressed input exceeds transport limit')
    with gzip.GzipFile(fileobj=io.BytesIO(archive), mode='rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError('expanded input exceeds transport limit')
    return data


def pack(input_path, directory):
    source, output = Path(input_path), Path(directory)
    if source.stat().st_size > LIMIT:
        raise ValueError('input exceeds transport limit')
    data = source.read_bytes()
    validate_bytes(data)
    if output.exists() and any(output.iterdir()):
        raise ValueError('choose a new empty package directory')
    archive = compress(data)
    manifest = dict(schema_version=VERSION, archive=ARCHIVE,
        archive_sha256=sha256(archive), archive_bytes=len(archive),
        export_sha256=CONTENT_SHA256, export_file_sha256=FILE_SHA256, export_bytes=FILE_BYTES,
        source_analysis_sha256=ANALYSIS_SHA256, source_audit_sha256=AUDIT_SHA256,
        score_rows=11368, successful_score_rows=11363, retained_failed_score_rows=5,
        new_fits=0, new_forecasts=0, new_scores=0, new_resampling=0,
        raw_trajectories_exported=False, original_identifiers_exported=False,
        numerically_qualified=False, scientific_claim_authorized=False, human_accepted=False)
    output.mkdir(parents=True, exist_ok=True)
    (output / ARCHIVE).write_bytes(archive)
    (output / 'manifest.json').write_bytes((json.dumps(manifest, sort_keys=True,
        ensure_ascii=False, allow_nan=False, indent=2) + '\n').encode('utf-8'))
    return manifest


def read_package(directory):
    directory = Path(directory)
    path = directory / 'manifest.json'
    if path.stat().st_size > 65536:
        raise ValueError('transport manifest exceeds 64KiB')
    manifest = json.loads(path.read_bytes())
    # Never trust a manifest-controlled archive name or hash as empirical authority.
    expected = dict(schema_version=VERSION, archive=ARCHIVE, export_sha256=CONTENT_SHA256,
        export_file_sha256=FILE_SHA256, export_bytes=FILE_BYTES,
        source_analysis_sha256=ANALYSIS_SHA256, source_audit_sha256=AUDIT_SHA256,
        score_rows=11368, successful_score_rows=11363, retained_failed_score_rows=5,
        new_fits=0, new_forecasts=0, new_scores=0, new_resampling=0,
        raw_trajectories_exported=False, original_identifiers_exported=False,
        numerically_qualified=False, scientific_claim_authorized=False, human_accepted=False)
    if set(manifest) != set(expected) | {'archive_sha256', 'archive_bytes'}:
        raise ValueError('exact transport manifest fields required')
    if any(type(manifest[k]) is not type(v) or manifest[k] != v for k, v in expected.items()):
        raise ValueError('manifest differs from frozen original input')
    archive_path = directory / ARCHIVE
    if archive_path.stat().st_size > LIMIT:
        raise ValueError('compressed input exceeds transport limit')
    archive = archive_path.read_bytes()
    if manifest['archive_sha256'] != sha256(archive) or manifest['archive_bytes'] != len(archive):
        raise ValueError('archive transport hash or size mismatch')
    data = expand(archive)
    validate_bytes(data)
    return data, manifest


def unpack(directory, output_path):
    data, manifest = read_package(directory)
    # Explicit single file, no archive paths, overwrite, locks or restoration work.
    with Path(output_path).open('xb') as stream:
        stream.write(data)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest='action', required=True)
    p = actions.add_parser('pack')
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--directory', type=Path, required=True)
    v = actions.add_parser('verify')
    v.add_argument('--directory', type=Path, required=True)
    u = actions.add_parser('unpack')
    u.add_argument('--directory', type=Path, required=True)
    u.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.action == 'pack':
        result = pack(args.input, args.directory)
    elif args.action == 'unpack':
        result = unpack(args.directory, args.output)
    else:
        _, result = read_package(args.directory)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
