"""Public CI must install existing imports without hiding local evidence gaps."""
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def test_existing_document_and_plot_imports_are_declared():
    lines = (ROOT / 'requirements-test.txt').read_text(encoding='utf-8').splitlines()
    names = {re.split(r'[<>=!~\[]', line, maxsplit=1)[0].lower()
             for line in lines if line.strip() and not line.startswith('#')}
    assert {'pytest', 'numpy', 'matplotlib', 'pillow', 'pymupdf'} <= names


def test_ci_keeps_complete_tests_and_original_evidence_boundaries():
    workflow = (ROOT / '.github/workflows/ci.yml').read_text(encoding='utf-8')
    assert 'pip install -r requirements-test.txt' in workflow
    assert 'python -m pytest tests -q' in workflow
    assert '--ignore' not in workflow
    assert '--deselect' not in workflow
