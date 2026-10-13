"""Inspect a trusted complete calibrated export, not a statistical decision."""

import argparse
import json
from pathlib import Path

if __package__:
    from .aggregate import validate_bundle
    from .admission import validate_admission
    from .calibrated_study import validate_calibration_table
    from .validate_calibration import load_document
else:
    from aggregate import validate_bundle
    from admission import validate_admission
    from calibrated_study import validate_calibration_table
    from validate_calibration import load_document


def validate(bundle, expected_hash):
    if (type(expected_hash) is not str or len(expected_hash) != 64
            or any(c not in "0123456789abcdef" for c in expected_hash)
            or bundle.get("bundle_hash") != expected_hash):
        raise ValueError("trusted expected calibrated bundle hash differs")
    rows = validate_bundle(bundle, formal=False)
    cost = validate_calibration_table(bundle)
    if cost is None:
        raise ValueError("complete calibrated export required")
    for row in rows.values():
        if row["status"] == "SUCCEEDED" and row["qualification"] == "qualified":
            validate_admission(bundle, row)
    return {"schema_version": "calibrated-study-inspection-v1", "source_bundle_hash": expected_hash,
        "expected_cells": len(rows), "calibration_slots": len(bundle["probability_calibration"]["slots"]),
        "cost": cost, "formal_comparison": False,
        "scope": "complete recorded preparation/matrix transport; no statistical adjudication or model qualification"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--expected-hash", required=True)
    args = parser.parse_args()
    with args.bundle.open("rb") as stream:
        content = stream.read(64*1024*1024+1)
    print(json.dumps(validate(load_document(content), args.expected_hash), sort_keys=True, separators=(",", ":"), allow_nan=False))


if __name__ == "__main__":
    main()
