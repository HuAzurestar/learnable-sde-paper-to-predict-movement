"""Independent stdlib-only validation of frozen upstream metadata receipts.

No runtime/provider imports, filesystem metadata-root reads or implicit grants.
The expected transport hash and operator catalog are trust boundaries; hashes
validate recorded bindings, not the truth of off-platform human attestations.
"""
from datetime import datetime
import hashlib
import json
import re


_HASH_FIELDS = ('data_hash', 'split_hash', 'fold_hash', 'feature_hash', 'selection_hash')
_HEADERS = {'schema_version', 'status', 'overall_status', 'scientific_role', 'final_eval_read_count',
            'source_selection_identity_sha256', 'immutability_policy', 'data_hash', 'split_hash',
            'fold_hash', 'feature_hash', 'selection_hash', 'code_sha'}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def require(condition, detail):
    if not condition:
        raise ValueError('invalid admission evidence: upstream ' + detail)


def hash_ref(value, length=64):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{' + str(length) + '}', value) is not None


def identity(record):
    return {key: value for key, value in record.items() if key != 'source_branch'}


def version(record):
    return tuple(record.get(key) for key in ('issue', 'acceptance_commit', 'code_sha', 'object_id'))


def rows_by_id(rows, key):
    require(isinstance(rows, list) and all(isinstance(row, dict) and isinstance(row.get(key), str)
            and bool(row[key]) for row in rows), 'invalid ' + key + ' rows')
    result = {row[key]: row for row in rows}
    require(len(result) == len(rows), 'duplicate ' + key)
    return result


def timestamp(value):
    require(isinstance(value, str), 'missing validation time')
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError('invalid admission evidence: upstream invalid validation time') from exc
    require(parsed.tzinfo is not None and parsed.utcoffset() is not None, 'naive validation time')
    return parsed


def input_metadata(record):
    required = ('object_id', 'issue', 'acceptance_commit', 'code_sha', 'schema_version', 'artifact_id',
                'artifact_hash', 'artifact_size_bytes', 'path', 'format', 'role', 'kind', 'license', 'metadata_checks') + _HASH_FIELDS
    require(all(key in record for key in required), 'incomplete accepted input')
    require(all(isinstance(record[key], str) and record[key].strip()
            for key in ('object_id', 'artifact_id', 'issue', 'schema_version', 'path')), 'invalid input identity')
    require(all(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', record[key]) is not None
                for key in ('object_id', 'artifact_id')), 'input object identifier')
    require(hash_ref(record['acceptance_commit'], 40) and hash_ref(record['code_sha'], 40)
            and hash_ref(record['artifact_hash']) and type(record['artifact_size_bytes']) is int
            and record['artifact_size_bytes'] >= 0, 'invalid input commit/hash/size')
    for key in _HASH_FIELDS:
        value = record[key]
        require(hash_ref(value) or isinstance(value, dict) and set(value) == {'not_applicable'}
                and isinstance(value['not_applicable'], str) and bool(value['not_applicable'].strip()),
                'missing explicit ' + key)
    license = record['license']
    require(record['role'] == 'metadata-only' and isinstance(license, dict)
            and isinstance(license.get('id'), str) and bool(license['id'].strip())
            and license.get('scope') == 'metadata-only', 'input license/role')
    checks = record['metadata_checks']
    require(record['format'] == 'json-metadata' and record['kind'] in {'metadata', 'terrain-selection'}
            and isinstance(checks, dict) and not set(checks) - _HEADERS
            and checks.get('schema_version') == record['schema_version']
            and all(type(value) in (str, int, bool, type(None)) for value in checks.values()), 'scalar schema checks')
    if record['kind'] == 'terrain-selection':
        require(hash_ref(record['selection_hash']) and checks.get('status') == 'selected'
                and type(checks.get('final_eval_read_count')) is int and checks['final_eval_read_count'] == 0
                and checks.get('immutability_policy') == 'new_selection_version_required'
                and checks.get('source_selection_identity_sha256') == record['selection_hash'],
                'immutable zero-final-eval selection')
        binding = record.get('benchmark_binding')
        require(isinstance(binding, dict) and set(binding) == {'matrix_object_id', 'matrix_lock_object_id'}
                and all(isinstance(value, str) and bool(value) for value in binding.values()),
                'explicit frozen selection matrix/lock references')


def publication(event, object_id, content_hash):
    require(isinstance(event, dict) and event.get('event_kind') == 'MANIFEST'
            and fingerprint({key: value for key, value in event.items() if key != 'hash'}) == event.get('hash')
            and event.get('payload') == {'object_id': object_id, 'sha256': content_hash}
            and type(event.get('sequence')) is int and event['sequence'] > 0, 'publication identity/hash')
    timestamp(event['created_at'])
    return event['sequence']


def validate_upstream(receipt):
    try:
        _validate_upstream(receipt)
    except (KeyError, TypeError, AttributeError, StopIteration) as exc:
        raise ValueError('missing or malformed upstream admission evidence') from exc


def _validate_upstream(receipt):
    docs, spec, cell = receipt['documents'], receipt['spec'], receipt['cell']
    evidence, settings, package, prereg = docs['upstream_snapshot'], spec['admission'], docs['package'], docs['preregistration']
    snapshot, catalog, validation = evidence['snapshot'], evidence['acceptance_catalog'], evidence['validation']
    require(snapshot.get('schema_version') == 'pirc25-upstream-snapshot-v1', 'snapshot schema')
    inputs = rows_by_id(snapshot['inputs'], 'object_id')
    studies = rows_by_id(snapshot['studies'], 'study_id')
    cells = rows_by_id(snapshot['cells'], 'cell_id')
    normalized = {key: value for key, value in snapshot.items() if key != 'source_branch'}
    normalized['inputs'] = [identity(record) for record in snapshot['inputs']]
    snapshot_hash, catalog_hash = fingerprint(normalized), fingerprint(catalog)
    require(snapshot_hash == settings['upstream_snapshot_hash'] == package['upstream_snapshot_hash']
            and catalog_hash == settings['upstream_acceptance_hash'] == package['upstream_acceptance_hash'], 'frozen references')
    require(catalog.get('schema_version') == 'pirc25-upstream-acceptance-v1'
            and isinstance(catalog.get('source'), str) and bool(catalog['source'].strip())
            and isinstance(catalog.get('entries'), list) and isinstance(catalog.get('source_evidence'), dict)
            and catalog['source_evidence'].get('entries') == catalog['entries']
            and fingerprint(catalog['source_evidence']) == catalog.get('source_evidence_hash'), 'operator catalog evidence')
    accepted = {}
    for entry in catalog['entries']:
        require(isinstance(entry, dict) and isinstance(entry.get('input'), dict), 'catalog row')
        key = version(entry['input'])
        if any(not isinstance(value, str) for value in key):
            continue
        if key in accepted:
            old = accepted[key]
            if old.get('status') != entry.get('status') or old.get('input') is None or identity(old['input']) != identity(entry['input']):
                accepted[key] = {'status': 'ambiguous'}
        else:
            accepted[key] = entry
    study_id, cell_hash = spec['study_id'], fingerprint(cell)
    study, selected = studies[study_id], cells[cell_hash]
    frozen_cells = [row['cell_id'] for row in snapshot['cells'] if row.get('study_id') == study_id]
    actual_cells = {fingerprint(row) for row in spec['cells']}
    require(len(frozen_cells) == len(actual_cells) and set(frozen_cells) == actual_cells
            and selected['study_id'] == study_id, 'complete study/cell matrix')
    dependencies = selected['upstream_ids']
    require(isinstance(dependencies, list) and all(isinstance(name, str) for name in dependencies)
            and len(set(dependencies)) == len(dependencies) and all(name in inputs for name in dependencies), 'selected dependency set')
    cutover = study['pirc22_cutover']
    require(isinstance(cutover, dict) and cutover.get('mode') in {'adopted_primary', 'pending_addendum', 'not_applicable'}
            and selected.get('role') in {'primary', 'secondary'}, 'explicit cutover/role')
    require(prereg.get('upstream_bindings', {}).get(study_id) == {'snapshot_hash': snapshot_hash,
            'acceptance_catalog_hash': catalog_hash, 'pirc22_cutover': cutover}, 'pre-read frozen cutover')
    terrain = [inputs[name] for name in dependencies if inputs[name].get('kind') == 'terrain-selection']
    require(not (cutover['mode'] in {'pending_addendum', 'not_applicable'} and terrain)
            and not (cutover['mode'] == 'adopted_primary' and selected['role'] == 'primary'
                     and (len(terrain) != 1 or terrain[0].get('selection_hash') != cutover.get('selection_hash'))), 'cutover dependency route')
    require(validation.get('schema_version') == 'pirc25-upstream-validation-v1'
            and validation.get('snapshot_hash') == snapshot_hash and validation.get('acceptance_catalog_hash') == catalog_hash
            and validation.get('data_authorization') == 'none' and validation.get('rejected_inputs') == []
            and fingerprint(validation) == evidence['validation_hash'], 'validation identity/refusal')
    require(validation.get('cells') == [{**selected, 'status': 'ready', 'rejected_inputs': []}], 'selected ready receipt')
    consumer = {'attempt_id': receipt['attempt_id'], 'run_id': receipt['run_id'], 'study_id': study_id,
                'cell_hash': cell_hash, 'spec_hash': fingerprint(spec)}
    require(validation.get('consumer') == consumer, 'validation consumer identity')
    finished = timestamp(validation['validation_finished_at'])
    require(finished <= timestamp(receipt['admitted_at']), 'validation after admission')
    resolved = rows_by_id(validation['resolved'], 'object_id')
    require(set(resolved) == set(dependencies), 'complete resolved input set')
    semantic_ids = set()
    for record in terrain:
        input_metadata(record)
        semantic_ids.update([record['object_id'], *record['benchmark_binding'].values()])
    for name in dependencies:
        record, actual = inputs[name], resolved[name]
        input_metadata(record)
        entry = accepted.get(version(record))
        require(entry is not None and entry.get('status') == 'accepted'
                and identity(entry['input']) == identity(record), 'input not in exact accepted version')
        extras = {'physical_size_bytes', 'last_validated_at'}
        if name in semantic_ids:
            extras.add('semantic_document')
        require(identity({key: value for key, value in actual.items() if key not in extras})
                == identity(record) and type(actual.get('physical_size_bytes')) is int
                and actual['physical_size_bytes'] == record['artifact_size_bytes']
                and actual.get('last_validated_at') == validation['validation_finished_at'], 'recorded input hash/physical size/time')
    # Separate pure module; never import the runtime or reopen source roots.
    if __package__:
        from .selection import common_primary, selection_documents
    else:
        from selection import common_primary, selection_documents
    for record in terrain:
        selection_documents(record, inputs, resolved, dependencies)
    if cutover['mode'] == 'adopted_primary' and selected['role'] == 'primary':
        primary = [row for row in snapshot['cells'] if row.get('study_id') == study_id and row.get('role') == 'primary']
        actual_primary = [row for row in spec['cells'] if cells[fingerprint(row)].get('role') == 'primary']
        common_primary(cutover, terrain, inputs, resolved, dependencies, primary, actual_primary)
    publications = evidence['publication_events']
    frozen = docs['preregistration_event']
    prereg_sequence = publication(frozen, 'preregistration-' + fingerprint(prereg), fingerprint(prereg))
    snapshot_sequence = publication(publications['snapshot'], 'upstream-snapshot-' + snapshot_hash, snapshot_hash)
    catalog_sequence = publication(publications['acceptance_catalog'], 'upstream-acceptance-' + catalog_hash, catalog_hash)
    validated_sequence = publication(publications['validation'], 'upstream-validation-' + evidence['validation_hash'], evidence['validation_hash'])
    event = evidence['validation_event']
    expected = {key: consumer[key] for key in ('study_id', 'cell_hash', 'attempt_id', 'run_id')}
    expected.update(snapshot_hash=snapshot_hash, acceptance_catalog_hash=catalog_hash,
                    validation_hash=evidence['validation_hash'], status='ready', rejected_inputs=[])
    require(event.get('event_kind') == 'UPSTREAM_VALIDATION' and event.get('payload') == expected
            and fingerprint({key: value for key, value in event.items() if key != 'hash'}) == event.get('hash')
            and type(event.get('sequence')) is int and max(snapshot_sequence, catalog_sequence) < prereg_sequence
            < validated_sequence < event['sequence'] and all(event['sequence'] < read['sequence'] for read in receipt['input_evidence']),
            'observed publication/validation order')
    timestamp(event['created_at'])
