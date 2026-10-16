"""Resolve a renamed current figure to its unchanged historical evidence asset."""
from scripts.pirc17_paper_paths import paper_path
import hashlib
import json
from pathlib import Path


def original_figure(paper: Path, relative: str) -> Path:
    current = (paper / "en" / relative).resolve()
    folder = (paper / "figures/reader-v9").resolve()
    if current.parent != folder or current.suffix != ".pdf":
        raise ValueError("current scientific figure must use the reader-v9 asset graph")
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    rows = [r for r in manifest["figures"] if r["current_pdf"] == "figures/reader-v9/" + current.name]
    if len(rows) != 1:
        raise ValueError("unique current-to-original binding required")
    row = rows[0]
    baseline = json.loads((paper_path(paper / "revision46-review-v8/build-manifest.json")).read_text(encoding="utf-8"))
    originals = {k: v for d in baseline["manuscripts"] if d["entry"] in {"main", "supplement"}
                 for k, v in d["source_graph_sha256"].items() if k.endswith(".pdf")}
    historical = paper.parents[1] / row["original_pdf"]
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    if not (originals[row["original_pdf"]] == row["original_pdf_sha256"] == sha(historical)):
        raise ValueError("historical evidence figure changed")
    if sha(current) != row["files_sha256"][current.name]:
        raise ValueError("current figure differs from rendering receipt")
    if row["scientific_artist_sha256_before"] != row["scientific_artist_sha256_after"]:
        raise ValueError("display renaming changed plotted scientific data")
    return historical
