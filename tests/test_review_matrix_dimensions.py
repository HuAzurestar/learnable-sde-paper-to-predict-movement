"""R5: horizon strata do not create budget arms or independent seed samples."""

import copy
import csv
import io
import json

import pytest

from scripts.pirc25.aggregate import aggregate, csv_bytes, evidence_index, fingerprint
from test_shared_evidence import bundle, seal


def matrix():
    value = bundle()
    original = value["cells"]
    cells = []
    for horizon in (1, 2):
        for source in original:
            row = copy.deepcopy(source)
            row["comparison_dimensions"] = {"horizon": horizon, "region": "whole"}
            row["cell_hash"] = fingerprint([source["cell_hash"], horizon])
            row["attempt_id"] += f"-h{horizon}"
            row["metrics"]["error"] += 100 * (horizon - 1)
            cells.append(row)
    value["cells"] = cells
    value["expected_cells"] = [{key: row[key] for key in
        ("cell_hash", "arm_id", "block_id", "seed", "comparison_dimensions")} for row in cells]
    return seal(value)


def test_multi_horizon_matrix_is_stratified_without_renaming_arms():
    result = aggregate(matrix())
    assert result["expected_cell_count"] == 16
    assert {row["arm_id"] for row in result["arms"]} == {"baseline", "candidate"}
    summaries = {(row["arm_id"], row["comparison_dimensions"]["horizon"]): row
                 for row in result["arms"]}
    assert len(summaries) == 4
    for horizon in (1, 2):
        row = summaries["baseline", horizon]
        assert row["metrics"]["error"] == 16.5 + 100 * (horizon - 1)
        assert row["independent_n"] == 2 and row["expected_cells"] == 4
    assert len(result["comparisons"]) == 2
    for comparison in result["comparisons"]:
        assert comparison["independent_n"] == 2
        assert comparison["metrics"]["error"]["candidate_minus_reference"] == -1
    table = list(csv.DictReader(io.StringIO(csv_bytes(result).decode())))
    assert {json.loads(row["comparison_dimensions"])["horizon"] for row in table} == {1, 2}
    claims = evidence_index(result, csv_bytes(result))["claims"]
    assert len({claim["claim_id"] for claim in claims}) == 4
    for claim in claims:
        horizon = claim["comparison_dimensions"]["horizon"]
        assert all(attempt.endswith(f"-h{horizon}") for attempt in claim["attempt_ids"])


def test_missing_and_failed_horizons_retain_separate_denominators():
    value = matrix()
    for row in value["cells"]:
        if row["comparison_dimensions"]["horizon"] == 2:
            row.update(status="MISSING", metrics=None, attempt_id=None, artifact_id=None)
    value["cells"][0].update(status="TIMEOUT", metrics=None)
    result = aggregate(seal(value))
    assert result["expected_cell_count"] == 16 and result["successful_cell_count"] == 7
    for row in result["arms"]:
        assert row["expected_cells"] == 4
        if row["comparison_dimensions"]["horizon"] == 2:
            assert row["independent_n"] == 0 and row["metrics"] == {}
            assert row["dispositions"] == {"MISSING": 4}
    pairs = {row["comparison_dimensions"]["horizon"]: row for row in result["comparisons"]}
    assert pairs[1]["independent_n"] == 1 and pairs[2]["independent_n"] == 0


def test_changed_dimension_is_rejected_even_with_resealed_bundle():
    value = matrix()
    value["cells"] = value["cells"][:8]
    value["expected_cells"] = value["expected_cells"][:8]
    # Avoid sharing the expected mapping so this changes only the disposition.
    value["cells"][0]["comparison_dimensions"] = {"horizon": 99, "region": "whole"}
    with pytest.raises(ValueError, match="identity|dimension"):
        aggregate(seal(value))


def test_true_duplicate_inside_one_stratum_remains_rejected():
    value = matrix()
    duplicate = copy.deepcopy(value["cells"][0])
    duplicate["cell_hash"] = fingerprint("different hash, identical statistical identity")
    value["cells"].append(duplicate)
    value["expected_cells"].append({key: duplicate[key] for key in
        ("cell_hash", "arm_id", "block_id", "seed", "comparison_dimensions")})
    with pytest.raises(ValueError, match="duplicate"):
        aggregate(seal(value))


def test_absent_arm_in_stratum_never_compares_across_horizons():
    value = matrix()
    value["cells"] = [row for row in value["cells"] if
                      row["arm_id"] == ("baseline" if row["comparison_dimensions"]["horizon"] == 1 else "candidate")]
    retained = {row["cell_hash"] for row in value["cells"]}
    value["expected_cells"] = [row for row in value["expected_cells"] if row["cell_hash"] in retained]
    result = aggregate(seal(value))
    assert len(result["comparisons"]) == 2
    assert all(row["independent_n"] == 0 and row["metrics"] == {} for row in result["comparisons"])
    assert all(len(row["absent_arms"]) == 1 for row in result["comparisons"])


def test_claim_sources_exclude_successes_in_incomplete_blocks():
    value = matrix()
    value["cells"][0].update(status="TIMEOUT", metrics=None)
    excluded = value["cells"][1]["attempt_id"]
    result = aggregate(seal(value))
    claims = evidence_index(result, csv_bytes(result))["claims"]
    assert all(excluded not in row["attempt_ids"] for row in claims)


@pytest.mark.parametrize("dimension", [None, [], {"seed": 2}])
def test_invalid_dimension_mapping_is_rejected(dimension):
    value = matrix()
    value["cells"][0]["comparison_dimensions"] = dimension
    value["expected_cells"][0]["comparison_dimensions"] = dimension
    with pytest.raises(ValueError, match="dimension"):
        aggregate(seal(value))


def test_registered_cell_prevents_resealed_dimension_omission():
    value = bundle()
    for row, expected in zip(value["cells"], value["expected_cells"]):
        registered = {key: row[key] for key in ("arm_id", "block_id", "seed")}
        registered["horizon"] = 1
        row["registered_cell"] = registered
        row["cell_hash"] = expected["cell_hash"] = fingerprint(registered)
        row["comparison_dimensions"] = {"horizon": 1}
        expected["comparison_dimensions"] = {"horizon": 1}
    aggregate(seal(value))
    value["cells"][0]["comparison_dimensions"] = {}
    value["expected_cells"][0]["comparison_dimensions"] = {}
    with pytest.raises(ValueError, match="registered cell dimension"):
        aggregate(seal(value))
