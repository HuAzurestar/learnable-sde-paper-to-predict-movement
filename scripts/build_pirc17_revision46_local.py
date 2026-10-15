"""Assemble the revised local manuscript with the existing six real-case maps.

Explicit private-source/output arguments; never loads a case in a public build.
No maps are downloaded, rerendered, rescored or published by this command.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_pirc17 import check_log, validate_output
from scripts.pirc17_display_names import tex_display


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assemble(private, output, case_figures=None):
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
    map_layout = None
    figure_source = private / "figures"
    if case_figures is not None:
        figure_source = case_figures.resolve()
        if ROOT == figure_source or ROOT in figure_source.parents:
            raise ValueError("Revised private maps must remain outside the public repository")
        map_layout = json.loads((figure_source / "map-layout-manifest.json").read_text(encoding="utf-8"))
        if (map_layout["original_case_projection_sha256"] != digest(cases_path)
                or map_layout["public_distribution_authorized"]
                or map_layout["new_fits_forecasts_scores_or_resampling"] != 0):
            raise ValueError("Revised map layout is not bound to the original cases")
    for path in sorted(figure_source.glob("case-*.pdf")):
        if map_layout is not None and digest(path) != map_layout["files_sha256"][path.name]:
            raise ValueError("Revised map bytes differ from their receipt")
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
        original_chapter_sha = hashlib.sha256(case_chapter.encode()).hexdigest()
        # Apply the same current names to owner-only text, without changing
        # source case records, map bytes, metric values or protected TeX labels.
        case_chapter = tex_display(case_chapter)
        if map_layout is not None:
            case_chapter = revise_case_captions(case_chapter, language)
        guide = (
            "\\paragraph{Cross-horizon reading guide.} First compare the four mean-error columns, then the corresponding maps. The first-target all-terrain mean is farther in all three cases; final means are closer in all three. Boechout and Bakewell have worse middle-target mean error, whereas the third case reverses after its first target. These are six fixed-seed forecasts, not a population frequency or terrain-benefit test. Compare base/all-terrain within a matched time; panel zoom varies across times and neither means nor four marginal clouds form a saved continuous prediction route.\n"
            if language == "en" else
            "\\paragraph{跨时域阅读顺序。}先读四列均值误差，再查对应地图。三例全地形首目标均值都更远，末目标都更近；Boechout、Bakewell的中间目标也更差，第三例则在首目标后反转。这是六份固定种子预测，不估计总体频率或地形收益。先在同目标时刻比较base与全地形，再关注跨时域放大尺度；均值及四份边际位置云都不是保存的连续预测路线。\n")
        (source / language / "local-case-reading.tex").write_text(guide+case_chapter, encoding="utf-8")
        main = (source / language / "main.tex").read_text(encoding="utf-8")
        # Keep the diagnostic argument uninterrupted. Existing private maps
        # form a local appendix; no new map or case is generated or published.
        # The public privacy anchor moves to the actual local case chapter.
        main = main.replace(r"\label{sec:case-horizons}\hypertarget{sec:case-horizons}{}", "", 1)
        appendix_title = "Local illustrative cases (not for redistribution)" if language == "en" else "本地解释性案例（不得再分发）"
        appendix = "\n\\clearpage\n\\appendix\n\\section{"+appendix_title+"}\n\\input{local-case-reading.tex}\n"
        main = main.replace(r"\input{revision46-bibliography.tex}", r"\input{revision46-bibliography.tex}"+appendix)
        (source / language / "main.tex").write_text(main, encoding="utf-8")
        preamble = source / language / "revision46-preamble.tex"
        text = preamble.read_text(encoding="utf-8")
        text = text.replace("Public review revision", "Local full review; not for public redistribution")
        text = text.replace("公开审阅修订稿", "本地完整审阅稿；不得公开再分发")
        preamble.write_text(text, encoding="utf-8")
        records.append({"language": language, "current_body_sha256": digest(source / language / "main.tex"),
                        "original_private_case_chapter_sha256": original_chapter_sha,
                        "displayed_case_chapter_sha256": hashlib.sha256(case_chapter.encode()).hexdigest(),
                        "display_name_policy": "reader-v9; original identifiers retained in source/audit only",
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
    if map_layout is not None:
        manifest["case_map_layout"] = map_layout
    (output / "local-build-manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    return manifest


def revise_case_captions(chapter, language):
    """Keep six cases/tables; put scale and interpretation beside each map."""
    notes = ([
        "Case A, early targets: all-terrain's mean is farther at both times, although each target remains inside its disk.",
        "Case A, late targets: the middle mean is farther and final mean closer; all four marginal ES values are worse. Disk inclusion does not establish movement along the route.",
        "Case B, early targets: the mean is farther with all-terrain while inclusion is retained. Showing the same background in both columns does not mean base queries maps.",
        "Case B, late targets: both models miss the target at both times. The final mean improves with all-terrain but both final disks still fail to contain the target.",
        "Case C, early targets: all-terrain worsens the first mean error and improves the second. The reversal does not identify a causal terrain mechanism.",
        "Case C, late targets: the 15-minute target changes from outside base to inside all-terrain with a larger radius; both final disks still miss the target."
    ] if language == "en" else [
        "案例A早期：全地形两个时刻均值都更远，但各目标仍在对应圆内。",
        "案例A长时：中间均值更远、终点更近，四时刻边际ES却均更差。圆包含不证明均值沿路线移动。",
        "案例B早期：全地形均值更远仍可包含目标；两列相同底图不表示base查询地图。",
        "案例B长时：两个时刻、两个模型均漏覆盖。全地形终点均值改善，但两个末时圆仍不包含目标。",
        "案例C早期：全地形首目标更差、第二目标反转，不能从反转识别地形机制。",
        "案例C长时：15分钟由base圆外变为全地形圆内，伴随半径增大；30分钟两者仍漏覆盖。"
    ])
    scale = (" Left: base; right: all-terrain. Metric axes match within each row; scale changes between times. Shared legends identify the green origin star and hindsight-only future observations. Local review only."
             if language == "en" else " 左base、右全地形；同行米制坐标范围一致，跨时刻尺度改变。共享图例解释绿色起点星形、仅供事后参考的未来观测；仅供本地审阅。")
    figures = list(re.finditer(r"\\begin\{figure\}.*?\\end\{figure\}", chapter, re.S))
    if len(figures) != 6:
        raise ValueError("Expected all six original map figures")
    for match, note in reversed(list(zip(figures, notes))):
        block = match.group()
        start, stop = block.index(r"\caption{"), block.index(r"\label{")
        block = block[:start]+"\\caption{"+note+scale+"}\n"+block[stop:]
        block = block.replace(r"height=.78\textheight", r"height=.80\textheight")
        chapter = chapter[:match.start()]+block+chapter[match.end():]
    rounding = ("\\paragraph{Displayed rounding.} Case differences use the unrounded saved values. Subtracting the two rounded table entries can differ by 0.01 m. Original core-time ratios are single saved trials, not deployment-cost estimates.\n"
                if language == "en" else "\\paragraph{显示舍入。}案例差值按未舍入保存值计算，相减已舍入表格数可能差0.01米。原核心耗时比只对应单次保存计时，不估计部署成本。\n")
    return rounding+chapter


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-manuscript", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--case-figures", type=Path, help="External v2 map layout with original-case binding")
    args = parser.parse_args()
    value = assemble(args.private_manuscript, args.output_dir, args.case_figures)
    print("Six local documents built; six original maps in each body; not uploaded or accepted.")
