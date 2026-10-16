"""Resolve relocated manuscript artifacts, never relocate scientific assets."""
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"
INDEX = PAPER / "paper-layout-index.tsv"


@lru_cache(maxsize=1)
def paper_entries():
    rows = {}
    for line in INDEX.read_text(encoding="utf-8").splitlines()[1:]:
        original, archived, sha = line.split("\t")
        for relative in (original, archived):
            if not (PAPER / relative).resolve().is_relative_to(PAPER.resolve()):
                raise ValueError("paper layout index escapes paper/pirc17")
        if original in rows or len(sha) != 64:
            raise ValueError("duplicate or invalid manuscript artifact entry")
        rows[original] = (archived, sha)
    return rows


def paper_path(path: Path) -> Path:
    """Keep old evidence IDs readable after moving paper-only artifacts.

    Archived snapshots stay immutable even when current/ is later updated.
    Unknown paths, including all scientific data/images, pass through.
    """
    path = Path(path).resolve()
    if not path.is_relative_to(PAPER.resolve()):
        return path
    relative = path.relative_to(PAPER).as_posix()
    entry = paper_entries().get(relative)
    if entry is not None:
        return PAPER / entry[0]
    for version in range(1, 11):
        old = "revision46-review-v" + str(version)
        if relative == old or relative.startswith(old + "/"):
            suffix = relative[len(old):].lstrip("/")
            return PAPER / "archive/paper-versions" / ("v" + str(version)) / suffix
    return path
