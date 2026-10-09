"""Repair checkout-only CRLF translation after proving original Git byte identity.

Does not replace user edits or change experiment exports. Windows core.autocrlf
may translate old text-bound JSON despite its recorded SHA. New attributes
protect these byte-bound exports; this migration restores their original bytes.
"""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    paths = subprocess.check_output(["git", "ls-files", "paper/pirc17", "scripts"], cwd=ROOT, text=True).splitlines()
    count = 0
    for name in paths:
        path = ROOT / name
        if path.suffix not in (".tex", ".json", ".py", ".csv", ".md") or not path.is_file():
            continue
        data = path.read_bytes()
        if b"\r\n" not in data:
            continue
        normalized = data.replace(b"\r\n", b"\n")
        original = subprocess.check_output(["git", "show", "8cbcb114:"+name], cwd=ROOT)
        if normalized == original:
            path.write_bytes(original)
            count += 1
    for lang in ("en", "zh"):
        original = subprocess.check_output(["git", "show", "8cbcb114:paper/pirc17/"+lang+"/main.tex"], cwd=ROOT)
        path = ROOT / "paper/pirc17" / lang / "historical-main-v1.tex"
        if path.read_bytes().replace(b"\r\n", b"\n") != original:
            raise ValueError("Historical source differs beyond checkout line endings; no overwrite")
        path.write_bytes(original)
    print("Proved and restored checkout-only line endings:", count, "; two exact historical sources")


if __name__ == "__main__":
    main()
