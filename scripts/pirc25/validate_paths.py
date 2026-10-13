"""Verify saved path/IS admissions and report honest current pass/fail counts."""

import argparse
import json
from pathlib import Path

if __package__:
    from .aggregate import validate_bundle
    from .admission import validate_admission
    from .path_qualification import PLUGIN_ID, validate_path_qualification
else:
    from aggregate import validate_bundle
    from admission import validate_admission
    from path_qualification import PLUGIN_ID, validate_path_qualification


def validate(bundle, expected_hash):
    if (type(expected_hash) is not str or len(expected_hash) != 64
            or any(c not in "0123456789abcdef" for c in expected_hash) or bundle.get("bundle_hash") != expected_hash):
        raise ValueError("trusted expected bundle hash differs")
    validate_bundle(bundle, formal=False)
    completed = [row for row in bundle["cells"] if row["status"] == "SUCCEEDED"]
    if not completed:
        raise ValueError("no completed path admission to verify")
    counts = {"PASSED": 0, "FAILED": 0}
    for row in completed:
        if row.get("qualification") != "qualified" or row.get("registered_cell", {}).get("plugin_id") != PLUGIN_ID:
            raise ValueError("only owner-admitted independent path targets can be verified")
        validate_admission(bundle, row)
        counts[validate_path_qualification(row["admission"], row)] += 1
    return {"schema_version": "affine-path-admission-verification-v1", "source_bundle_hash": expected_hash,
        "verified_path_cells": len(completed), "current_passed_cells": counts["PASSED"], "current_failed_cells": counts["FAILED"],
        "expected_cells": len(bundle["expected_cells"]), "noncompleted_rows": len(bundle["cells"])-len(completed),
        "scope": "recorded-admission-and-saved-current-classification-only; no statistical adjudication, full-distribution or scientific model qualification"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--expected-hash", required=True)
    args = parser.parse_args()
    with args.bundle.open("rb") as stream:
        content = stream.read(64*1024*1024+1)
    if len(content) > 64*1024*1024:
        raise ValueError("authorized bundle exceeds byte quota")
    print(json.dumps(validate(json.loads(content), args.expected_hash), sort_keys=True, separators=(",", ":"), allow_nan=False))


if __name__ == "__main__":
    main()
