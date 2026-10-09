"""Resolve actual PDF companion links against compiled named destinations."""
import argparse
import json
from pathlib import Path
from urllib.parse import unquote
import fitz


def check(folder):
    problems, counts = [], {}
    for language in ("en", "zh"):
        docs = {name: fitz.open(folder / language / (name+".pdf")) for name in ("main", "supplement", "audit-notes")}
        names = {key: set(doc.resolve_names()) for key,doc in docs.items()}
        checked = 0
        for source,doc in docs.items():
            for index,page in enumerate(doc):
                for link in page.get_links():
                    file = link.get("file", "")
                    if not file or ".pdf#nameddest=" not in file:
                        continue
                    file, label = file.split("#nameddest=", 1)
                    target = Path(file).stem
                    label = unquote(label)
                    if target not in names or label not in names[target]:
                        problems.append({"language": language, "source": source, "page": index+1,
                                         "target": target, "destination": label})
                    checked += 1
        counts[language] = checked
        for doc in docs.values():
            doc.close()
    return {"schema_version": "pirc17-pdf-companion-link-check-v1", "checked": counts,
            "broken": problems, "passed": not problems, "human_visual_acceptance": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, required=True)
    result = check(parser.parse_args().build_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
