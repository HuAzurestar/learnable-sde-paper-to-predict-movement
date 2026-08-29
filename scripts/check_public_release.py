"""Reject private research artifacts and workstation paths in paper sources."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_SUFFIXES = {".parquet", ".npy", ".npz", ".pt", ".pth", ".ckpt", ".zip", ".7z"}
PATTERNS = {
    "workstation path": re.compile(r"(?i)(?:\b[A-Z]:[\\/]|[\\/]Users[\\/][^\\/]+|[\\/]home[\\/][^\\/]+)"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "common access token": re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,})"),
}


def candidate_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return [ROOT / item for item in result.stdout.splitlines() if item]


def main() -> int:
    problems: list[str] = []
    for path in candidate_files():
        relative = path.relative_to(ROOT)
        if relative == Path("scripts/check_public_release.py"):
            continue
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            problems.append(f"forbidden artifact: {relative}")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(content):
                line = content.count("\n", 0, match.start()) + 1
                problems.append(f"{label}: {relative}:{line}")
    if problems:
        print("Public release scan failed:")
        print("\n".join(f"  - {item}" for item in sorted(set(problems))))
        return 1
    print("Public release scan passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
