"""Verify an authorized cubature export, not a statistical or model verdict."""

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
            or any(c not in "0123456789abcdef" for c in expected_hash)
            or bundle.get("bundle_hash") != expected_hash):
        raise ValueError("trusted expected bundle hash differs")
    validate_bundle(bundle, formal=False)
    successful = [row for row in bundle["cells"] if row["status"] == "SUCCEEDED"]
    if not successful:
        raise ValueError("no completed cubature admission to verify")
    for row in successful:
        if row.get("qualification") != "qualified" or row.get("registered_cell", {}).get("plugin_id") != "affine-cubature":
            raise ValueError("only qualified affine cubature admission can be verified")
        validate_admission(bundle, row)
    return {"schema_version": "affine-cubature-admission-verification-v1", "source_bundle_hash": expected_hash,
        "verified_cubature_cells": len(successful), "expected_cells": len(bundle["expected_cells"]),
        "scope": "recorded-admission-only; no statistical adjudication or model qualification"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--expected-hash", required=True)
    args = parser.parse_args()
    with args.bundle.open("rb") as stream:
        content = stream.read(64*1024*1024+1)
    if len(content) > 64*1024*1024:
        raise ValueError("authorized bundle exceeds byte quota")
    result = validate(json.loads(content), args.expected_hash)
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False))


if __name__ == "__main__":
    main()
