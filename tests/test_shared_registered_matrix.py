"""All-failed formal matrices still need their original identity and plan."""

from copy import deepcopy

import pytest

from scripts.pirc25.aggregate import fingerprint, validate_bundle
from test_shared_evidence import bundle, seal


def failed_matrix():
    value = bundle()
    plan = {"reference_arm_id": "baseline", "candidate_arm_ids": ["candidate"],
            "preregistration_hash": "a" * 64, "failure_policy": "retain-and-exclude-incomplete-blocks"}
    originals = [{k: c[k] for k in ("arm_id", "block_id", "seed")} for c in value["cells"]]
    source = {k: value[k] for k in ("study_id", "code_hash", "data_hash", "protocol_hash")}
    source.update(cells=originals, comparison_plan=plan)
    value.update(registered_spec=source, spec_hash=fingerprint(source), comparison_plan=plan)
    for cell, expected, original in zip(value["cells"], value["expected_cells"], originals):
        cell.update(cell_hash=fingerprint(original), status="FAILED", metrics=None, artifact_id=None)
        expected["cell_hash"] = cell["cell_hash"]
    return seal(value)


def test_failed_matrix_retains_its_original_registered_denominator():
    assert len(validate_bundle(failed_matrix(), formal=True)) == 8


@pytest.mark.parametrize("field", ["study_id", "code_hash", "data_hash", "protocol_hash", "comparison_plan"])
def test_failed_matrix_cannot_change_frozen_source_identity(field):
    value = failed_matrix()
    if field == "comparison_plan":
        value[field] = {**value[field], "reference_arm_id": "candidate", "candidate_arm_ids": ["baseline"]}
    else:
        value[field] = "changed-study" if field == "study_id" else fingerprint("changed")
    with pytest.raises(ValueError, match="registered matrix"):
        validate_bundle(seal(value), formal=True)


def test_failed_matrix_cannot_change_only_unscored_cell_dimensions():
    value = deepcopy(failed_matrix())
    value["cells"][0]["comparison_dimensions"] = {"horizon": 999}
    value["expected_cells"][0]["comparison_dimensions"] = {"horizon": 999}
    with pytest.raises(ValueError, match="registered matrix"):
        validate_bundle(seal(value), formal=True)
