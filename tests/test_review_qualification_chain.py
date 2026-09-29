"""R1: a plugin's qualification string is not formal admission evidence."""

import pytest

from scripts.pirc25.aggregate import aggregate
from test_shared_evidence import bundle, seal


def test_r1_formal_rejects_self_declared_qualification_without_evidence_chain():
    value = bundle()
    value["comparison_plan"] = {"reference_arm_id": "baseline", "candidate_arm_ids": ["candidate"],
        "preregistration_hash": "a" * 64, "failure_policy": "retain-and-exclude-incomplete-blocks"}
    for cell in value["cells"]:
        cell["qualification"] = "qualified"
    with pytest.raises(ValueError, match="evidence|admission|qualification"):
        aggregate(seal(value), formal=True)
