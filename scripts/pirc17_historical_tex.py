"""Resolve explicitly archived TeX without modifying frozen source receipts."""
from functools import lru_cache
import hashlib
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"
SOURCE = "8caa3a09bdda29a1f8613f11710e1f84eb01e5dc"
INDEX = PAPER / "tex-archive-index.tsv"
_cache = TemporaryDirectory(prefix="pirc17-historical-tex-")


@lru_cache(maxsize=1)
def archive_entries():
    rows = {}
    for line in INDEX.read_text(encoding="utf-8").splitlines()[1:]:
        original, archived, sha = line.split("\t")
        for relative in (original, archived):
            path = (PAPER / relative).resolve()
            if not path.is_relative_to(PAPER.resolve()):
                raise ValueError("archive index escapes the paper directory")
        if original in rows or len(sha) != 64:
            raise ValueError("invalid or duplicate archive entry")
        rows[original] = (archived, sha)
    return rows


def historical_tex(path: Path, *, use_git=False) -> Path:
    """Keep original IDs; resolve moved files or exact pinned Git bytes.

    Non-archived current inputs pass through unchanged. Missing/corrupt
    archived bytes never weaken a historical hash assertion. Git fallback
    means the review archive can later be removed without breaking readers.
    """
    path = Path(path).resolve()
    if not path.is_relative_to(PAPER.resolve()):
        raise ValueError("historical TeX path must be inside paper/pirc17")
    original = path.relative_to(PAPER).as_posix()
    entry = archive_entries().get(original)
    if entry is None:
        return path
    archived, expected = entry
    target = (PAPER / archived).resolve()
    if use_git or not target.exists():
        target = Path(_cache.name) / (expected + ".tex")
        if not target.exists():
            data = subprocess.check_output(
                ["git", "show", SOURCE + ":paper/pirc17/" + original], cwd=ROOT)
            if hashlib.sha256(data).hexdigest() != expected:
                # Some legacy working-tree TeX used CRLF. Reconstruct only
                # when that checkout-only conversion proves the exact hash.
                checkout = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
                if hashlib.sha256(checkout).hexdigest() == expected:
                    data = checkout
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError("pinned Git source differs from archive receipt")
            target.write_bytes(data)
    if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
        raise ValueError("archived TeX differs from frozen source bytes")
    return target
