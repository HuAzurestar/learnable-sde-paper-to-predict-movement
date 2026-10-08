"""Verify an authorized MLMC admission export, not a statistical comparison."""

import argparse
import json
from pathlib import Path

if __package__:
    from .aggregate import validate_bundle
    from .admission import validate_admission
else:
    from aggregate import validate_bundle
    from admission import validate_admission


def validate(bundle, expected_hash):
    if (type(expected_hash) is not str or len(expected_hash) != 64
            or any(c not in "0123456789abcdef" for c in expected_hash) or bundle.get("bundle_hash") != expected_hash):
        raise ValueError("trusted expected bundle hash differs")
    validate_bundle(bundle, formal=False)
    successful = [row for row in bundle["cells"] if row["status"] == "SUCCEEDED"]
    if not successful:
        raise ValueError("no completed MLMC admission to verify")
    for row in successful:
        if row.get("qualification") != "qualified" or row.get("registered_cell", {}).get("plugin_id") != "affine-mlmc-production-chunk":
            raise ValueError("only qualified affine MLMC admission can be verified")
        validate_admission(bundle, row)
    return {"schema_version": "affine-mlmc-admission-verification-v1", "source_bundle_hash": expected_hash,
        "verified_mlmc_cells": len(successful), "expected_cells": len(bundle["expected_cells"]),
        "scope": "recorded-admission-only; no statistical adjudication, rigorous coverage or model qualification"}


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
