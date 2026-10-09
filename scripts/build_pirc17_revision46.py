"""Build six independent review documents with source-graph provenance.

Only document compilation, never scientific execution or acceptance.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_pirc17 import check_log, validate_output


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_language(language, output):
    folder = ROOT / "paper/pirc17" / language
    destination = output / language
    destination.mkdir(parents=True)
    records = []
    for entry in ("main", "supplement", "audit-notes"):
        result = subprocess.run(["latexmk", "-pdf" if language == "en" else "-xelatex",
            "-interaction=nonstopmode", "-halt-on-error", "-file-line-error",
            "-outdir="+destination.as_posix(), entry+".tex"], cwd=folder,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (destination / (entry+"-command.txt")).write_bytes(result.stdout)
        if result.returncode:
            raise RuntimeError(f"{language}/{entry} compilation failed; see isolated build log")
        log = destination / (entry+".log")
        log_text = log.read_text(encoding="utf-8", errors="replace")
        check_log(log_text)
        pdf = destination / (entry+".pdf")
        if not pdf.read_bytes().startswith(b"%PDF-"):
            raise ValueError(f"Invalid PDF: {language}/{entry}")
        inputs = {}
        for line in (destination / (entry+".fls")).read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.startswith("INPUT "):
                continue
            path = Path(line[6:])
            path = (folder / path).resolve() if not path.is_absolute() else path.resolve()
            if ROOT in path.parents and path.is_file() and path.suffix in (".tex", ".pdf", ".png", ".json"):
                inputs[path.relative_to(ROOT).as_posix()] = digest(path)
        page_info = subprocess.check_output(["pdfinfo", str(pdf)], text=True, encoding="utf-8", errors="replace")
        pages = int(re.search(r"^Pages:\s+(\d+)", page_info, re.M).group(1))
        records.append({"language": language, "entry": entry, "pages": pages,
            "source_graph_sha256": inputs, "pdf": pdf.relative_to(output).as_posix(),
            "pdf_sha256": digest(pdf), "log_sha256": digest(log), "strict_log_passed": True})
    return records


def build(output):
    output = validate_output(output, ROOT)
    subprocess.run([sys.executable, str(ROOT / "scripts/check_public_release.py")], cwd=ROOT, check=True)
    source_start = {p.relative_to(ROOT).as_posix(): digest(p)
                    for p in (ROOT / "paper/pirc17").rglob("*")
                    if p.is_file() and p.suffix in (".tex", ".json", ".pdf", ".png", ".svg", ".csv")}
    output.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        records = list(pool.map(lambda lang: compile_language(lang, output), ("en", "zh")))
    if any(digest(ROOT / name) != value for name,value in source_start.items()):
        raise ValueError("Source changed while building; no stable manifest issued")
    result = {"schema_version": "pirc17-reader-six-document-build-v1",
              "repository_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "working_tree_dirty_at_start": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)),
              "manuscripts": [record for group in records for record in group],
              "empirical_claims_verified_by_build": False, "human_acceptance": False,
              "new_fits_forecasts_or_resampling": 0}
    (output / "build-manifest.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    result = build(parser.parse_args().output_dir)
    print(json.dumps({r["language"]+"/"+r["entry"]: r["pages"] for r in result["manuscripts"]}))
