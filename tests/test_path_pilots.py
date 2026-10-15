"""Stdlib metadata controls; actual saved worker proofs are paired Runtime tests."""
from copy import deepcopy

import pytest

from scripts.pirc25.validate_path_pilots import validate
from scripts.pirc25.aggregate import fingerprint
from tests.test_shared_evidence import bundle, seal


def missing_matrix():
    value = bundle()
    registered = []
    for row in value["cells"]:
        cell = {k: row[k] for k in ("arm_id", "block_id", "seed")}
        cell["plugin_id"] = "affine-path-qualification"
        registered.append(cell)
        row.update(cell_hash=fingerprint(cell), registered_cell=cell, status="MISSING", metrics=None,
            attempt_id=None, run_id=None, artifact_id=None, qualification=None)
    value["registered_spec"] = {k: value[k] for k in ("study_id", "code_hash", "protocol_hash", "data_hash")}
    value["registered_spec"]["cells"] = registered
    value["spec_hash"] = fingerprint(value["registered_spec"])
    value["expected_cells"] = [{k: row[k] for k in ("cell_hash", "arm_id", "block_id", "seed")} for row in value["cells"]]
    value["path_pilot_evidence"] = "owned-saved-path-pilot-results-and-native-execution-v1"
    return seal(value)


def test_all_missing_matrix_remains_unknown_not_a_zero_error_or_pass_claim():
    value = missing_matrix()
    report = validate(value, value["bundle_hash"])
    assert report["verified_pilot_cells"] == report["passed_cells"] == report["failed_cells"] == 0
    assert report["expected_cells"] == report["noncompleted_rows"] == 8
    assert report["scientific_qualification"] is False


@pytest.mark.parametrize("fault", ["clipped", "duplicate-source", "wrong-source", "missing-marker", "nonpilot"])
def test_source_inventory_and_explicit_transport_cannot_be_self_resealed_away(fault):
    value = deepcopy(missing_matrix())
    if fault == "clipped":
        value["cells"].pop()
        value["expected_cells"].pop()
    elif fault == "duplicate-source":
        value["registered_spec"]["cells"].append(deepcopy(value["registered_spec"]["cells"][0]))
        value["spec_hash"] = fingerprint(value["registered_spec"])
    elif fault == "wrong-source":
        value["registered_spec"]["study_id"] = "other-study"
        value["spec_hash"] = fingerprint(value["registered_spec"])
    elif fault == "missing-marker":
        value.pop("path_pilot_evidence")
    else:
        value["cells"][0]["registered_cell"]["plugin_id"] = "foreign-plugin"
    value = seal(value)
    with pytest.raises(ValueError):
        validate(value, value["bundle_hash"])


@pytest.mark.parametrize("expected", [None, "", "0"*64, True])
def test_an_external_exact_owner_hash_is_always_required(expected):
    value = missing_matrix()
    with pytest.raises(ValueError, match="trusted expected bundle hash"):
        validate(value, expected)
