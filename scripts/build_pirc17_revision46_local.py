"""Assemble the revised local manuscript with the existing six real-case maps.

Explicit private-source/output arguments; never loads a case in a public build.
No maps are downloaded, rerendered, rescored or published by this command.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_pirc17 import check_log, validate_output


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assemble(private, output):
    output = validate_output(output, ROOT)
    if private.resolve() == (ROOT / "paper/pirc17").resolve():
        raise ValueError("An actual owner-controlled private manuscript is required")
    cases_path = private / "figures/case-horizons.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    if (cases["seed"] != 20260814 or cases["particles"] != 512 or cases["selected_cases"] != 3
            or cases["reused_scientific_forecasts"] != 6
            or any(cases[name] != 0 for name in ("new_forecasts", "new_fits", "new_particle_scores", "new_inference_tests"))):
        raise ValueError("Only the original three cases/six predictions may be reused")
    output.mkdir(parents=True, exist_ok=True)
    source = output / "sources/paper/pirc17"
    source.mkdir(parents=True)
    public = ROOT / "paper/pirc17"
    # Copy document/figure assets, not raw outputs or checkpoints.
    for path in public.rglob("*"):
        if path.is_file() and (path.suffix == ".tex" or (path.suffix == ".pdf" and "figures" in path.parts)):
            destination = source / path.relative_to(public)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
    case_bindings = {}
    for path in sorted((private / "figures").glob("case-*.pdf")):
        case_bindings[path.name] = digest(path)
        shutil.copyfile(path, source / "figures" / path.name)
    if len(case_bindings) != 6:
        raise ValueError("Exactly six original paired horizon figures required")
    records = []
    for language in ("en", "zh"):
        old = (private / language / "main.tex").read_text(encoding="utf-8")
        label = old.index(r"\label{sec:case-horizons}")
        begin = old.rfind(r"\subsection", 0, label)
        end = old.index(r"\section", label)
        case_chapter = old[begin:end]
        if case_chapter.count(r"\includegraphics") != 6:
            raise ValueError("All original maps and captions must be retained")
        guide = (
            "\\paragraph{Cross-horizon reading guide.} First compare the four mean-error columns, then the corresponding maps. The first-target all-terrain mean is farther in all three cases; final means are closer in all three. Boechout and Bakewell have worse middle-target mean error, whereas the third case reverses after its first target. These are six fixed-seed forecasts, not a population frequency or terrain-benefit test. Compare base/all-terrain within a matched time; panel zoom varies across times and neither means nor four marginal clouds form a saved continuous prediction route.\n"
            if language == "en" else
            "\\paragraph{跨时域阅读顺序。}先读四列均值误差，再查对应地图。三例全地形首目标均值都更远，末目标都更近；Boechout、Bakewell的中间目标也更差，第三例则在首目标后反转。这是六份固定种子预测，不估计总体频率或地形收益。先在同目标时刻比较base与全地形，再关注跨时域放大尺度；均值及四份边际位置云都不是保存的连续预测路线。\n")
        (source / language / "local-case-reading.tex").write_text(guide+case_chapter, encoding="utf-8")
        main = (source / language / "main.tex").read_text(encoding="utf-8")
        start = main.index(r"\subsection{Real-route illustrations" if language == "en" else r"\subsection{真实路线案例")
        stop = main.index("Future work should" if language == "en" else "后续应以", start)
        main = main[:start]+r"\input{local-case-reading.tex}"+"\n\n"+main[stop:]
        (source / language / "main.tex").write_text(main, encoding="utf-8")
        preamble = source / language / "revision46-preamble.tex"
        text = preamble.read_text(encoding="utf-8")
        text = text.replace("Public review revision", "Local full review; not for public redistribution")
        text = text.replace("公开审阅修订稿", "本地完整审阅稿；不得公开再分发")
        preamble.write_text(text, encoding="utf-8")
        records.append({"language": language, "current_body_sha256": digest(source / language / "main.tex"),
                        "original_private_case_chapter_sha256": hashlib.sha256(case_chapter.encode()).hexdigest(),
                        "retained_case_figures": 6, "new_cross_horizon_reading_guide": True})
    def compile_one(language):
        destination = output / "pdfs" / language
        destination.mkdir(parents=True)
        pdf_records = []
        for entry in ("main", "supplement", "audit-notes"):
            result = subprocess.run(["latexmk", "-pdf" if language == "en" else "-xelatex",
                "-interaction=nonstopmode", "-halt-on-error", "-file-line-error",
                "-outdir="+destination.as_posix(), entry+".tex"], cwd=source / language,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            (destination / (entry+"-command.txt")).write_bytes(result.stdout)
            if result.returncode:
                raise RuntimeError("Local "+language+"/"+entry+" build failed; isolated log retained")
            check_log((destination / (entry+".log")).read_text(encoding="utf-8", errors="replace"))
            pdf_records.append({"entry": entry, "pdf_sha256": digest(destination / (entry+".pdf"))})
        return {"language": language, "documents": pdf_records}
    with ThreadPoolExecutor(max_workers=2) as pool:
        pdfs = list(pool.map(compile_one, ("en", "zh")))
    manifest = {"schema_version": "pirc17-local-revised-case-manuscript-v1",
        "original_case_manifest_sha256": digest(cases_path), "case_figure_sha256": case_bindings,
        "documents": records, "pdfs": pdfs, "new_fits_forecasts_scores_map_queries_or_resampling": 0,
        "public_distribution_authorized": cases["public_distribution_authorized"],
        "human_accepted": False, "local_review_only": True}
    (output / "local-build-manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-manuscript", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    value = assemble(args.private_manuscript, args.output_dir)
    print("Six local documents built; six original maps in each body; not uploaded or accepted.")
