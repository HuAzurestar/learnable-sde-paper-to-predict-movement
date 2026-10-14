"""Checks on the actual approved aggregate package; no private runtime needed."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('release_evidence', ROOT / 'scripts/pirc26/evidence.py')
e = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(e)
PAPER = ROOT / 'paper/pirc26'


class ReleaseTests(unittest.TestCase):
    def test_actual_review_and_hash_chain(self):
        value = json.loads((PAPER / 'evidence/summary.json').read_text(encoding='utf8'))
        e.validate_summary(value)
        self.assertFalse(value['review']['human_scientific_acceptance'])
        self.assertFalse(value['provenance_limits']['raw_or_model_export'])
        for source in value['source_catalog'].values():
            self.assertEqual(source['reference']['artifact_id'], source['source_body_sha256'])

    def test_actual_tables_and_claim_index(self):
        value = json.loads((PAPER / 'evidence/summary.json').read_text(encoding='utf8'))
        tables = e.render_tables(value)
        claims = json.loads((PAPER / 'evidence/claims.json').read_text(encoding='utf8'))
        self.assertEqual(claims, e.claim_index(value, tables))
        for name, text in tables.items():
            self.assertEqual((PAPER / 'shared' / name).read_text(encoding='utf8'), text)
            self.assertEqual(hashlib.sha256(text.encode('utf8')).hexdigest(), claims['tables'][name])

    def test_bilingual_labels_citations_and_tables(self):
        en = (PAPER / 'en/main.tex').read_text(encoding='utf8')
        zh = (PAPER / 'zh/main.tex').read_text(encoding='utf8')
        for expression in (r'\\label\{([^}]+)\}', r'\\bibitem\{([^}]+)\}', r'\\tabfile\{([^}]+)\}'):
            self.assertEqual(re.findall(expression, en), re.findall(expression, zh))
        for text in (en, zh):
            citations = {key for group in re.findall(r'\\cite\{([^}]+)\}', text) for key in group.split(',')}
            self.assertTrue(citations <= set(re.findall(r'\\bibitem\{([^}]+)\}', text)))
            self.assertEqual(len(re.findall(r'\\tabfile\{([^}]+)\}', text)), 7)

    def test_relative_recovery_not_absolute(self):
        self.assertIn('relative residual-field RMSE', (PAPER / 'en/main.tex').read_text(encoding='utf8'))
        self.assertIn('相对残差场 RMSE', (PAPER / 'zh/main.tex').read_text(encoding='utf8'))

    def test_rehashed_permission_promotion_rejected(self):
        for mutate in (lambda v: v['review'].update(raw_model_test_disclosure=True),
                       lambda v: v['review'].update(decision='ACCEPTED'),
                       lambda v: v['cost_snapshot'][0].update(charged_ms=-1)):
            value = json.loads((PAPER / 'evidence/summary.json').read_text(encoding='utf8'))
            mutate(value)
            value['review_hash'] = e.fingerprint(value['review'])
            value['safe_summary_hash'] = e.fingerprint({k: v for k, v in value.items() if k != 'safe_summary_hash'})
            with self.assertRaises(ValueError):
                e.validate_summary(value)


if __name__ == '__main__':
    unittest.main()
