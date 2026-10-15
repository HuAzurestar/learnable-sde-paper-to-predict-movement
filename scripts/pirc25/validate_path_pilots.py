"""Verify owner-saved path pilot PASS/FAIL reports, never promote admissions."""
import argparse
import json
from pathlib import Path

if __package__:
    from .aggregate import validate_bundle
    from .path_pilots import validate_path_pilot
    from .analytic_qualification import fingerprint
else:
    from aggregate import validate_bundle
    from path_pilots import validate_path_pilot
    from analytic_qualification import fingerprint


def validate(bundle, expected_hash):
    if (type(expected_hash) is not str or len(expected_hash) != 64
            or any(c not in "0123456789abcdef" for c in expected_hash) or bundle.get("bundle_hash") != expected_hash):
        raise ValueError("trusted expected bundle hash differs")
    validate_bundle(bundle, formal=False)
    spec = bundle.get("registered_spec")
    if (type(spec) is not dict or fingerprint(spec) != bundle["spec_hash"]
            or any(spec[k] != bundle[k] for k in ("study_id", "code_hash", "protocol_hash", "data_hash"))
            or len({fingerprint(c) for c in spec["cells"]}) != len(spec["cells"])
            or {fingerprint(c) for c in spec["cells"]} != {r["cell_hash"] for r in bundle["cells"]}
            or any(r.get("registered_cell") not in spec["cells"] for r in bundle["cells"])):
        raise ValueError("complete frozen pilot source matrix required; no clipped cells")
    if bundle.get("path_pilot_evidence") != "owned-saved-path-pilot-results-and-native-execution-v1":
        raise ValueError("explicit full saved pilot export required; legacy scalar export is insufficient")
    if any(row.get("registered_cell", {}).get("plugin_id") != "affine-path-qualification" for row in bundle["cells"]):
        raise ValueError("complete registered path-pilot matrix required")
    counts = {"PASSED": 0, "FAILED": 0}
    for row in bundle["cells"]:
        if row["status"] == "SUCCEEDED":
            if row["admission"]["spec"] != bundle["registered_spec"]:
                raise ValueError("pilot source spec differs from whole matrix")
            counts[validate_path_pilot(row["admission"], row)] += 1
    return {"schema_version": "saved-path-pilot-verification-v1", "source_bundle_hash": expected_hash,
        "verified_pilot_cells": sum(counts.values()), "passed_cells": counts["PASSED"], "failed_cells": counts["FAILED"],
        "expected_cells": len(bundle["expected_cells"]), "noncompleted_rows": len(bundle["cells"])-sum(counts.values()),
        "scientific_qualification": False,
        "scope": "recorded-pilot-and-saved-classification-only; no production admission, distribution guarantee or statistical adjudication"}


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
