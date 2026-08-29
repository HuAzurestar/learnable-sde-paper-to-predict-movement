"""Validate the repository's Issue-first pull-request title convention."""

from __future__ import annotations

import re
import sys

TYPE_TO_PREFIX = {
    "feat": "feature", "fix": "fix", "docs": "docs", "refactor": "refactor",
    "perf": "perf", "test": "test", "build": "build", "ci": "ci", "chore": "chore",
    "paper": "paper",
}
HEADER = re.compile(r"^#([1-9][0-9]*) (" + "|".join(TYPE_TO_PREFIX) + r")(?:\([a-z0-9][a-z0-9-]*\))?!?: .+")


def main(title: str, branch: str) -> int:
    if re.fullmatch(r"chore: repository bootstrap(?: .+)?", title):
        return 0 if branch.startswith("chore/") else 1
    match = HEADER.fullmatch(title)
    if not match:
        print("PR title must use #<issue> <type>(optional-scope): summary")
        return 1

    issue, change_type = match.group(1), match.group(2)
    expected_prefix = f"{TYPE_TO_PREFIX[change_type]}/{issue}-"
    if not branch.startswith(expected_prefix):
        print(
            f"PR type '{change_type}' requires branch '{expected_prefix}<summary>'; "
            f"received '{branch}'"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
