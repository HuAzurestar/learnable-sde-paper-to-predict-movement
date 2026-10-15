import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('pirc26_tex_log', Path(__file__).resolve().parents[1] / 'scripts/pirc26_check_tex_log.py')
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class TexLogTests(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(gate.validate_log('Output written on main.pdf')['max_overfull_pt'], 0.)

    def test_small_overflow_and_boundary(self):
        for width in ('0.7565', '2.0'):
            gate.validate_log('Overfull ' + chr(92) + 'hbox (' + width + 'pt too wide)')

    def test_large_horizontal_overflow(self):
        for width in ('2.00001', '339.6517'):
            with self.assertRaises(ValueError):
                gate.validate_log('Overfull ' + chr(92) + 'hbox (' + width + 'pt too wide)')

    def test_vertical_overflow(self):
        with self.assertRaises(ValueError):
            gate.validate_log('Overfull ' + chr(92) + 'vbox (12.0pt too high)')

    def test_unresolved_and_missing_glyphs(self):
        for text in ('There were undefined references.', 'Citation X undefined on input line 3.',
                     'Rerun to get cross-references right.', 'Missing character: test'):
            with self.assertRaises(ValueError):
                gate.validate_log(text)


if __name__ == '__main__':
    unittest.main()
