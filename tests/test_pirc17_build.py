"""Fast software tests: no forecasts, private inputs, or TeX installation required."""

import importlib.util
from pathlib import Path
import tempfile

import pytest

SPEC = importlib.util.spec_from_file_location(
    "build_pirc17", Path(__file__).resolve().parents[1] / "scripts/build_pirc17.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@pytest.mark.parametrize("warning", [
    "LaTeX Warning: There were undefined references.",
    "LaTeX Warning: Citation `unknown' on page 1 undefined on input line 20.",
    "LaTeX Warning: Reference `unknown' on page 1 undefined on input line 20.",
    "LaTeX Warning: Rerun to get cross-references right.",
    "Missing character: There is no glyph in font!",
    r"Overfull \hbox (10pt too wide) in paragraph at lines 1--2",
    r"Overfull \vbox (10pt too high) detected at line 5",
])
def test_reject_unresolved_or_clipped_output(warning):
    with pytest.raises(ValueError):
        MODULE.check_log(warning)


def test_allow_clean_log_with_underfull_spacing():
    MODULE.check_log(r"Underfull \hbox (badness 1000) in paragraph")


def test_output_preserves_paper_and_previous_evidence():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        for output in [root, root / "paper", root / "paper/pirc17/en"]:
            with pytest.raises(ValueError):
                MODULE.validate_output(output, root)
        output = root / "build"
        assert MODULE.validate_output(output, root) == output.resolve()
        output.mkdir()
        (output / "previous.log").touch()
        with pytest.raises(ValueError):
            MODULE.validate_output(output, root)
