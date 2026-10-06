"""Pure offline metadata contract controls, not actual upstream acceptance."""
from copy import deepcopy

import pytest

from scripts.pirc25.upstream import fingerprint, identity, input_metadata, rows_by_id, timestamp, version


def record():
    return {'object_id': 'metadata', 'artifact_id': 'synthetic-metadata', 'issue': 'synthetic-control',
            'acceptance_commit': '1' * 40, 'code_sha': '2' * 40,
            'schema_version': 'synthetic-metadata-v1', 'artifact_hash': fingerprint('synthetic metadata control'),
            'artifact_size_bytes': 80, 'path': 'metadata.json', 'format': 'json-metadata',
            'role': 'metadata-only', 'kind': 'metadata', 'license': {'id': 'synthetic-only', 'scope': 'metadata-only'},
            'metadata_checks': {'schema_version': 'synthetic-metadata-v1'},
            **{key: {'not_applicable': 'no research input in pure schema control'}
               for key in ('data_hash', 'split_hash', 'fold_hash', 'feature_hash', 'selection_hash')}}


def test_complete_explicit_metadata_contract_is_readable():
    input_metadata(record())
    selection = record()
    selection['kind'] = 'terrain-selection'
    selection['selection_hash'] = fingerprint('synthetic selection, not actual evidence')
    selection['metadata_checks'].update(status='selected', final_eval_read_count=0,
        source_selection_identity_sha256=selection['selection_hash'], immutability_policy='new_selection_version_required')
    selection['benchmark_binding'] = {'matrix_object_id': 'matrix', 'matrix_lock_object_id': 'matrix-lock'}
    input_metadata(selection)


@pytest.mark.parametrize('field', ['acceptance_commit', 'code_sha', 'artifact_id', 'artifact_hash', 'artifact_size_bytes',
    'schema_version', 'data_hash', 'split_hash', 'fold_hash', 'feature_hash', 'selection_hash', 'license', 'metadata_checks'])
def test_missing_accepted_metadata_cannot_be_inferred(field):
    value = record()
    value.pop(field)
    with pytest.raises(ValueError, match='upstream'):
        input_metadata(value)


@pytest.mark.parametrize('field,value', [('object_id', 'relative/alias'), ('artifact_id', '../other'),
    ('acceptance_commit', 'moving-branch'), ('code_sha', '2' * 64), ('artifact_hash', True),
    ('artifact_size_bytes', True), ('artifact_size_bytes', -1), ('data_hash', {'not_applicable': ''}),
    ('license', {'id': 'synthetic', 'scope': 'data-execution'}), ('role', 'trajectory'),
    ('metadata_checks', {'schema_version': 'synthetic-metadata-v1', 'payload': 'arbitrary payload'}),
    ('metadata_checks', {'schema_version': 'another-schema'})])
def test_invalid_identity_role_license_or_header_is_refused(field, value):
    item = record()
    item[field] = value
    with pytest.raises(ValueError, match='upstream'):
        input_metadata(item)


@pytest.mark.parametrize('count', [True, False, 1, -1, '0'])
def test_selection_requires_typed_zero_final_eval_count(count):
    item = record()
    item['kind'] = 'terrain-selection'
    item['selection_hash'] = fingerprint('synthetic selection')
    item['metadata_checks'].update(status='selected', final_eval_read_count=count,
        source_selection_identity_sha256=item['selection_hash'], immutability_policy='new_selection_version_required')
    with pytest.raises(ValueError, match='upstream'):
        input_metadata(item)


def test_display_branch_does_not_change_input_identity_or_version():
    first, second = record(), deepcopy(record())
    first['source_branch'], second['source_branch'] = 'display-only-one', 'display-only-two'
    assert identity(first) == identity(second)
    assert version(first) == version(second)


@pytest.mark.parametrize('rows', [[{'object_id': 'same'}, {'object_id': 'same'}], [{'object_id': ''}], [None], None])
def test_ambiguous_or_missing_row_identity_is_refused(rows):
    with pytest.raises(ValueError, match='upstream'):
        rows_by_id(rows, 'object_id')


@pytest.mark.parametrize('value', [None, True, '', 'not-a-date', '2026-10-04T00:00:00'])
def test_validation_time_requires_actual_timezone_aware_value(value):
    with pytest.raises(ValueError, match='upstream'):
        timestamp(value)
