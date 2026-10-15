"""Synthetic contract fixtures, not empirical research qualification."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('pirc26_evidence', Path(__file__).resolve().parents[1] / 'scripts/pirc26/evidence.py')
e = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(e)


def fixture():
    diagnostic = {'marginal_x_coverage_0.95': 0., 'marginal_y_coverage_0.95': 0.,
        'paired_endpoint_position_rms_m': 0., 'mean_pointwise_energy_jackknife_se_m': 0.}
    metrics = {'energy_score_mean_m': {'M0_unit_mean': 1., 'M2_unit_mean': 2.,
        'M2_minus_M0_unit_mean': 1., 'exploratory_conditional_percentile_95_interval': [-1., 2.],
        'formal_superiority_claim': False}, 'fde_m': {'M0_unit_mean': 1., 'M2_unit_mean': 2., 'formal_superiority_claim': False}}
    source = {'schema_version': 'pirc26-compact-copied-evidence-v1', 'public_export_authorized': False,
        'statistical_recomputation': False, 'final_test_read': False, 'scientific_qualification': 'not-established',
        'dispositions': {'whole_unit_gate_n': 1, 'global_winner': 'NOT_ESTABLISHED'},
        'real_case_status_counts': {m: {'MEASURED': 63, 'NO_CAUSAL_NATIVE_COVERAGE': 216,
            'SOURCE_UNAVAILABLE': 3, 'NUMERICAL_FAILED': 0, 'UNEXECUTED': 0} for m in ('M0', 'M2')},
        'real_comparisons': [dict(horizon_seconds=h, paired_original_units=n, paired_successful_segments=c,
            candidate_units=7, blind_test=False, qualification='not-established', metrics=deepcopy(metrics))
            for h, n, c in ((10, 6, 26), (30, 6, 17), (60, 5, 20))],
        'real_diagnostics': {m: [dict(horizon_seconds=h, declared_rows=94,
            equal_original_unit_metrics=deepcopy(diagnostic)) for h in (10, 30, 60)] for m in ('M0', 'M2')},
        'M1': {m: {'aggregate': {'fit_rows': 40, 'measured_fits': 40, 'rollout_rows': 30,
            'measured_rollouts': 30, 'matched_teacher_rows': 20, 'matched_recovery_passes': 12,
            'condition_number_max': 1.}, 'calibration': {'matched_discrete_teacher_recovery': 'NOT_PASSED'}}
            for m in ('M1-S', 'M1-R')},
        'O2': {'rows': [dict(seed=s, step_seconds=dt, status='MEASURED', controlled_feasibility_passed=True,
            fit={'steps': 12, 'status': 'MAX_STEPS', 'wall_seconds': 1.},
            resources={'peak_resident_bytes': 1048576}, gradient_checks=[{'passed': True}] * 4)
            for s in (26101411, 26101412, 26101413) for dt in (.25, .125)]},
        'gradient_routes': {'rows': [dict(seed=s, step_seconds=dt, solver=solver, route=route,
            status='MEASURED', controlled_route_passed=True, forward_matched=True,
            finite_difference_passed=True, brownian_paired=True, resource_gate_passed=True,
            gradient_relative_l2=0., helpers={m: {'benchmark_wall_seconds': 1.,
                'resources': {'peak_resident_bytes': 1048576}} for m in ('direct', 'candidate')})
            for s in (26101411, 26101412, 26101413) for dt in (.25, .125)
            for solver, route in (('reversible_heun', 'G2'), ('midpoint', 'G3'))]},
        'cost_snapshot': [{'attempt_id': 'fixture-old', 'arm_id': 'pirc26-m0-o1', 'charged_ms': 1000, 'settled': True}],
        'provenance': {label: {'reference': {'attempt_id': 'fixture-' + label, 'artifact_id': '0' * 64,
            'grant_id': 'must-not-export'}, 'source_code_hash': next(iter(e.EPOCHS)),
            'source_protocol_hash': '1' * 64, 'source_spec_hash': '2' * 64,
            'source_body_sha256': '3' * 64, 'charged_ms': 1}
            for label in ('M1-S', 'M1-R', 'paired', 'diagnostics', 'O2', 'routes')}}
    reference = {'attempt_id': 'fixture-copy', 'artifact_id': '4' * 64, 'charged_ms': 1000}
    review = {'decision': 'APPROVED_SAFE_DERIVATION_ONLY', 'source_artifact_id': reference['artifact_id'],
        'destination': 'HuAzurestar/learnable-sde-paper-to-predict-movement/paper/pirc26',
        'raw_model_test_disclosure': False, 'reviewer': 'fixture, not an actual release approval'}
    return source, reference, review


class EvidenceTests(unittest.TestCase):
    def test_deterministic_and_no_grant_disclosure(self):
        args = fixture()
        one, two = e.make_summary(*args), e.make_summary(*deepcopy(args))
        self.assertEqual(e.encoded(one), e.encoded(two))
        self.assertNotIn(b'must-not-export', e.encoded(one))
        self.assertEqual(sum(r['charged_ms'] for r in one['cost_snapshot']), 2000)

    def test_tables_and_claim_hashes(self):
        value = e.make_summary(*fixture())
        tables = e.render_tables(value)
        self.assertEqual(len(tables), 7)
        self.assertEqual(len(e.claim_index(value, tables)['tables']), 7)
        self.assertEqual(e.table(['A', 'B'], [[1, 2]]),
            '\\begin{tabular}{r r}\n\\toprule\nA & B ' + chr(92) * 2 + '\n\\midrule\n1 & 2 ' + chr(92) * 2 + '\n\\bottomrule\n\\end{tabular}\n')

    def test_changed_counts_and_cherry_pick_rejected(self):
        for mutate in (lambda s: s['real_case_status_counts']['M0'].update(MEASURED=64),
                       lambda s: s['O2']['rows'].pop(),
                       lambda s: s['gradient_routes']['rows'].pop(),
                       lambda s: s['M1']['M1-S']['aggregate'].update(matched_recovery_passes=20),
                       lambda s: s['dispositions'].update(global_winner='M2')):
            source, ref, review = fixture()
            mutate(source)
            with self.assertRaises(ValueError):
                e.make_summary(source, ref, review)

    def test_review_cannot_be_rebound(self):
        source, ref, review = fixture()
        review['source_artifact_id'] = 'wrong'
        with self.assertRaises(ValueError):
            e.make_summary(source, ref, review)

    def test_hash_tampering(self):
        value = e.make_summary(*fixture())
        value['O2']['rows'][0]['fit']['wall_seconds'] += 1
        with self.assertRaises(ValueError):
            e.validate_summary(value)

    def test_private_fields_nonfinite_and_paths(self):
        for value in ({'unit_hash': 'hidden'}, {'fit_rows': [{}]}, {'x': float('nan')},
                      {'x': chr(67) + chr(58) + chr(47) + 'private/example'}):
            with self.assertRaises(ValueError):
                e.safe_tree(value)

    def test_budget_not_reset_or_overrun(self):
        source, ref, review = fixture()
        source['cost_snapshot'][0]['charged_ms'] = 86400000
        with self.assertRaises(ValueError):
            e.make_summary(source, ref, review)


if __name__ == '__main__':
    unittest.main()
