"""Offline counterpart of the frozen PIRC-22 consumer contract.

Only recorded, catalog-bound documents are used. No runtime imports, source
paths, training or PIRC-17 ablation generation. Published matrix identities
are schema-versioned constants, not new scientific acceptance decisions.
"""
import hashlib
import json
import math

if __package__:
    from .upstream import fingerprint, require
else:
    from upstream import fingerprint, require


_MATRIX_HASH = '94e91ad3bfe9a5421a697dd8c7f6d964f61bdf95478a7a4a68175707abaa9d4f'
_FEATURE_HASH = 'e53857fd2749da76c3bf856537d3ff8e30c7c2989d2d585dcc068ac913058616'
_WIDTHS = {'linear': [], 'mlp-small-16': [16], 'mlp-small-32': [32],
           'mlp-medium-32-16': [32, 16], 'mlp-medium-64-32': [64, 32]}
_TRAINING = {'learning_rate': 1e-3, 'weight_decay': 1e-4, 'batch_size': 256,
             'maximum_epochs': 200, 'patience': 20, 'minimum_delta': 1e-8}


def legacy_hash(value):
    # Original PIRC-22 uses ensure_ascii=True, unlike the receipt transport.
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode('utf-8')).hexdigest()


def selection_documents(terrain, inputs, resolved, dependencies):
    """Verify original consumer/matrix semantics independently of ready flags."""
    record = terrain
    binding = record['benchmark_binding']
    names = [record['object_id'], binding['matrix_object_id'], binding['matrix_lock_object_id']]
    require(len(set(names)) == 3 and all(name in dependencies for name in names),
            'complete declared selection matrix/lock inputs')
    documents = []
    for name in names:
        document = resolved[name].get('semantic_document')
        require(isinstance(document, dict) and fingerprint(document) == inputs[name].get('canonical_hash'),
                'catalog-bound selection semantic identity')
        require(all(key in document and type(document[key]) is type(value) and document[key] == value
                    for key, value in inputs[name]['metadata_checks'].items()), 'semantic metadata headers')
        documents.append(document)
    consumer, matrix, lock = documents
    matrix_hash = legacy_hash(matrix)
    require(matrix.get('schema_version') == 'pirc22-representation-matrix-v1'
            and matrix.get('status') == 'FROZEN'
            and matrix.get('mutation_policy') == 'new_matrix_id_required'
            and lock.get('schema_version') == 'pirc22-representation-matrix-lock-v1'
            and lock.get('matrix_id') == matrix.get('matrix_id')
            and lock.get('matrix_identity_sha256') == matrix_hash == _MATRIX_HASH
            and matrix.get('source_feature_spec_id') == 'pirc21-p0-feature-spec-v1'
            and matrix.get('source_feature_spec_sha256') == _FEATURE_HASH,
            'original frozen representation matrix/lock')
    require(consumer.get('schema_version') == 'pirc22-benchmark-selection-consumer-v1'
            and consumer.get('consumer_identity_sha256') == legacy_hash(
                {key: value for key, value in consumer.items() if key != 'consumer_identity_sha256'})
            and consumer.get('status') == 'selected'
            and type(consumer.get('final_eval_read_count')) is int and consumer['final_eval_read_count'] == 0
            and consumer.get('matrix_identity_sha256') == matrix_hash, 'original BenchmarkSelection identity')
    configuration = consumer.get('selected_configuration')
    require(isinstance(configuration, dict), 'original selected configuration')
    rows = matrix['candidates']
    require(isinstance(rows, list), 'matrix candidates')
    candidates = {row['candidate_id']: row for row in rows}
    candidate = candidates.get(str(configuration.get('candidate_id', '')))
    widths = _WIDTHS.get(str(configuration.get('conditioner_id', '')))
    require(candidate is not None and widths is not None
            and all(candidate[key] == configuration.get(key) for key in
                    ('variant_ids', 'composition_ids', 'interaction_ids', 'model_input_dim'))
            and configuration.get('hidden_widths') == widths
            and configuration.get('layer_count') == len(widths), 'original selected matrix/conditioner configuration')
    training = configuration.get('training_config')
    require(isinstance(training, dict) and not set(training) - set(_TRAINING), 'original training configuration')
    values = {**_TRAINING, **training}
    for key in ('batch_size', 'maximum_epochs', 'patience'):
        require(type(values[key]) is int and values[key] >= 1, 'original positive training budget')
    for key in ('learning_rate', 'weight_decay', 'minimum_delta'):
        value = values[key]
        require(isinstance(value, (int, float)) and math.isfinite(value)
                and (value > 0 if key == 'learning_rate' else value >= 0), 'original finite training budget')
    return {'selection_hash': consumer['source_selection_identity_sha256'],
            'consumer_identity_sha256': consumer['consumer_identity_sha256'],
            'matrix_identity_sha256': consumer['matrix_identity_sha256'], 'configuration': configuration}, set(names)


def common_primary(cutover, terrain, inputs, resolved, dependencies, frozen_cells, actual_cells):
    common = cutover.get('conditioner_binding')
    require(len(terrain) == 1 and isinstance(common, dict), 'common frozen primary conditioner')
    observed, names = selection_documents(terrain[0], inputs, resolved, dependencies)
    require(observed == common and observed['selection_hash'] == cutover.get('selection_hash')
            and all(row.get('conditioner_binding') == common
                    and isinstance(row.get('upstream_ids'), list)
                    and all(isinstance(name, str) for name in row['upstream_ids'])
                    and names <= set(row['upstream_ids']) for row in frozen_cells)
            and all(row.get('conditioner_binding') == common for row in actual_cells),
            'all primary cells share the frozen conditioner')
