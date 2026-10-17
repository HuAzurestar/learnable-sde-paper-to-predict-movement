"""Check re-laid-out private maps against original annotations, without rescoring.

All case-level output remains in the explicit external local build directory.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_pirc17 import check_log
from scripts.check_pirc17_revision46_links import check as check_links


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def spans(page):
    return [s for b in page.get_text("dict")["blocks"]
            for line in b.get("lines", []) for s in line["spans"]]


def check(private, build):
    build = build.resolve()
    if build == ROOT or ROOT in build.parents:
        raise ValueError("Private build must remain outside the public repository")
    original = private / "figures/case-horizons.json"
    data = json.loads(original.read_text(encoding="utf-8"))
    receipt = json.loads((build / "local-build-manifest.json").read_text(encoding="utf-8"))
    layout = receipt["case_map_layout"]
    assert receipt["original_case_manifest_sha256"] == digest(original)
    assert layout["original_case_projection_sha256"] == digest(original)
    assert layout["renderer_sha256"] == digest(ROOT / "scripts/render_pirc17_local_maps_v2.py")
    assert data["seed"] == 20260814 and data["particles"] == 512
    assert len(data["cases"]) == 3 and data["reused_scientific_forecasts"] == 6
    assert not layout["public_distribution_authorized"] and receipt["local_review_only"]
    assert layout["new_fits_forecasts_scores_or_resampling"] == 0
    assert layout["particle_marks"] == 12288 and layout["display_source_reread"]
    checked_panels = checked_figures = 0
    for case in data["cases"]:
        models = {m["subject"]: m for m in case["models"]}
        label = case["label"] if case["label"] != "Zagan" else r"\.{Z}aga\'{n}"
        tail = " & ".join(
            f'{models["base"]["horizons"][i]["mean_error_m"]:.1f} / '
            f'{models["all-terrain"]["horizons"][i]["mean_error_m"]:.1f}' for i in range(4))
        for lang in ("en", "zh"):
            source = (build / "sources/paper/pirc17" / lang / "local-case-reading.tex").read_text(encoding="utf-8")
            assert label+" & "+tail+r"\\" in source
        for index, figure in enumerate(case["figures"]):
            path = build / "sources/paper/pirc17/figures" / figure["pdf"]
            assert digest(path) == layout["files_sha256"][path.name] == receipt["case_figure_sha256"][path.name]
            with fitz.open(path) as doc:
                assert len(doc) == 1
                text = doc[0].get_text()
                assert "512 saved particles / panel" in text and "hindsight only" in text
                assert "zoom changes across times" in text and "Forecast origin" in text
                for slot in (index*2, index*2+1):
                    assert f'({case["actual_scoring_seconds"][slot]:.0f} s)' in text
                    for model in models.values():
                        h = model["horizons"][slot]
                        annotation = f'Error {h["mean_error_m"]:.1f} m; R90 {h["radius_m"]:.1f} m'
                        assert annotation in text
                        assert annotation+'\nTarget '+('inside' if h['covered'] else 'OUTSIDE') in text
                        assert model["horizons"][-1]["mean_error_m"] == model["fde_m"]
                        checked_panels += 1
            checked_figures += 1
    documents = []
    for language in ("en", "zh"):
        for entry in ("main", "supplement", "audit-notes"):
            folder = build / "pdfs" / language
            check_log((folder / (entry+".log")).read_text(encoding="utf-8", errors="replace"))
        with fitz.open(build / "pdfs" / language / "main.pdf") as doc:
            map_pages = [p for p in doc if "512 saved particles / panel" in p.get_text()]
            assert len(map_pages) == 6
            # All labels in the embedded map are PDF text, not inferred from pixels.
            font_sizes = [s["size"] for p in map_pages for s in spans(p)
                          if any(key in s["text"] for key in ("512 saved", "WorldCover display", "R90", "hindsight only"))]
            assert font_sizes and min(font_sizes) >= 8.0
            documents.append({"language": language, "pages": len(doc), "map_pages": [p.number+1 for p in map_pages],
                              "minimum_checked_map_font_pt": min(font_sizes)})
    assert (checked_figures, checked_panels) == (6, 24)
    links = check_links(build / "pdfs")
    assert links["passed"]
    return {"schema_version": "pirc17-reader-v2-private-case-check", "passed": True,
            "original_case_manifest_sha256": digest(original), "matched_figures": 6,
            "matched_error_radius_coverage_annotations": 24, "particle_marks": 12288,
            "documents": documents, "companion_links": links, "new_scientific_execution": 0,
            "display_sources_reread_for_layout": True, "human_acceptance": False,
            "public_distribution_authorized": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-manuscript", type=Path, required=True)
    parser.add_argument("--local-build", type=Path, required=True)
    args = parser.parse_args()
    result = check(args.private_manuscript, args.local_build)
    (args.local_build / "reader-v2-case-check.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print({k: result[k] for k in ("passed", "matched_figures", "matched_error_radius_coverage_annotations", "documents")})
