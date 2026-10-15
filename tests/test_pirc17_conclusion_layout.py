"""The body has one result list, one terrain figure and no repeated running title."""
from pathlib import Path
import re

import pytest

PAPER = Path(__file__).resolve().parents[1] / "paper/pirc17"


def expanded(path, stack=()):
    path = path.resolve()
    assert path not in stack, f"Recursive TeX input: {path}"
    text = re.sub(r"(?<!\\)%[^\n]*", "", path.read_text(encoding="utf-8"))
    return re.sub(r"\\input\{([^}]+)\}",
                  lambda m: expanded(path.parent / (m[1] if m[1].endswith('.tex') else m[1] + '.tex'), (*stack, path)), text)


@pytest.mark.parametrize("lang,heading", [("zh", "结论"), ("en", "Conclusion")])
def test_one_numbered_result_list_and_six_conclusions(lang, heading):
    text = expanded(PAPER / lang / "main.tex")
    conclusion = text.split(r"\section{" + heading + "}", 1)[1]
    assert text.count(r"\begin{enumerate}") == text.count(r"\end{enumerate}") == 1
    results = conclusion.split(r"\begin{enumerate}", 1)[1].split(r"\end{enumerate}", 1)[0]
    assert len(re.findall(r"\\item\b", results)) == 6
    assert all(v in results for v in ("CV", "RDM", "120", "300", "46.52", "43", "42.51", "57.27"))
    assert "RQ1" not in results and "RQ2" not in results
    assert r"\renewcommand{\labelenumi}{\arabic{enumi}.}" in results


@pytest.mark.parametrize("lang,discussion", [("zh", "讨论"), ("en", "Discussion")])
def test_single_figure_and_section_definitions_without_running_section_titles(lang, discussion):
    text = expanded(PAPER / lang / "main.tex")
    assert text.count(r"\label{fig:terrain-description}") == 1
    assert text.count("../figures/reader-v9/terrain-evidence.pdf") == 1
    assert text.count(r"\section{" + discussion + "}") == 1
    assert r"\pagestyle{plain}" in text
    assert r"\FloatBarrier" + "\n" + r"\section{" + discussion + "}" in text
