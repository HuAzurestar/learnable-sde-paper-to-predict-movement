"""Independent reader arithmetic/quota controls; no research evidence minted."""

import ast
from fractions import Fraction
import math
from pathlib import Path

import pytest

from scripts.pirc25.analytic_qualification import bounded, interval, outward
from scripts.pirc25.validate_analytic import validate


@pytest.mark.parametrize("document", [None, [], [[], []], [["0", "3"], ["1", "3"]],
    [["00", "1"], ["1", "1"]], [["2", "2"], ["2", "1"]], [["2", "1"], ["1", "1"]],
    [["1", "0"], ["1", "1"]], [["1", "-1"], ["1", "1"]], [[True, "1"], ["1", "1"]],
    [[str(1 << 4097), "1"], [str(1 << 4097), "1"]], [["1", str(1 << 161)], ["1", "1"]]])
def test_noncanonical_or_oversize_interval_refused(document):
    with pytest.raises(ValueError):
        interval(document)


def test_exact_dyadic_read_and_outward_rounding_are_independent():
    assert interval([["-1", "2"], ["3", "4"]]) == (Fraction(-1, 2), Fraction(3, 4))
    for value in (Fraction(0), Fraction(1, 2), Fraction(1, 3), Fraction(1, 1 << 1100)):
        assert Fraction(outward(value)) >= value
        if outward(value) != 0:
            assert Fraction(math.nextafter(outward(value), -math.inf)) < value


@pytest.mark.parametrize("document,options", [("x"*1236, {"string_limit": 1235}),
    ([0]*2049, {"nodes": 2048}), ([[[0]]], {"depth_limit": 2}),
    ({"long-key"*20: 0}, {}), (float("nan"), {}), (1 << 4097, {}), ("x"*200, {"byte_limit": 100})])
def test_reader_resource_quotas_are_fixed_and_separate(document, options):
    options = {"byte_limit": 128*1024, **options}
    with pytest.raises(ValueError, match="analytic qualification"):
        bounded(document, **options)


def test_reader_imports_only_standard_library_and_never_runtime_provider():
    path = Path(__file__).resolve().parents[1]/"scripts/pirc25/analytic_qualification.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    imported.update(alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
    assert imported <= {"datetime", "fractions", "hashlib", "json", "math"}


@pytest.mark.parametrize("expected", [None, "", "0"*64, "f"*63])
def test_trusted_expected_transport_hash_is_not_optional(expected):
    with pytest.raises(ValueError, match="trusted expected bundle hash"):
        validate({"bundle_hash": "f"*64}, expected)
