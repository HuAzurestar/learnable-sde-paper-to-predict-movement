"""Create a new, explicitly unaccepted response from the 46 approved task cards.

Keeps every checklist and original42 mapping. This is a ledger initializer,
not a completion mechanism; it refuses to replace an existing response.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"


def create(plan_dir):
    output = PAPER / "revision46-response-v1.json"
    if output.exists():
        raise ValueError("Existing review work cannot be overwritten by initialization")
    records, source_bindings = [], {}
    for name in ("20261008-paper-revision-figures.md", "20261008-paper-revision-structure.md", "20261008-paper-revision-science.md"):
        path = plan_dir / name
        data = path.read_bytes()
        source_bindings[name] = hashlib.sha256(data).hexdigest()
        text = data.decode("utf-8")
        parts = list(re.finditer(r"^## ([GORX]\d{2}) (.+)$", text, re.M))
        for n, match in enumerate(parts):
            block = text[match.end():parts[n+1].start() if n+1 < len(parts) else len(text)]
            checks = re.findall(r"^- \[ \] (.+)$", block, re.M)
            records.append({"id": match.group(1), "title": match.group(2),
                "editing": "draft_implemented" if match.group(1) != "G12" else "pending_local_case_revision",
                "verification": "pending", "human_accepted": False,
                "checklist": [{"criterion": check, "status": "pending", "evidence": []} for check in checks],
                "remaining_scientific_gaps": [], "evidence": []})
    detailed = plan_dir / "20261008-paper-revision-plan-detailed.md"
    text = detailed.read_text(encoding="utf-8")
    mapping = {}
    for match in re.finditer(r"^\| (P[012]-\d{2}) \|[^\n]+?\| ([^|]+) \|", text, re.M):
        mapping[match.group(1)] = re.findall(r"[GORX]\d{2}", match.group(2))
    if len(records) != 46 or len({r["id"] for r in records}) != 46 or len(mapping) != 42:
        raise ValueError("All46 cards and original42 mappings required")
    expected = {f"{prefix}{n:02d}" for prefix,total in (("G",13),("O",8),("R",17),("X",8)) for n in range(1,total+1)}
    if expected != {r["id"] for r in records} or any(not set(v) <= expected for v in mapping.values()):
        raise ValueError("Card ID or original review mapping mismatch")
    value = {"schema_version": "pirc17-revision46-response-v1", "source_base_commit": "8cbcb1140d804b25b553ab4e7cda0be3a0d34b1b",
        "plan_source_sha256": source_bindings, "tasks": records, "original42_mapping": mapping,
        "original42_accepted": 0, "editing_complete": False, "verification_complete": False,
        "scientific_gaps_solved_by_prose": False, "human_accepted": False,
        "new_experiments": 0, "authorship": "awaiting_true_author_or_explicit_anonymous_review_confirmation",
        "public_case_permission": "unverified; no private case input in public build",
        "paper_pr_delivered": False, "MPA_master_merged": False}
    output.write_text(json.dumps(value, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print("46 cards;", sum(len(r["checklist"]) for r in records), "pending checks; original42 mapped; not acceptance")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, required=True)
    create(parser.parse_args().plan_dir)
