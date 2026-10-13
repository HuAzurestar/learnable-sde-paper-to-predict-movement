"""Current convergence contract: existing evidence, four figures, bounded claims."""
from pathlib import Path
import re
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"


@pytest.mark.parametrize("language", ["en", "zh"])
def test_current_body_keeps_core_evidence_and_four_existing_figures(language):
    body = (PAPER / language / "main.tex").read_text(encoding="utf-8")
    expanded = body
    for stem in ("reader-v2-tradeoff", "reader-v2-calibration"):
        expanded = expanded.replace(r"\input{"+stem+".tex}", (PAPER / language / (stem+".tex")).read_text(encoding="utf-8"))
    figures = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", expanded)
    assert len(figures) == 4
    assert {Path(f).name for f in figures} == {
        "revision46-population.pdf", "revision46-inertial-horizons.pdf",
        "tradeoff.pdf", "preliminary-calibration-area.pdf"}
    assert expanded.count(r"\begin{table}") == 2
    for figure in figures:
        path = (PAPER / language / figure).resolve()
        relative = path.relative_to(ROOT).as_posix()
        assert path.read_bytes() == subprocess.check_output(["git", "show", "6370953:"+relative], cwd=ROOT)
    for value in ("512", "46.52", "95.65", "37.83", "35.22", "33.04", "52.17",
                  "21.74", "79.13", "41.100259", "1379/1380", "1148/1150", "RQ1", "RQ2"):
        assert value in body
    for macro in ("FullES", "InertialES", "InertialDelta", "PointRowFull", "PointRowGMM", "PointRowdtThreeHundred", "PointRowInertial"):
        assert "\\"+macro in body
    assert r"\frac1{2N(N-1)}\sum_{i\ne j}" in body
    assert body.index(r"\input{reader-v2-tradeoff.tex}") < body.index(r"\input{reader-v2-calibration.tex}")
    assert ("not a fresh blinded holdout" if language == "en" else "不是全新盲测留出集") in body
    assert ("not a positive or null terrain" if language == "en" else "不是地形正效应或零效应") in body
    assert ("not 230" if language == "en" else "不是230") in body
    assert (r"\section{Conclusion}" if language == "en" else r"\section{结论}") in body
    assert not any("case-" in f for f in figures)


def test_no_existing_scientific_or_image_asset_changes():
    tracked = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "6370953", "paper/pirc17"], cwd=ROOT, text=True).splitlines()
    for name in tracked:
        if "/figures/" in name and name.endswith((".png", ".pdf", ".json")):
            current = (ROOT / name).read_bytes()
            original = subprocess.check_output(["git", "show", "6370953:"+name], cwd=ROOT)
            # Git's Windows text checkout may apply CRLF to manifests; image
            # binaries remain byte-exact and manifest content is unchanged.
            if name.endswith(".json"):
                current = current.replace(b"\r\n", b"\n")
            assert current == original, name
