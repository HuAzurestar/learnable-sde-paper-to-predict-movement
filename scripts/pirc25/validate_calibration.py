"""Inspect trusted saved calibration proofs; this is not an export command.

Only the isolated producer's saved proof is consumed. No formal matrix,
method qualification, export authorization or statistical claim is created.
"""

import argparse
import json
from pathlib import Path

if __package__:
    from .analytic_qualification import bounded, fingerprint
    from .probability_calibration import validate_saved_calibration, summarize_calibration_sources
else:
    from analytic_qualification import bounded, fingerprint
    from probability_calibration import validate_saved_calibration, summarize_calibration_sources


def validate(document, expected_hash):
    bounded(document, 64*1024*1024, nodes=1000000, depth_limit=32, string_limit=16384)
    if (type(expected_hash) is not str or len(expected_hash) != 64
            or any(c not in "0123456789abcdef" for c in expected_hash)
            or fingerprint(document) != expected_hash):
        raise ValueError("trusted expected calibration inspection hash differs")
    if (type(document) is not dict or set(document) != {"schema_version", "consumer_study_id", "sources"}
            or document["schema_version"] != "saved-calibration-inspection-v1"
            or type(document["consumer_study_id"]) is not str or not 0 < len(document["consumer_study_id"]) <= 128
            or type(document["sources"]) is not list or not 0 < len(document["sources"]) <= 10000):
        raise ValueError("complete bounded calibration inspection input required")
    verified = []
    for source in document["sources"]:
        if type(source) is not dict or set(source) != {"evidence", "pointer"}:
            raise ValueError("explicit calibration evidence and pointer required")
        verified.append(validate_saved_calibration(source["evidence"], source["pointer"],
            consumer_study_id=document["consumer_study_id"]))
    return {"schema_version": "saved-calibration-inspection-result-v1", "source_hash": expected_hash,
        "verified_references": len(verified), "cost": summarize_calibration_sources(verified),
        "scientific_qualification": False, "method_qualification": False,
        "scope": "recorded preparation only; no export authorization, admission, statistical adjudication or model qualification"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path)
    parser.add_argument("--expected-hash", required=True)
    args = parser.parse_args()
    with args.document.open("rb") as stream:
        content = stream.read(64*1024*1024+1)
    if len(content) > 64*1024*1024:
        raise ValueError("calibration inspection exceeds byte quota")
    print(json.dumps(validate(json.loads(content), args.expected_hash), sort_keys=True, separators=(",", ":"), allow_nan=False))


if __name__ == "__main__":
    main()
