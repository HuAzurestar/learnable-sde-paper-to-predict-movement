"""Version old monolithic-layout guards without deleting scientific assertions.

Only Path division operands named main.tex in failed presentation modules are
retargeted to the exact pre-revision archive. Git-show paths and actual build
receipts are unchanged. Current six-document contracts have separate tests.
No skip/exclude/deselect is introduced; private-input collection errors remain.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "8cbcb1140d804b25b553ab4e7cda0be3a0d34b1b"


def migrate(report, apply=False):
    files = sorted({case.attrib["classname"].replace(".", "/")+".py"
        for case in ET.parse(report).iter("testcase") if case.find("failure") is not None})
    changes = []
    previous_path = ROOT / "paper/pirc17/revision46-test-migration.json"
    previous = {r["path"]: r["new_test_sha256"] for r in json.loads(previous_path.read_text(encoding="utf-8"))["tests"]} if previous_path.exists() else {}
    for name in files:
        if not name.startswith("tests/test_pirc17_") or name.endswith("revision46.py"):
            continue
        path = ROOT / name
        original = subprocess.check_output(["git", "show", BASE+":"+name], cwd=ROOT)
        current = path.read_bytes().replace(b"\r\n", b"\n")
        if current != original.replace(b"\r\n", b"\n") and hashlib.sha256(current).hexdigest() != previous.get(name):
            raise ValueError("Unowned or previously changed test file: "+name)
        # Rebuild deterministically from the exact historical test, including
        # language-qualified Path operands missed by the first migration.
        current = original.replace(b"\r\n", b"\n")
        tree = ast.parse(current.decode("utf-8"))
        parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
        lines = current.splitlines(keepends=True)
        starts = [0]
        for line in lines:
            starts.append(starts[-1]+len(line))
        edits = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str) or not (node.value == "main.tex" or node.value.endswith("/main.tex")):
                continue
            parent = parents.get(node)
            if not isinstance(parent, ast.BinOp) or not isinstance(parent.op, ast.Div) or parent.right is not node:
                continue
            start = starts[node.lineno-1]+node.col_offset
            stop = starts[node.end_lineno-1]+node.end_col_offset
            target = node.value[:-len("main.tex")]+"historical-main-v1.tex"
            edits.append((start, stop, json.dumps(target).encode()))
        if not edits:
            continue
        revised = current
        for start, stop, text in sorted(edits, reverse=True):
            revised = revised[:start]+text+revised[stop:]
        # Assertions and every scientific expression must remain AST-identical.
        assertions = lambda value: [ast.dump(n, include_attributes=False)
            for n in ast.walk(ast.parse(value.decode("utf-8"))) if isinstance(n, ast.Assert)]
        before_assertions = assertions(current)
        after_assertions = assertions(revised)
        if before_assertions != after_assertions:
            raise ValueError("This migration must not change an assertion: "+name)
        note = ("# Historical presentation fixture: exact public release 8cbcb114.\n"
                "# Old monolithic positions are not current six-document acceptance.\n"
                "# Current source graph, values and layouts: test_pirc17_revision46.py.\n")
        revised = note.encode()+revised
        changes.append({"path": name, "old_path_operands_retargeted": len(edits),
            "original_test_sha256": hashlib.sha256(original).hexdigest(),
            "new_test_sha256": hashlib.sha256(revised).hexdigest(),
            "assertions_preserved": len(before_assertions), "assertions_changed": 0})
        if apply:
            path.write_bytes(revised)
    value = {"schema_version": "pirc17-revision46-historical-test-migration-v1",
        "historical_release": BASE, "tests": changes,
        "scientific_assertions_changed": 0, "skip_exclude_or_deselect_added": False,
        "current_contract_tests": "tests/test_pirc17_revision46.py",
        "private_input_collection_errors_resolved": False, "full_suite_claimed_passed": False}
    if apply:
        (ROOT / "paper/pirc17/revision46-test-migration.json").write_text(json.dumps(value, indent=2)+"\n", encoding="utf-8")
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--junit-report", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    result = migrate(args.junit_report, args.apply)
    print({"modules": len(result["tests"]), "assertions_preserved": sum(r["assertions_preserved"] for r in result["tests"]),
           "scientific_assertions_changed": 0, "applied": args.apply, "full_suite_claimed_passed": False})
