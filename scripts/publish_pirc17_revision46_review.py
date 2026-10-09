"""Copy a verified public six-document build to a new versioned PR attachment.

Never handles the separate local-case build or overwrites historical PDFs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.build_pirc17 import check_log
from scripts.check_pirc17_revision46_links import check


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def publish(build):
    manifest = json.loads((build/"build-manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "pirc17-reader-six-document-build-v1"
    assert manifest["new_fits_forecasts_or_resampling"] == 0
    assert len(manifest["manuscripts"]) == 6
    assert {(r["language"],r["entry"]) for r in manifest["manuscripts"]} == {
        (lang,entry) for lang in ("en","zh") for entry in ("main","supplement","audit-notes")}
    destination = ROOT/"paper/pirc17/revision46-review-v1"
    if destination.exists():
        raise ValueError("Versioned review already exists; use a new reviewed version,never overwrite")
    subprocess.run([sys.executable,str(ROOT/"scripts/check_public_release.py")],cwd=ROOT,check=True)
    assert check(build)["passed"]
    for row in manifest["manuscripts"]:
        assert row["strict_log_passed"]
        assert digest(build/row["pdf"]) == row["pdf_sha256"]
        log = build/row["language"]/(row["entry"]+".log")
        assert digest(log) == row["log_sha256"]
        check_log(log.read_text(encoding="utf-8",errors="replace"))
        for name,sha in row["source_graph_sha256"].items():
            path = (ROOT/name).resolve()
            assert ROOT in path.parents and digest(path) == sha
            assert "case-" not in name and "local-case" not in name
    destination.mkdir()
    for row in manifest["manuscripts"]:
        folder = destination/row["language"]
        folder.mkdir(exist_ok=True)
        shutil.copyfile(build/row["pdf"],folder/(row["entry"]+".pdf"))
    manifest.update(publication_scope="public sources and aggregate figures only;local maps excluded",
                    prior_review_pdfs_and_bindings_overwritten=False,
                    human_acceptance=False,authorship_verified=False)
    (destination/"build-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    assert check(destination)["passed"]
    print("Six versioned public PDFs copied; all source hashes, strict logs and companion links checked.")


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir",type=Path,required=True)
    publish(parser.parse_args().build_dir)
