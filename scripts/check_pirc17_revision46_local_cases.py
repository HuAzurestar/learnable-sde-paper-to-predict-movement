"""Verify the original local-only six maps and 24 mean errors without rescoring."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.check_pirc17_revision46_links import check as check_links


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(private, build):
    original = private / "figures/case-horizons.json"
    data = json.loads(original.read_text(encoding="utf-8"))
    receipt = json.loads((build / "local-build-manifest.json").read_text(encoding="utf-8"))
    assert receipt["original_case_manifest_sha256"] == digest(original)
    assert data["seed"] == 20260814 and data["particles"] == 512
    assert len(data["cases"]) == 3 and data["reused_scientific_forecasts"] == 6
    assert data["public_distribution_authorized"] is False and receipt["local_review_only"]
    assert receipt["new_fits_forecasts_scores_map_queries_or_resampling"] == 0
    checked_errors = checked_figures = 0
    for case in data["cases"]:
        # The original table has one case row, with base/all-terrain pairs
        # in each time column, rather than a separate row for each model.
        models = {m["subject"]: m for m in case["models"]}
        assert set(models) == {"base", "all-terrain"}
        label = case["label"] if case["label"] != "Zagan" else r"\.{Z}aga\'{n}"
        tail = " & ".join(
            f'{models["base"]["horizons"][i]["mean_error_m"]:.1f} / '
            f'{models["all-terrain"]["horizons"][i]["mean_error_m"]:.1f}'
            for i in range(4))
        for lang in ("en", "zh"):
            source = (build / "sources/paper/pirc17" / lang / "local-case-reading.tex").read_text(encoding="utf-8")
            assert label+" & "+tail+r"\\" in source
        for model in case["models"]:
            assert model["status"] == "success" and len(model["horizons"]) == 4
            errors = [h["mean_error_m"] for h in model["horizons"]]
            assert errors[-1] == model["fde_m"]
            checked_errors += len(errors)
        for index, figure in enumerate(case["figures"]):
            path = build / "sources/paper/pirc17/figures" / figure["pdf"]
            assert digest(path) == figure["pdf_sha256"] == digest(private / "figures" / figure["pdf"])
            with fitz.open(path) as doc:
                assert len(doc) == 1
                text = doc[0].get_text()
                assert text.count("512 predicted positions") == 4 and "No predicted trajectory" in text
                for slot in (index*2, index*2+1):
                    assert f'actual {case["actual_scoring_seconds"][slot]:.0f} s' in text
                    for model in case["models"]:
                        assert f'Mean error={model["horizons"][slot]["mean_error_m"]:.1f} m' in text
            checked_figures += 1
    assert checked_errors == 24 and checked_figures == 6
    links = check_links(build / "pdfs")
    assert links["passed"]
    return {"schema_version": "pirc17-revision46-local-case-check-v1",
        "original_case_manifest_sha256": digest(original), "matched_mean_errors": checked_errors,
        "matched_original_map_pdfs": checked_figures, "companion_links": links,
        "new_scientific_execution": 0, "public_distribution_authorized": False,
        "human_accepted": False, "passed": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-manuscript", type=Path, required=True)
    parser.add_argument("--local-build", type=Path, required=True)
    args = parser.parse_args()
    result = check(args.private_manuscript, args.local_build)
    (args.local_build / "case-check.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print("Verified six unchanged local maps,24 original mean errors,and all companion links;not published or accepted.")
