"""Independent observation schema, native units and legacy unknown controls."""
import ast
from pathlib import Path

import pytest

from scripts.pirc25.resource_usage import packet, fingerprint, validate_resources, POLICY, DURATION, MEMORY
from scripts.pirc25.aggregate import aggregate
from test_shared_evidence import bundle


def fixture(platform="win32", measured=True):
    cell = {"resource_observation_policy": dict(POLICY), "resource_class": "cpu", "plugin_id": "affine-propagation",
            "propagation_request": {}}
    spec = {"study_id": "fixture", "code_hash": "1"*64, "cells": [cell]}
    attempt = "a"*32
    value = {"schema_version": "pirc27-propagation-resource-observation-v1", "study_id": spec["study_id"],
        "spec_hash": fingerprint(spec), "cell_hash": fingerprint(cell), "code_hash": spec["code_hash"],
        "attempt_id": attempt, "policy_hash": fingerprint(POLICY), "includes_previous_attempts": False,
        "execution_state": "SUCCEEDED", "resumed": False,
        "duration": {"wall_ns": 100, "cpu_ns": 150, "units": "ns", "scope": DURATION,
                     "cpu_scope": "current-process-all-threads"},
        "memory": {"observer_schema": "pirc26-process-resource-observation-v1", "status": "MEASURED",
            "point": "job-payload-before-encoding", "platform": platform, "scope": MEMORY, "units": "bytes",
            "includes_children": False, "includes_previous_attempts": False, "is_phase_isolated": False,
            "resident_counter": "windows.PROCESS_MEMORY_COUNTERS_EX.PeakWorkingSetSize" if platform == "win32"
                else "linux.getrusage.RUSAGE_SELF.ru_maxrss", "peak_resident_bytes": 4096, "reason": None}}
    if not measured:
        value["memory"].update(status="UNAVAILABLE", resident_counter=None, peak_resident_bytes=None,
            reason="NATIVE_COUNTER_UNAVAILABLE" if platform == "win32" or platform.startswith("linux") else "UNSUPPORTED_PLATFORM")
    return value, spec, cell, attempt


@pytest.mark.parametrize("platform,measured", [("win32", True), ("linux", True), ("win32", False), ("darwin", False)])
def test_native_counter_and_unknown_scope(platform, measured):
    packet(*fixture(platform, measured))  # Multithread CPU > wall is legal.


@pytest.mark.parametrize("field,value", [("peak_resident_bytes", 0), ("peak_resident_bytes", True),
    ("units", "KiB"), ("includes_children", 0), ("is_phase_isolated", True), ("resident_counter", "limit")])
def test_wrong_native_units_scopes_and_boolean_substitution(field, value):
    observation, spec, cell, aid = fixture()
    observation["memory"][field] = value
    with pytest.raises(ValueError, match="resource evidence"):
        packet(observation, spec, cell, aid)


def test_legacy_evidence_still_valid_without_inventing_resource_values():
    value = bundle()
    aggregate(value)
    assert all("resource_usage" not in row for row in value["cells"])


def test_reader_only_imports_standard_library():
    path = Path(__file__).resolve().parents[1]/"scripts/pirc25/resource_usage.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    imports.update(a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names)
    assert imports <= {"hashlib", "json", "re"}


@pytest.mark.parametrize("mutation", ["missing-history", "missing-usage", "unexpected-usage", "invented-zero"])
def test_registered_policy_cannot_lose_history_or_invent_a_measurement(mutation):
    _, spec, cell, _ = fixture()
    row = {"registered_cell": cell, "cell_hash": fingerprint(cell), "history": [], "cost": {"sources": []},
        "resource_usage": {"schema_version": "pirc27-resource-history-v1",
            "peak_aggregation": "not-additive;not-a-phase-delta;not-a-tree-peak", "attempts": []}}
    bundle = {"registered_spec": spec, "spec_hash": fingerprint(spec), "study_id": spec["study_id"], "code_hash": spec["code_hash"]}
    validate_resources(row, bundle)  # A truly unattempted cell has no measurements.
    if mutation == "missing-history":
        row["history"] = [{"attempt_id": "a"*32, "state": "FAILED", "error_code": "NUMERICAL_FAILURE"}]
    elif mutation == "missing-usage":
        del row["resource_usage"]
    elif mutation == "unexpected-usage":
        row["registered_cell"] = {}
    else:
        row["resource_usage"]["peak_resident_bytes"] = 0
    with pytest.raises(ValueError, match="resource evidence"):
        validate_resources(row, bundle)


@pytest.mark.parametrize("mutation", ["absent-cell", "empty-cell", "stripped-policy"])
def test_registered_source_policy_cannot_be_downgraded_by_stripping_row_fields(mutation):
    from copy import deepcopy
    _, spec, cell, _ = fixture()
    row = {"cell_hash": fingerprint(cell), "history": [], "cost": {"sources": []}}
    if mutation != "absent-cell":
        row["registered_cell"] = {} if mutation == "empty-cell" else deepcopy(cell)
        if mutation == "stripped-policy":
            del row["registered_cell"]["resource_observation_policy"]
    bundle = {"registered_spec": spec, "spec_hash": fingerprint(spec), "study_id": spec["study_id"], "code_hash": spec["code_hash"]}
    with pytest.raises(ValueError, match="resource evidence"):
        validate_resources(row, bundle)
