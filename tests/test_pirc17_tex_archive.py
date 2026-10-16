"""Reversible archiving must preserve evidence and every active build input."""
import hashlib
import json
from pathlib import Path

import pytest

from scripts.pirc17_historical_tex import (
    PAPER, SOURCE, archive_entries, historical_tex,
)


def test_all_twenty_moves_preserve_original_and_git_bytes():
    rows = archive_entries()
    assert len(rows) == 20
    for original, (archived, sha) in rows.items():
        assert not (PAPER / original).exists()
        path = historical_tex(PAPER / original)
        assert path == PAPER / archived
        assert hashlib.sha256(path.read_bytes()).hexdigest() == sha
        assert historical_tex(PAPER / original, use_git=True).read_bytes() == path.read_bytes()
    assert SOURCE == "8caa3a09bdda29a1f8613f11710e1f84eb01e5dc"


def test_every_v10_build_input_is_still_exact_and_outside_archive():
    manifest = json.loads((PAPER / "revision46-review-v10/build-manifest.json").read_text())
    inputs = {k: v for row in manifest["manuscripts"] for k, v in row["source_graph_sha256"].items()}
    assert len(inputs) == 76
    assert sum(k.endswith(".tex") for k in inputs) == 56
    for name, sha in inputs.items():
        assert "/archive/" not in name
        assert hashlib.sha256((PAPER.parents[1] / name).read_bytes()).hexdigest() == sha


def test_current_regeneration_templates_are_not_archived():
    manifest = json.loads((PAPER / "figures/reader-v9/manifest.json").read_text())
    assert len(manifest["tex_projections"]) == 20
    for row in manifest["tex_projections"]:
        path = PAPER.parents[1] / row["source"]
        assert path.exists() and "/archive/" not in str(path).replace("\\", "/")
        text = path.read_text(encoding="utf-8").encode("utf-8")
        assert hashlib.sha256(text).hexdigest() == row["source_utf8_lf_sha256"]


def test_resolver_rejects_escape_and_leaves_current_sources_alone():
    assert historical_tex(PAPER / "en/main.tex") == PAPER / "en/main.tex"
    with pytest.raises(ValueError):
        historical_tex(Path("outside.tex").resolve())
