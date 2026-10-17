"""Versioned reader figures from frozen aggregates; no scientific execution."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import plot_pirc17_revision46 as old
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.text import Text
import numpy as np

PAPER = ROOT / "paper/pirc17"
SEQUENTIAL = LinearSegmentedColormap.from_list("reader-sequential", ["#fff8de", "#dceee2", "#d4e2f4"])
DIVERGING = LinearSegmentedColormap.from_list("reader-deviation", ["#f5d9c8", "#fcfcf7", "#d9e4f5"])
COVER_CLASSES = {"built": [50], "vegetation": [10, 20, 30, 40, 95, 100], "water/wetland": [80, 90], "valid other": "other valid codes"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def geometry():
    fig = plt.figure(figsize=(6.5, 5.0), layout="constrained")
    grid = fig.add_gridspec(2, 2, height_ratios=[3, 1.5])
    a, b, c = fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1]), fig.add_subplot(grid[1, :])
    a.plot([.2, 2.6], [1.3, 1.3], color="#777777", lw=3)
    a.scatter([1], [.3], color="black")
    a.scatter([1], [1.3], color="#326a9b")
    old.arrow(a, (1, .3), (1, 1.3))
    a.text(1.15, .65, "$d, u$ toward\nnearest point", fontsize=10)
    a.text(.12, 1.5, "Road / river feature", fontsize=10)
    a.text(.12, -.25, "Not a tangent or flow direction", fontsize=9)
    a.set_title("(a) Nearest-point geometry", fontsize=11)
    for y in (.2, .6, 1, 1.4):
        b.plot([.1, 2.5], [y, y+.65], color="#bbbbbb", lw=1)
    origin = np.array([1.1, .6])
    for vector, label, colour in [(np.array([-.28, .96]), "uphill a", "#517349"),
                                  (np.array([-.96, -.28]), "contour q", "#985d39"),
                                  (np.array([.75, .66]), "history h", "#326a9b")]:
        old.arrow(b, origin, origin+vector, color=colour)
        b.text(*(origin+vector+np.array([-.06, .1])), label, fontsize=9)
    b.text(.1, -.25, "$h^T a$, $h^T q$: no slope multiplier", fontsize=9)
    b.set_title("(b) Signed projections", fontsize=11)
    for ax in (a, b):
        ax.set(xlim=(-.1, 2.8), ylim=(-.4, 2.1), aspect="equal")
        ax.axis("off")
    c.axis("off")
    c.set_title("(c) Frozen WorldCover groups and road interaction", fontsize=11)
    for x, (name, codes), colour in zip([0, .24, .54, .8], COVER_CLASSES.items(), ["#f4d8cd", "#d5e8d1", "#d4e2f4", "#ece8dc"]):
        c.text(x, .65, name, fontsize=10, bbox=dict(facecolor=colour, edgecolor="none", pad=4))
        label = ",".join(map(str, codes)) if isinstance(codes, list) else "other valid codes"
        if name == "vegetation":
            label = "10,20,30,40,\n95,100"
        c.text(x, .34, label, fontsize=9)
    c.text(0, -.1, r"$1_{\rm group}\log(1+d/(1\,m))$; nodata is missing, not valid other.", fontsize=10)
    return fig


def design():
    source, data = old.design_matrix()
    plt.close(source)
    fig, ax = plt.subplots(figsize=(6.5, 4.8), layout="constrained")
    ax.imshow(data["retained"], cmap=old.ListedColormap(["#fafafa", "#d4e2f4"]), vmin=0, vmax=1, aspect="auto")
    groups = ["history", "road", "river", "cover", "surface", "road × cover", "surface × history", "road d × u", "river d × u"]
    ax.set_xticks(range(9), groups, rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(10), [f"{n}  ({k}/{2*k}/{2*k+1})" for n, k in zip(old.TERRAIN_ORDER, data["K"])], fontsize=9)
    for i, row in enumerate(data["retained"]):
        for j, value in enumerate(row):
            ax.text(j, i, str(value), color="black", ha="center", va="center", fontsize=9)
    ax.set_title("Retained groups: 1 present, 0 absent\nRow widths: K / 2K / (2K+1)", fontsize=11)
    return fig, data


def overview(inputs, stats, selected):
    fig, data = old.overview(inputs, stats, selected=selected)
    fig.set_size_inches(7.5 if selected else 8.8, 3.5 if selected else 11)
    for ax in fig.axes[:3]:
        im = ax.images[0]
        im.set_cmap(DIVERGING if ax is fig.axes[2] else SEQUENTIAL)
        if ax is fig.axes[2]:
            # A +10 and -10 pp departure have equal absolute colour distance.
            im.set_norm(Normalize(-90, 90))
        for text in ax.texts:
            text.set_color("black")
        ax.set_title(["ES (m): lower is better", "Area (km²): pair with coverage", "Coverage − 90% (pp)"][fig.axes.index(ax)], fontsize=10)
    for item in fig.findobj(Text):
        item.set_fontsize(max(item.get_fontsize(), 10 if selected else 11))
        item.set_color("black")
    data["coverage_colour_bounds_pp"] = [-90, 90]
    data["all_cell_text_black"] = True
    return fig, data


def seed_examples(stats):
    names = ["arm-03/single_gaussian", "arm-04/gmm_kernel", "arm-06/dt600"]
    rows = [next(r for r in stats["comparisons"] if r["candidate"] == n) for n in names]
    fig, ax = plt.subplots(figsize=(6.5, 2.5), layout="constrained")
    for i, r in enumerate(rows):
        ax.plot(r["simultaneous_interval_m"], [i, i], color="#326a9b", lw=2)
        ax.scatter(r["seed_delta_m"], i+np.linspace(-.1, .1, 5), s=25, facecolor="#f3be84", edgecolor="black", lw=.4)
        ax.scatter(r["delta_estimate_m"], i, marker="D", color="#326a9b", s=38, zorder=5)
    ax.set_yticks(range(3), [old.short(r["candidate"])+" − "+old.short(r["control"]) for r in rows], fontsize=9)
    ax.axvline(0, color="black", lw=.8)
    ax.invert_yaxis()
    ax.set_xlabel("Δ ES (m): five seed points, mean diamond, block interval", fontsize=9)
    old.axes_style(ax)
    return fig, rows


def paired_overview(data, metric):
    names = data["configurations"]
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 8.5), layout="constrained")
    values = np.asarray(data[metric])
    deviation = np.asarray(data["coverage_deviation_pp"])
    for j, (ax, matrix, cmap, norm) in enumerate(zip(axes, (values, deviation),
            (SEQUENTIAL, DIVERGING), (Normalize(0, values.max()), Normalize(-90, 90)))):
        im = ax.imshow(matrix, cmap=cmap, norm=norm, aspect="auto")
        ax.set_xticks(range(4), ["1", "5", "15", "30"], fontsize=10)
        ax.set_yticks(range(len(names)), [old.short(n) for n in names] if j == 0 else [], fontsize=10)
        ax.set_xlabel("Nominal minutes", fontsize=10)
        for i in range(len(names)):
            for k in range(4):
                label = f"{matrix[i,k]:+.1f}" if j else (f"{matrix[i,k]:.0f}" if metric == "ES_m" else f"{matrix[i,k]:.2g}")
                ax.text(k, i, label, color="black", ha="center", va="center", fontsize=9.5)
        ax.set_title(("ES (m): lower is better" if metric == "ES_m" else "Mean area (km²)") if not j else "Coverage − 90% (pp)", fontsize=10)
        fig.colorbar(im, ax=ax, orientation="horizontal", shrink=.95, pad=.025)
    return fig


def render(output):
    if output.exists():
        raise ValueError("Use a new versioned figure directory")
    output.mkdir(parents=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    inputs = old.Inputs()
    stats = inputs.read("preliminary-method-statistics-v1.json")
    figures = []
    def save(stem, fig, payload):
        hashes = {}
        for extension in ("pdf", "png"):
            path = output / (stem+"."+extension)
            opts = {"metadata": {"CreationDate": None, "ModDate": None}} if extension == "pdf" else {"dpi": 170}
            fig.savefig(path, **opts)
            hashes[path.name] = digest(path)
        plt.close(fig)
        figures.append({"name": stem, "files_sha256": hashes, "displayed": payload})
    save("geometry", geometry(), {"cover_classes": COVER_CLASSES, "schematic": True, "slope_magnitude_depicted": False})
    fig, value = design(); save("design", fig, value)
    for selected in (False, True):
        fig, value = overview(inputs, stats, selected)
        save("selected-overview" if selected else "full-overview", fig, value)
        if not selected:
            for metric, stem in (("ES_m", "method-horizon-overview"), ("area_km2", "method-region-overview")):
                save(stem, paired_overview(value, metric), {"configurations": value["configurations"], metric: value[metric],
                     "coverage_deviation_pp": value["coverage_deviation_pp"], "coverage_colour_bounds_pp": [-90, 90],
                     "all_cell_text_black": True, "area_colour_scale": "linear"})
    fig, rows = seed_examples(stats); save("seed-examples", fig, rows)
    fig, rows = old.tradeoff(stats)
    fig.set_size_inches(9.5, 8)
    for ax in fig.axes:
        for label in ax.texts:
            name = label.get_text()
            if name == "single_gaussian":
                label.set_text("single Gaussian")
                label.set_position((5, -17))
            elif name == "drift_only":
                label.set_position((-10, -19))
            elif name == "explicit_decomp":
                label.set_text("explicit")
            elif name == "gmm_kernel":
                label.set_text("GMM")
            elif name.startswith("Candidate minus"):
                label.set_text("Candidate minus control\n\nBottom left: both improve\nTop left: ES improves,\n  FDE worsens\nBottom right: reverse\nTop right: both worsen\n\nDescriptive means only.\nNo joint test or ranking.\nAliases are not independent\nalgorithm discoveries.")
    for item in fig.findobj(Text):
        item.set_fontsize(max(item.get_fontsize(), 11))
    save("tradeoff", fig, rows)
    manifest = dict(schema_version="pirc17-reader-figures-v2", source_sha256=inputs.bindings,
                    renderer_sha256=digest(Path(__file__)), original_renderer_sha256=digest(Path(old.__file__)),
                    figures=figures, new_fits_forecasts_particle_scores_resampling_or_map_queries=0,
                    historical_assets_overwritten=False)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    print("Eight versioned reader figures rendered from frozen aggregates.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    render(parser.parse_args().output_dir)
