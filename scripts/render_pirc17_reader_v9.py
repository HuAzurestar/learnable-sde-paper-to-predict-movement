"""Rerender the active scientific figure graph with one display-name policy.

Reuse the actual original plotting functions and unchanged aggregates; edit
Matplotlib text/formatters before rendering, never paint over a PDF/PNG. Old
renderers/assets remain versioned historical evidence. Only the 19 unique
figures used by the current main/supplement graph are delivered. No model,
private trajectories, new scores, fit, map query or inference is imported.
"""
from __future__ import annotations
from scripts.pirc17_paper_paths import paper_path

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
from unittest.mock import patch

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib.patches import FancyArrowPatch
from matplotlib.text import Annotation, Text
from matplotlib.ticker import Formatter
import numpy as np

from scripts.pirc17_display_names import display_text, figure_text, tex_display

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"
BASELINE = paper_path(PAPER / "revision46-review-v8/build-manifest.json")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def payload_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=True,
                                    default=str).encode()).hexdigest()


def text_digest(path):
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def numerical_artists(fig):
    """Scientific artist data, not layout/tick-label positions affected by text."""
    def array(value):
        a = np.ma.asarray(value)
        return {"data": a.data.tolist(), "mask": np.ma.getmaskarray(a).tolist()}
    return [{"lines": [[array(line.get_xdata()), array(line.get_ydata())] for line in ax.lines],
             "images": [array(im.get_array()) for im in ax.images],
             "collections": [{"offsets": array(c.get_offsets()),
                              "values": None if c.get_array() is None else array(c.get_array()),
                              "paths": [array(p.vertices) for p in c.get_paths()]}
                             for c in ax.collections],
             # Arrow-head display vertices depend on layout. The scientific
             # geometry is their data-coordinate start/end points instead.
             "patches": [array(p._posA_posB) if isinstance(p, FancyArrowPatch)
                         else array(p.get_path().vertices) for p in ax.patches]}
            for ax in fig.axes]


class DisplayFormatter(Formatter):
    def __init__(self, original):
        self.original = original

    def __call__(self, value, pos=None):
        return figure_text(self.original(value, pos))

    def get_offset(self):
        return self.original.get_offset()

    def set_locs(self, locs):
        super().set_locs(locs)
        self.original.set_locs(locs)

    def set_axis(self, axis):
        super().set_axis(axis)
        self.original.set_axis(axis)


def name_figure(fig):
    fig.canvas.draw()  # Materialise lazy tick and legend text before inspecting it.
    before = payload_hash(numerical_artists(fig))
    changed = {}
    for text in fig.findobj(Text):
        old = text.get_text()
        new = figure_text(old)
        if isinstance(text, Annotation) and new in {"Mixed calibration", "ES calibration"}:
            new = new.replace(" ", "\n", 1)
        if old != new:
            changed[old] = new
            text.set_text(new)
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            for which in ("major", "minor"):
                formatter = getattr(axis, "get_" + which + "_formatter")()
                if not isinstance(formatter, DisplayFormatter):
                    getattr(axis, "set_" + which + "_formatter")(DisplayFormatter(formatter))
    fig.canvas.draw()
    after = payload_hash(numerical_artists(fig))
    if before != after:
        raise ValueError("display naming changed scientific artist data")
    labels = sorted({text.get_text() for text in fig.findobj(Text) if text.get_text()})
    forbidden = [s for s in labels if re.search(r"\b(?:Full\d*|GMM|Inertial|inertial)\b", s, flags=re.ASCII)]
    if forbidden:
        raise ValueError("legacy visible model names remain: " + repr(forbidden))
    return {"label_changes": changed, "displayed_labels": labels,
            "scientific_artist_sha256_before": before,
            "scientific_artist_sha256_after": after}


def stem_for(original):
    return {"full-overview": "method-overview",
            "revision46-inertial-horizons": "cv-horizons",
            "preliminary-full-horizons": "hsm-horizons"}.get(original.stem, original.stem)


def project_supplement(baseline, output, figure_paths):
    """Version display-only TeX; original tables/data/labels remain traceable."""
    result = []
    for lang in ("en", "zh"):
        source = next(d for d in baseline["manuscripts"] if d["language"] == lang and d["entry"] == "supplement")
        paths = [ROOT / p for p in source["source_graph_sha256"]
                 if p.startswith("paper/pirc17/" + lang + "/") and p.endswith(".tex")
                 and Path(p).name not in {"supplement.tex", "revision46-preamble.tex", "revision46-bibliography.tex"}]
        projected_names = {p.name for p in paths}
        destination = output / "projections" / lang
        destination.mkdir(parents=True)
        for path in paths:
            original = path.read_text(encoding="utf-8")
            current = tex_display(original)
            for old, new in figure_paths.items():
                current = current.replace("../" + old, "../figures/reader-v9/" + new)
            current = re.sub(r"\\input\{([^}]+)\}",
                             lambda m: r"\input{reader-v9/" + m[1] + "}" if m[1] in projected_names else m[0], current)
            target = destination / path.name
            target.write_text(current, encoding="utf-8")
            # Count every original table and preserve all labels, math and numbers;
            # presentation names, not original machine identities, may change.
            labels = lambda t: re.findall(r"\\label\{([^}]+)\}", t)
            if labels(original) != labels(current):
                raise ValueError("projection changed scientific table/figure anchors")
            result.append({"source": path.relative_to(ROOT).as_posix(),
                           "source_utf8_lf_sha256": text_digest(path),
                           "projection": lang + "/reader-v9/" + path.name,
                           "projection_utf8_lf_sha256": text_digest(target),
                           "table_anchors": [label for label in labels(current) if label.startswith("tab:")]})
    return result


def render(output):
    if output.exists():
        raise ValueError("fresh external output required; never overwrite historical figures")
    output.mkdir(parents=True)
    # Legacy SVG manifests are retained inside the receipt too. Make their
    # non-scientific IDs/date fields deterministic, without editing old renderers.
    matplotlib.rcParams["svg.hashsalt"] = "pirc17-reader-v9"
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    original_nodes = {k: v for d in baseline["manuscripts"] if d["entry"] in {"main", "supplement"}
                      for k, v in d["source_graph_sha256"].items() if k.endswith(".pdf")}
    if len(original_nodes) != 19:
        raise ValueError("unexpected original main/supplement figure graph")
    for path, checksum in original_nodes.items():
        if digest(ROOT / path) != checksum:
            raise ValueError("historical active figure changed: " + path)
    from scripts import (plot_pirc17_revision46, plot_pirc17_reader_v2,
                         plot_pirc17_preliminary, plot_pirc17_calibration,
                         plot_pirc17_calibration_blocks, plot_pirc17_terrain)
    jobs = [("revision46-v1", plot_pirc17_revision46), ("reader-v2", plot_pirc17_reader_v2),
            ("preliminary", plot_pirc17_preliminary), ("calibration", plot_pirc17_calibration),
            ("blocks", plot_pirc17_calibration_blocks), ("terrain-description-v1", plot_pirc17_terrain)]
    renderer_hashes = {Path(m.__file__).name: digest(Path(m.__file__)) for _, m in jobs}
    renderer_hashes[Path(__file__).name] = digest(Path(__file__))
    renderer_hashes["pirc17_display_names.py"] = digest(Path(__file__).with_name("pirc17_display_names.py"))
    records, rewritten, legacy_manifests = [], {}, {}
    original_savefig = Figure.savefig

    def named_savefig(fig, path, *args, **kwargs):
        if not hasattr(fig, "_pirc17_display_record"):
            fig._pirc17_display_record = name_figure(fig)
        if Path(path).suffix == ".pdf":
            kwargs["metadata"] = {**(kwargs.get("metadata") or {}), "CreationDate": None, "ModDate": None}
        elif Path(path).suffix == ".svg":
            kwargs["metadata"] = {**(kwargs.get("metadata") or {}), "Date": None}
        rewritten[str(Path(path).resolve())] = fig._pirc17_display_record
        return original_savefig(fig, path, *args, **kwargs)

    with tempfile.TemporaryDirectory(prefix="pirc17-reader-v9-") as temporary:
        temporary = Path(temporary)
        for name, module in jobs:
            dest = temporary / name
            with patch.object(Figure, "savefig", named_savefig):
                if name == "terrain-description-v1":
                    module.render(PAPER / "terrain-description-v1/summary.json", dest)
                else:
                    module.render(dest)
            legacy_manifests[name] = {p.name: json.loads(p.read_text(encoding="utf-8"))
                                      for p in dest.glob("*manifest.json")}
        figure_paths = {}
        for old, checksum in original_nodes.items():
            original = Path(old)
            if original.parent.name in {"revision46-v1", "reader-v2", "terrain-description-v1"}:
                directory = original.parent.name
            elif original.stem == "preliminary-calibration-area":
                directory = "calibration"
            elif original.stem == "preliminary-calibration-blocks":
                directory = "blocks"
            else:
                directory = "preliminary"
            rendered = temporary / directory / original.name
            stem = stem_for(original)
            files = {}
            for suffix in (".pdf", ".png"):
                target = output / (stem + suffix)
                shutil.copyfile(rendered.with_suffix(suffix), target)
                files[target.name] = digest(target)
            figure_paths[original.relative_to(Path("paper/pirc17")).as_posix()] = stem + ".pdf"
            records.append({"original_pdf": old, "original_pdf_sha256": checksum,
                            "current_pdf": "figures/reader-v9/" + stem + ".pdf", "files_sha256": files,
                            **rewritten[str(rendered.resolve())]})
        for language in ("en", "zh"):
            table = (temporary / "terrain-description-v1" / ("summary-table-" + language + ".tex")).read_text(encoding="utf-8")
            # This table's rows intentionally use the same A-g/B+g labels as the plot.
            (output / ("summary-table-" + language + ".tex")).write_text(
                display_text(table), encoding="utf-8")
    projections = project_supplement(baseline, output, figure_paths)
    original_numbers = (PAPER / "revision46-numbers.tex").read_text(encoding="utf-8")
    number_labels = [tex_display(line).replace(r"\newcommand", r"\renewcommand", 1)
                     for line in original_numbers.splitlines() if line.startswith(r"\newcommand{\PointRow")]
    if len(number_labels) != 4:
        raise ValueError("four unchanged point-error rows required")
    (output / "number-labels.tex").write_text("\n".join(number_labels) + "\n", encoding="utf-8")
    manifest = {"schema_version": "pirc17-reader-v9-presentation-v1",
                "baseline_build_manifest_sha256": digest(BASELINE),
                "renderer_sha256": renderer_hashes, "active_unique_figures": len(records),
                "figures": records, "tex_projections": projections,
                "original_renderer_manifests": legacy_manifests,
                "figure_path_replacements": figure_paths,
                "scientific_artist_data_unchanged": True,
                "new_fits_forecasts_particle_scores_inference_or_map_queries": 0,
                "historical_assets_overwritten": False, "human_acceptance": False}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    result = render(parser.parse_args().output_dir)
    print(json.dumps({"active_figures": result["active_unique_figures"],
                      "projected_TeX_files": len(result["tex_projections"]),
                      "scientific_artist_data_unchanged": True}))
