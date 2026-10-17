"""CI covers both current PIRC-17 manuscripts without replacing historical gates."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def job(name):
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    match = re.search(
        rf"^  {re.escape(name)}:\n(.*?)(?=^  [\w-]+:\n|\Z)",
        workflow,
        re.MULTILINE | re.DOTALL,
    )
    assert match, name
    return match.group(1)


def steps(name):
    return [
        step.rstrip()
        for step in re.split(r"^      - ", job(name), flags=re.MULTILINE)[1:]
    ]


@pytest.mark.parametrize("language,engine,label", [
    ("en", "-pdf", "English"),
    ("zh", "-xelatex", "Chinese"),
])
def test_historical_pdf_steps_are_retained(language, engine, label):
    actual = steps("tex-" + language)
    historical = [
        "uses: xu-cheng/latex-action@v4\n"
        "        with:\n"
        "          root_file: main.tex\n"
        f"          working_directory: paper/{language}\n"
        f"          args: {engine} -interaction=nonstopmode -halt-on-error -file-line-error",
        "name: Reject unresolved references and citations\n"
        f"""        run: '! grep -E "Undefined (references|citations)|Rerun to get" paper/{language}/main.log'""",
        "uses: actions/upload-artifact@v4\n"
        "        with:\n"
        f"          name: paper-{language}-" + "${{ github.sha }}\n"
        f"          path: paper/{language}/main.pdf\n"
        "          retention-days: 7",
    ]
    start = actual.index(historical[0])
    assert actual[start:start + len(historical)] == historical


@pytest.mark.parametrize("language,engine,label", [
    ("en", "-pdf", "English"),
    ("zh", "-xelatex", "Chinese"),
])
def test_current_manuscript_build_and_strict_log_check_are_required(language, engine, label):
    actual = steps("tex-" + language)
    compile_step = (
        f"name: Compile current PIRC-17 {label} manuscript\n"
        "        uses: xu-cheng/latex-action@v4\n"
        "        with:\n"
        "          root_file: main.tex\n"
        f"          working_directory: paper/pirc17/{language}\n"
        f"          args: {engine} -interaction=nonstopmode -halt-on-error -file-line-error"
    )
    start = actual.index(compile_step)
    assert actual[start + 1] == (
        "uses: actions/setup-python@v7\n"
        "        with:\n"
        '          python-version: "3.10"'
    )
    assert actual[start + 2] == (
        f"name: Reject unresolved or clipped PIRC-17 {label} output\n"
        "        run: |\n"
        '          python -c "from pathlib import Path; from scripts.build_pirc17 import check_log; '
        f"check_log(Path('paper/pirc17/{language}/main.log').read_text(encoding='utf-8', errors='replace'))" + '"'
    )
    assert actual[start + 3] == (
        "uses: actions/upload-artifact@v4\n"
        "        with:\n"
        f"          name: pirc17-{language}-" + "${{ github.sha }}\n"
        f"          path: paper/pirc17/{language}/main.pdf\n"
        "          retention-days: 7"
    )
    assert start + 7 == len(actual)
    companion = actual[start + 4]
    assert f"Compile PIRC-17 {label} companion documents" in companion
    assert "supplement.tex\n            audit-notes.tex" in companion
    assert f"working_directory: paper/pirc17/{language}" in companion
    assert f"args: {engine} -interaction=nonstopmode -halt-on-error -file-line-error" in companion
    assert "check_log" in actual[start + 5] and "('supplement','audit-notes')" in actual[start + 5]
    assert f"paper/pirc17/{language}/supplement.pdf" in actual[start + 6]
    assert f"paper/pirc17/{language}/audit-notes.pdf" in actual[start + 6]
    assert "continue-on-error:" not in job("tex-" + language)


def test_original_evidence_command_and_required_gates_are_not_excluded():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    if re.search(r"^  evidence:", workflow, re.MULTILINE):
        evidence = job("evidence")
        assert "python -m pytest tests -q" in evidence
        assert "python -m pip install -r requirements-test.txt" in evidence
        gate = "EVIDENCE"
    else:
        evidence = job("aggregation")
        assert "python -m pytest -q" in evidence
        gate = "AGGREGATION"
    assert "--ignore" not in evidence
    assert "--deselect" not in evidence
    assert "continue-on-error" not in evidence
    required = job("required")
    assert "if: ${{ always() }}" in required
    for name in ["POLICY", "TEX_EN", "TEX_ZH", gate]:
        assert f'test "${name}" = success' in required

