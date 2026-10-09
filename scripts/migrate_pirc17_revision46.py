"""Mechanically partition the frozen pre-revision sources; no scientific rerun.

The verbatim snapshots are immutable. Every old source unit is assigned a
destination and hash; rewriting the reader-facing argument is a separate task.
Generated cross-document links refer to explicit PDF named destinations.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"
AUDIT = {
    "sec:audited-review-update", "sec:preliminary-cost", "sec:runtime-environment",
    "sec:source-reconciliation-details", "sec:score-execution-snapshots",
    "sec:execution-coverage", "sec:runtime-record-details", "sec:execution-reconstruction",
}
ARCHIVE_TITLES = {
    "Introduction", "引言", "Discussion and limitations", "讨论与局限",
    "Conclusion", "结论",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def export():
    report = {"schema_version": "pirc17-revision46-source-migration-v1",
              "source_commit": "8cbcb1140d804b25b553ab4e7cda0be3a0d34b1b",
              "new_fits_forecasts_or_resampling": 0, "languages": {}}
    for lang in ("en", "zh"):
        folder = PAPER / lang
        frozen = folder / "historical-main-v1.tex"
        data = frozen.read_bytes()
        source = data.decode("utf-8").replace("\r\n", "\n")
        bib_start = source.index(r"\begin{thebibliography}")
        bib_end = source.index(r"\end{thebibliography}") + len(r"\end{thebibliography}")
        (folder / "revision46-bibliography.tex").write_text(source[bib_start:bib_end] + "\n", encoding="utf-8")
        core = source[source.index(r"\section{Introduction}" if lang == "en" else r"\section{引言}"):bib_start]
        # Sections/subsections are indivisible old units; include all paragraphs,
        # formulae, tables and \input directives, not a selected numerical subset.
        starts = list(re.finditer(r"^\\(?:section|subsection)\{([^\n]+?)\}", core, re.M))
        units = []
        parent = ""
        for n, match in enumerate(starts):
            end = starts[n+1].start() if n+1 < len(starts) else len(core)
            value = core[match.start():end].replace("\\appendix\n", "")
            title = match.group(1)
            labels = re.findall(r"\\label\{([^}]+)\}", value)
            if match.group(0).startswith(r"\section"):
                parent = title
            destination = "supplement"
            if parent in ARCHIVE_TITLES:
                destination = "historical-source"
            if set(labels) & AUDIT or parent in ("Version and evidence binding", "版本与证据绑定"):
                destination = "audit-notes"
            # Once an appendix scientific subsection begins, classify by its
            # own label rather than putting every appendix into an audit bin.
            if match.group(0).startswith(r"\subsection") and parent in ("Version and evidence binding", "版本与证据绑定"):
                destination = "audit-notes" if set(labels) & AUDIT else "supplement"
            if parent in ("Computational cost", "计算成本"):
                destination = "audit-notes"
            units.append(dict(title=title, labels=labels, destination=destination,
                              original_text_sha256=sha(value.encode()), text=value,
                              start_line=source[:source.index(core)+match.start()].count("\n")+1))
        ownership = {label: unit["destination"] for unit in units for label in unit["labels"]}
        scientific_tables = {"all-method-absolute.tex", "method-horizon-tables.tex", "method-region-tables.tex"}
        for unit in units:
            for name in re.findall(r"\\input\{([^}]+)\}", unit["text"]):
                child = folder / (name if name.endswith(".tex") else name+".tex")
                if child.is_file():
                    for label in re.findall(r"\\label\{([^}]+)\}", child.read_text(encoding="utf-8")):
                        ownership[label] = "supplement" if child.name in scientific_tables else unit["destination"]
        for destination in ("supplement", "audit-notes"):
            chunks = []
            for unit in units:
                if unit["destination"] != destination:
                    continue
                value = unit["text"]
                if destination == "audit-notes":
                    for name in scientific_tables:
                        value = value.replace(r"\input{"+name+"}", "")
                # These are versioned current reading documents, not literal
                # archived snapshots. Preserve the latter's bytes separately.
                value = re.sub(r"\\label\{([^}]+)\}", lambda m: m.group(0)+r"\hypertarget{"+m.group(1)+"}{}", value)
                def external(m):
                    label = m.group(1)
                    owner = ownership.get(label)
                    if owner == destination:
                        return m.group(0)
                    filename = "main" if owner == "historical-source" or owner is None else owner
                    title = {"main": "main paper" if lang == "en" else "论文本体",
                             "supplement": "scientific supplement" if lang == "en" else "科学补充材料",
                             "audit-notes": "audit record" if lang == "en" else "审查记录"}[filename]
                    return r"\href{"+filename+r".pdf\#"+label+"}{"+title+"}"
                value = re.sub(r"\\(?:ref|eqref)\{([^}]+)\}", external, value)
                # The old overview's 'support blocks' are reused cases, never
                # twelve extra recording identities. No old JSON is edited.
                value = value.replace("46 primary blocks and 12 support blocks", "46 unique recording blocks and 12 reused support cases (58 origin--mode cases)")
                value = value.replace("46 个主要块和 12 个支持块", "46 个独特记录块与 12 个复用的支持案例（58 个起点--模式案例）")
                chunks.append(value)
            # Appendix subsections are promoted to independently numbered
            # supplement/audit sections; numeric facts and labels are retained.
            content = "\n".join(chunks)
            # New presentation assets have their own bindings. Never overwrite
            # an old figure/manifest whose hash belongs to a historical audit.
            for name in ("method-horizon-overview", "method-region-overview"):
                original = folder / (name+".tex")
                revised = original.read_text(encoding="utf-8").replace(
                    "../figures/"+name+".pdf", "../figures/revision46-corrections-v1/"+name+".pdf")
                (folder / ("revision46-"+name+".tex")).write_text(revised, encoding="utf-8")
                content = content.replace(r"\input{"+name+".tex}", r"\input{revision46-"+name+".tex}")
            content = content.replace("../figures/preliminary-full-horizons.pdf",
                                      "../figures/revision46-corrections-v1/preliminary-full-horizons.pdf")
            if destination == "supplement":
                content += "\n\\section{" + ("Complete saved method tables" if lang == "en" else "完整保存方法表") + "}\n"
                content += "\n".join(r"\input{"+name+"}" for name in sorted(scientific_tables))+"\n"
            content = content.replace(r"\subsection{", r"\section{")
            (folder / f"revision46-{destination}-retained.tex").write_text(content, encoding="utf-8")
        report["languages"][lang] = {"frozen_source_sha256": sha(data),
            "units": [{k: v for k, v in unit.items() if k != "text"} for unit in units],
            "original_bibliography_sha256": sha(source[bib_start:bib_end].encode()),
            "all_units_assigned": len(units) == len(starts),
            "scientific_inputs_moved_from_execution_unit_to_supplement": sorted(scientific_tables)}
    stats = json.loads((PAPER / "preliminary-method-statistics-v1.json").read_text(encoding="utf-8"))
    inertial = json.loads((PAPER / "inertial-primary-description-v1.json").read_text(encoding="utf-8"))["profiles"][0]
    points = json.loads((PAPER / "point-error-horizon-description-v1.json").read_text(encoding="utf-8"))["profiles"]
    full = next(c for c in stats["configs"] if c["configuration"] == "arm-01/full")
    numbers = {"FullES": full["weighted_es_m"], "InertialES": inertial["weighted_es_m"],
               "FullFDE": full["fde_m"], "FullADE": full["ade_m"],
               "InertialDelta": full["weighted_es_m"] - inertial["weighted_es_m"]}
    lines = ["% Generated from original public aggregate values; no inference."]
    lines += ["\\newcommand{\\"+k+"}{"+f"{v:.2f}"+"}" for k,v in numbers.items()]
    for profile in points:
        name = profile["model"]
        command = "dtThreeHundred" if name == "dt300" else name
        lines.append(r"\newcommand{\PointRow"+command+"}{"+name+" & "+" & ".join(f"{v:.2f}" for v in profile["point_error_by_time_m"])+r"\\}")
    (PAPER / "revision46-numbers.tex").write_text("\n".join(lines)+"\n", encoding="utf-8")
    (PAPER / "revision46-source-migration.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    result = export()
    print("Frozen sources partitioned; units:", {k: len(v["units"]) for k,v in result["languages"].items()})
