"""Build current bilingual PIRC-17 review PDFs, not historical release PDFs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINES = {"en": "-pdf", "zh": "-xelatex"}
LOG_ERRORS = re.compile(
    r"Undefined (?:references|citations)|There were undefined|"
    r"(?:Reference|Citation) .+ undefined|Rerun to get|Missing character:|"
    r"Overfull \\[hv]box",
    re.IGNORECASE,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_log(text: str) -> None:
    problems = [line for line in text.splitlines() if LOG_ERRORS.search(line)]
    if problems:
        raise ValueError("Unresolved or clipped manuscript output:\n" + "\n".join(problems))


def validate_output(output: Path, root: Path) -> Path:
    output = output.resolve()
    paper = (root / "paper").resolve()
    # Do not overwrite committed review PDFs or the historical release sources.
    if output == paper or paper in output.parents or output in paper.parents:
        raise ValueError("Choose a separate build directory outside paper/")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Choose a new empty build directory; previous evidence is retained")
    return output


def build(output: Path, root: Path = ROOT) -> dict:
    output = validate_output(output, root)
    # Public-boundary policy is checked before TeX loads repository sources.
    subprocess.run(
        [sys.executable, str(root / "scripts/check_public_release.py")], cwd=root, check=True
    )
    ledger_path = root / "paper/pirc17/claim-ledger.json"
    ledger_hash = digest(ledger_path)
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True))
    manuscripts = []
    source_hashes = {
        language: digest(root / "paper/pirc17" / language / "main.tex")
        for language in ENGINES
    }
    output.mkdir(parents=True, exist_ok=True)
    for language, engine in ENGINES.items():
        source = root / "paper/pirc17" / language / "main.tex"
        source_hash = source_hashes[language]
        destination = output / language
        destination.mkdir()
        subprocess.run(
            ["latexmk", engine, "-interaction=nonstopmode", "-halt-on-error",
             "-file-line-error", "-outdir=" + destination.as_posix(), "main.tex"],
            cwd=source.parent, check=True,
        )
        log = destination / "main.log"
        log_text = log.read_text(encoding="utf-8", errors="replace")
        check_log(log_text)
        pdf = destination / "main.pdf"
        if not pdf.read_bytes().startswith(b"%PDF-"):
            raise ValueError("Missing or invalid PDF for " + language)
        if digest(source) != source_hash or digest(ledger_path) != ledger_hash:
            raise ValueError("Manuscript input changed during build; rebuild a stable revision")
        manuscripts.append({
            "language": language, "engine": engine,
            "source": source.relative_to(root).as_posix(), "source_sha256": source_hash,
            "pdf": pdf.relative_to(output).as_posix(), "pdf_sha256": digest(pdf),
            "log": log.relative_to(output).as_posix(), "log_sha256": digest(log),
            "tex_banner": log_text.splitlines()[0] if log_text else "",
        })
    if any(digest(root / "paper/pirc17" / language / "main.tex") != expected
           for language, expected in source_hashes.items()):
        raise ValueError("Bilingual sources changed during build; rebuild a stable revision")
    manifest = {
        "schema_version": "pirc17-review-build-v1", "repository_head": head,
        "working_tree_dirty_at_start": dirty, "claim_ledger_sha256": ledger_hash,
        "manuscripts": manuscripts, "compilation_verified": True,
        "empirical_claims_verified_by_build": False, "acceptance_verified_by_build": False,
        "ledger_declared_empirical_integration": ledger["final_empirical_results_integrated"],
        "ledger_declared_human_acceptance": ledger["human_accepted"],
    }
    (output / "build-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    build(args.output_dir)
    print("Both current PIRC-17 review PDFs built; evidence manifest saved. Not scientific acceptance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
