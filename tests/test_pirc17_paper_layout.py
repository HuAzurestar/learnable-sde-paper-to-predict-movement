"""One reading entry; paper-only archival must not move data or image assets."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

from scripts.pirc17_paper_paths import PAPER, ROOT, paper_entries, paper_path

BASE = "c94bf363d9eaf600d02056ec2a148086eccfd8a8"


def is_paper_artifact(relative):
    if re.fullmatch(r"revision46-review-v(?:[1-9]|10)/(?:build-manifest\.json|(?:en|zh)/(?:main|supplement|audit-notes)\.pdf)", relative):
        return True
    if relative in {"en/public-review.pdf", "zh/public-review.pdf"}:
        return True
    if "/" in relative:
        return False
    return (relative in {"PUBLIC_REVIEW.md", "reader-v10-editorial-record.md", "review-current-v2.md", "tex-archive-review.md", "review-response-v1.json"}
            or bool(re.fullmatch(r"reader-v\d+-(?:editorial-record|regression-check|score-binding|public-source-binding)\.json", relative))
            or bool(re.fullmatch(r"revision46-(?:reference-check-v1|regression-check-v1|response-v[123]|source-migration|test-migration)\.json", relative))
            or (relative.startswith("public-review-") and relative.endswith(".json")))


def test_all_107_paper_moves_are_exact_and_cannot_include_scientific_assets():
    entries = paper_entries()
    assert len(entries) == 107
    for old, (new, sha) in entries.items():
        assert is_paper_artifact(old), old
        assert not (PAPER / old).exists()
        assert new.startswith("archive/")
        assert paper_path(PAPER / old) == PAPER / new
        assert hashlib.sha256((PAPER / new).read_bytes()).hexdigest() == sha


def test_single_current_release_has_exact_last_delivered_pdf_bytes():
    manifest = json.loads((PAPER / "current/build-manifest.json").read_text())
    assert len(manifest["manuscripts"]) == 6
    for row in manifest["manuscripts"]:
        current = PAPER / "current" / row["pdf"]
        assert hashlib.sha256(current.read_bytes()).hexdigest() == row["pdf_sha256"]
        assert current.read_bytes() == (PAPER / "archive/paper-versions/v10" / row["pdf"]).read_bytes()
    for language in ("en", "zh"):
        assert not (PAPER / language / "public-review.pdf").exists()
    assert not list(PAPER.glob("revision46-review-*"))


def test_all_original_data_and_image_paths_remain_untouched():
    originals = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASE, "paper/pirc17"], cwd=ROOT, text=True).splitlines()
    changed = set(subprocess.check_output(["git", "diff", BASE, "--name-only", "--", "paper/pirc17"], cwd=ROOT, text=True).splitlines())
    moved = {"paper/pirc17/" + x for x in paper_entries()}
    protected = {p for p in originals if p not in moved and (
        Path(p).suffix in {".json", ".csv", ".png", ".svg", ".jpg", ".jpeg", ".gz", ".npz"}
        or p.startswith("paper/pirc17/figures/")
        or p.startswith(tuple("paper/pirc17/" + x + "/" for x in (
            "final-results-v1", "public-paired-replay-v1", "qualification-v1", "replay-input-v1", "secondary-scores-v1", "terrain-description-v1"))))}
    assert not changed & protected
    assert all((ROOT / p).exists() for p in protected)
    assert all(paper_path(ROOT / p) == ROOT / p for p in protected)


def test_both_front_pages_link_only_one_current_release():
    for path in (ROOT / "paper/README.md", PAPER / "README.md"):
        text = path.read_text(encoding="utf-8")
        links = re.findall(r"\]\(([^)]+)\)", text)
        assert any("current/zh/main.pdf" in p for p in links)
        assert any("current/en/main.pdf" in p for p in links)
        assert not any("revision46-review" in p or "reader-v" in p for p in links)
        for relative in links:
            assert (path.parent / relative).exists(), (path.name, relative)
