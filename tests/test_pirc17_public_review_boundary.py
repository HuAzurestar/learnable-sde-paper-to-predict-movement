"""The public review projection must not contain withheld route assets."""
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_public_index_omits_routes_and_original_pdfs():
    names = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    assert not any(name.startswith("paper/pirc17/figures/case-") for name in names)
    assert "paper/pirc17/en/main.pdf" not in names
    assert "paper/pirc17/zh/main.pdf" not in names


def test_public_sources_do_not_load_local_route_figures():
    for language in ("en", "zh"):
        source = (ROOT / "paper/pirc17" / language / "main.tex").read_text(encoding="utf-8")
        assert r"\label{sec:case-horizons}" in source
        assert "../figures/case-" not in source
        assert "tab:case-point-errors" not in source
        assert "fig:case-boechout" not in source


def test_original_review_status_is_not_elevated_by_projection():
    import json
    original = json.loads((ROOT / "paper/pirc17/review-response-v1.json").read_text(encoding="utf-8"))
    assert original["accepted_items"] == 0
    assert original["all_review_items_or_paper_complete"] is False
    assert original["independent_saved_output_audit_completed"] is False
