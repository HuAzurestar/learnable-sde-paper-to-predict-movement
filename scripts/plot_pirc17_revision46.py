"""Reader-oriented PIRC17 figures from unchanged public aggregate evidence.

No model fitting, forecasts, particle scoring, bootstrap, maps or route inputs.
Geometry and timing panels are explicitly schematic. All numerical panels
retain named controls and source precision; their manifest binds every input.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, TwoSlopeNorm
from matplotlib.patches import FancyArrowPatch, Rectangle
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper" / "pirc17"
DELTA = 41.100259
TERRAIN_ORDER = ["base", "all-terrain", "loo-road", "loo-river",
                 "loo-worldcover", "loo-surface", "lio-road", "lio-river",
                 "lio-worldcover", "lio-surface"]
K_COUNTS = [2, 28, 19, 23, 20, 20, 7, 7, 6, 10]
COLORS = {"Full": "#326a9b", "inertial": "#bd5c34"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Inputs:
    def __init__(self, paper: Path = PAPER):
        self.paper = paper
        self.bindings: dict[str, str] = {}

    def read(self, name: str):
        path = self.paper / name
        self.bindings[name] = digest(path)
        if path.suffix == ".csv":
            with path.open(encoding="utf-8", newline="") as stream:
                return list(csv.DictReader(stream))
        return json.loads(path.read_text(encoding="utf-8"))


def short(name: str) -> str:
    if name.startswith("arm-"):
        arm, variant = name.split("/", 1)
        return "Full" + arm[-2:] if variant == "full" else variant
    return name


def axes_style(axis):
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(alpha=.18, zorder=0)


def arrow(axis, start, end, color="#326a9b", label=None):
    axis.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>",
                                  mutation_scale=14, linewidth=1.7, color=color))
    if label:
        center = (np.asarray(start) + np.asarray(end)) / 2
        axis.text(center[0], center[1] + .1, label, color=color, fontsize=9)


def geometry():
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.7), layout="constrained")
    ax = axes[0]
    road = np.array([[.2, 1.4], [1.5, 1.4], [2.7, 2.5]])
    ax.plot(*road.T, linewidth=4, color="#777777")
    query, nearest = (1.1, .3), (1.1, 1.4)
    ax.scatter(*query, color="black", zorder=3)
    ax.scatter(*nearest, color=COLORS["Full"], zorder=3)
    arrow(ax, query, nearest, label=r"$d,\ u$ toward nearest point")
    ax.text(.35, 2.6, "Road / river line", fontsize=10)
    ax.text(.2, -.02, "query position", fontsize=9)
    ax.text(.2, -.46, "Not road tangent or river flow", fontsize=9)
    ax.set_title("(a) Nearest-point geometry")
    ax = axes[1]
    for height in (.25, .65, 1.05, 1.45, 1.85, 2.25):
        ax.plot([.15, 2.9], [height, height + .8], color="#bcbcbc", linewidth=1)
    origin = np.array([1.1, 1.05])
    a = np.array([-.28, .96]); q = np.array([-.96, -.28])
    h = np.array([.75, .66])
    for vector, label, color in ((a, "uphill a", "#517349"),
                                  (q, "signed contour q", "#bd5c34"),
                                  (h, "history h", "#326a9b")):
        arrow(ax, origin, origin + vector, color=color)
        end = origin + vector
        ax.text(end[0] + .04, end[1], label, color=color, fontsize=9)
    ax.text(.12, -.22, r"$h^\top a,\ h^\top q$ (no slope multiplier)", fontsize=9)
    ax.text(.12, -.52, r"$q=(-a_n,a_e)$; reversing q flips sign", fontsize=9)
    ax.set_title("(b) Signed surface projections")
    ax = axes[2]
    for index, label in enumerate(("built", "wooded", "open", "other")):
        ax.add_patch(Rectangle((.2, 2.3-index*.52), .58, .35,
                               facecolor=plt.cm.Set2(index), edgecolor="white"))
        ax.text(.88, 2.39-index*.52, label, fontsize=10)
    ax.text(.2, -.04, r"$1_{\mathrm{class}}\log(1+d/(1\,\mathrm{m}))$", fontsize=11)
    ax.text(.2, -.42, "nodata is missing, not valid 'other'", fontsize=9)
    ax.set_title("(c) Cover and road-distance interaction")
    for ax in axes:
        ax.set_xlim(-.08, 3.2); ax.set_ylim(-.65, 3)
        ax.set_aspect("equal"); ax.axis("off")
    return fig


def design_matrix():
    # Selected groups and dependent interactions; all rows retain history.
    cols = ["history", "road", "river", "cover", "surface",
            "road × cover", "surface × history"]
    rows = []
    for name in TERRAIN_ORDER:
        groups = {"history"}
        if name == "all-terrain":
            groups.update(cols[1:5])
        elif name.startswith("loo-"):
            removed = {"worldcover": "cover", "surface": "surface"}.get(name[4:], name[4:])
            groups.update(set(cols[1:5]) - {removed})
        elif name.startswith("lio-"):
            added = {"worldcover": "cover", "surface": "surface"}.get(name[4:], name[4:])
            groups.add(added)
        rows.append([int(col in groups) for col in cols[:5]] +
                    [int({"road", "cover"} <= groups), int("surface" in groups)])
    fig, (ax, note) = plt.subplots(1, 2, figsize=(12, 5.1),
                                   gridspec_kw={"width_ratios": [4, 2]}, layout="constrained")
    ax.imshow(rows, cmap=ListedColormap(["#eeeeee", "#326a9b"]), vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(7), cols, rotation=35, ha="right")
    ax.set_yticks(range(10), [f"{name}   K={k}" for name, k in zip(TERRAIN_ORDER, K_COUNTS)])
    ax.set_xticks(np.arange(-.5, 7, 1), minor=True)
    ax.set_yticks(np.arange(-.5, 10, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=2); ax.tick_params(which="minor", length=0)
    ax.set_title("Retained groups and dependent interactions")
    note.axis("off")
    note.text(0, .97, "Named machine contrasts\n\nOverall: A − B\nLOO: A − (A minus group)\nLIO: (B plus group) − B\n\nΔ < 0: candidate better\nFactor benefit D = −Δ\nCI [l,u] becomes [−u,−l]\n\nAll rows retain history.\nShared fitted base B0;\ncorrection and Q refitted.\n\nK numeric; 2K inputs;\n2K+1 raw regression columns.\nNot a pure information ablation.",
              va="top", fontsize=10, linespacing=1.45)
    return fig, {"groups": cols, "retained": rows, "K": K_COUNTS}


def population(inputs):
    duration = inputs.read("final-cohort-duration-description-v1.json")["stages"]
    speed = inputs.read("final-cohort-speed-description-v1.json")["stages"]
    stages = ["released", "temporal_support", "joint_feature_validity", "selected_primary"]
    labels = ["original windows", "time eligible", "common features valid", "main origins"]
    windows = [duration[s]["windows"] for s in stages]
    blocks = [duration[s]["recording_hash_blocks"] for s in stages]
    if windows != [12370, 127, 106, 46] or blocks != [1094, 89, 73, 46]:
        raise ValueError("Unexpected frozen cohort funnel")
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.5),
                             gridspec_kw={"width_ratios": [1.25, 1, 1]}, layout="constrained")
    ax = axes[0]; ax.axis("off")
    for index, (label, count, block) in enumerate(zip(labels, windows, blocks)):
        y = .94 - index*.23
        ax.text(.5, y, f"{count:,} windows / {block:,} record blocks\n{label}",
                ha="center", va="top", fontsize=10,
                bbox={"boxstyle": "round,pad=.4", "facecolor": "#e5eef4", "edgecolor": "#326a9b"})
        if index < 3:
            ax.annotate("", xy=(.5, y-.16), xytext=(.5, y-.09),
                        arrowprops={"arrowstyle": "->", "color": "#326a9b"})
    ax.set_title("(a) Selection, not independent people")
    plotted = {}
    for ax, kind, title, unit in ((axes[1], "duration", "(b) Recorded follow-up", "seconds"),
                                   (axes[2], "speed", "(c) Saved rate per window", "m/s (retained unit)")):
        values = []
        for s in ("released", "selected_primary"):
            row = duration[s]["followup"] if kind == "duration" else speed[s]["window_median_saved_speed"]
            med, lo, hi = ([row[k] for k in ("median_seconds", "q25_seconds", "q75_seconds")]
                           if kind == "duration" else [row[k] for k in ("median", "q25", "q75")])
            values.append([med, lo, hi])
        for y, (med, lo, hi) in enumerate(values):
            ax.plot([lo, hi], [y, y], color="#326a9b", linewidth=3)
            ax.scatter([med], [y], color="#326a9b", s=45, zorder=3)
            ax.text(med, y+.14, f"{med:.3g} [{lo:.3g}, {hi:.3g}]", ha="center", fontsize=8)
        ax.set_yticks([0, 1], ["original", "selected"]); ax.set_ylim(-.35, 1.65)
        ax.set_xlabel(unit); ax.set_title(title); axes_style(ax)
        plotted[kind] = values
    return fig, {"windows": windows, "blocks": blocks, **plotted}


def inertial(inputs, stats):
    full = next(c for c in stats["configs"] if c["configuration"] == "arm-01/full")
    reference = inputs.read("inertial-primary-description-v1.json")["profiles"][0]
    point = inputs.read("point-error-horizon-description-v1.json")["profiles"]
    horizon = [1, 5, 15, 30]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.9), layout="constrained")
    for ax, metric in zip(axes, ("es_by_time_m", "point_error_by_time_m")):
        for label in ("Full", "inertial"):
            if metric == "es_by_time_m":
                values = full[metric] if label == "Full" else reference[metric]
            else:
                values = next(p for p in point if p["model"].lower() == label.lower())[metric]
            ax.plot(horizon, values, "o-", color=COLORS[label], label=label, linewidth=1.6)
        ax.set_xticks(horizon); ax.set_xlabel("Nominal horizon (minutes)")
        ax.set_ylabel("Energy score (m)" if metric.startswith("es") else "Mean-position error (m)")
        ax.set_title("Lower is better; lines guide the eye"); ax.legend(frameon=False); axes_style(ax)
    return fig, {"nominal_minutes": horizon, "Full_ES_m": full["es_by_time_m"],
                 "inertial_ES_m": reference["es_by_time_m"]}


def tradeoff(stats):
    configs = {c["configuration"]: c for c in stats["configs"]}
    families = list(dict.fromkeys(c["family_id"] for c in stats["comparisons"]))
    fig, axes = plt.subplots(2, 3, figsize=(12, 7.1), layout="constrained")
    points = []
    for ax, family in zip(axes.flat, families):
        rows = [r for r in stats["comparisons"] if r["family_id"] == family]
        for row in rows:
            x = row["delta_estimate_m"]
            y = configs[row["candidate"]]["fde_m"] - configs[row["control"]]["fde_m"]
            ax.scatter(x, y, s=32, color="#326a9b")
            ax.annotate(short(row["candidate"]), (x, y), xytext=(4, 4),
                        textcoords="offset points", fontsize=7)
            points.append({"family": family, "candidate": row["candidate"],
                           "control": row["control"], "delta_ES_m": x, "delta_FDE_m": y})
        ax.axhline(0, color="#666666", linewidth=.8); ax.axvline(0, color="#666666", linewidth=.8)
        controls = ", ".join(dict.fromkeys(short(r["control"]) for r in rows))
        ax.set_title(f"{family.removeprefix('method-')}\nNamed control: {controls}", fontsize=10)
        ax.set_xlabel("Δ ES (m)"); ax.set_ylabel("Δ FDE (m)"); ax.margins(.28); axes_style(ax)
    for ax in axes.flat[len(families):]:
        ax.axis("off")
        ax.text(.05, .9, "Candidate minus named control\n\nBottom left: both improve\nTop left: ES improves, FDE worsens\nBottom right: opposite tradeoff\nTop right: both worsen\n\nDescriptive means, not new tests.\nOverlapping aliases are not\nindependent algorithm discoveries.",
                va="top", fontsize=10)
    return fig, points


def seed_blocks(stats):
    rows = stats["comparisons"]
    fig, ax = plt.subplots(figsize=(10.5, 8.0), layout="constrained")
    highlights = {"arm-03/single_gaussian", "arm-04/gmm_kernel", "arm-06/dt600"}
    for index, row in enumerate(rows):
        lo, hi = row["simultaneous_interval_m"]
        color = "#bd5c34" if row["candidate"] in highlights else "#526776"
        ax.plot([lo, hi], [index, index], color=color, linewidth=2)
        ax.scatter(row["seed_delta_m"], np.full(5, index)+np.linspace(-.12, .12, 5),
                   s=15, color=color, marker="o", zorder=3)
        ax.scatter([row["delta_estimate_m"]], [index], color=color, marker="D", s=28, zorder=4)
    ax.set_yticks(range(len(rows)), [short(r["candidate"])+" − "+short(r["control"]) for r in rows], fontsize=8)
    ax.invert_yaxis(); ax.axvline(0, color="black", linewidth=.8)
    ax.set_xlabel("Δ ES (m): seed points; block simultaneous interval; mean diamond")
    ax.set_title("Consistent seed directions do not establish block-level effects")
    axes_style(ax)
    return fig, [{k: row[k] for k in ("family_id", "candidate", "control", "seed_delta_m", "delta_estimate_m", "simultaneous_interval_m")} for row in rows]


def history_timeline():
    fig, axes = plt.subplots(2, 1, figsize=(11, 5.4), layout="constrained")
    ax = axes[0]
    ax.axvline(0, color="black", linewidth=1); ax.axhline(0, color="#777777", linewidth=1)
    ax.plot([-1.2, -.8, -.4, 0], [0]*4, "o", color="#326a9b", label="observed prefix")
    ax.plot([.5, 1.3, 2.1, 3], [0]*4, "s", color="#bd5c34", label="simulation-only history")
    for x, label in zip([.5, 1.3, 2.1, 3], ["1 min", "5 min", "15 min", "30 min"]):
        ax.annotate(label+" scoring", (x, 0), xytext=(x, .65), ha="center", fontsize=9,
                    arrowprops={"arrowstyle": "->", "color": "#666666"})
    ax.text(-1.3, -.4, "visible observations", fontsize=10)
    ax.text(.12, -.4, "integrator step h ≤ 5 s; forecast horizon H", fontsize=10)
    ax.text(-1.25, 1.24, "future truth → scoring; future-map validity → population selection (separate chain)", fontsize=9)
    ax.set_xlim(-1.5, 3.5); ax.set_ylim(-.65, 1.55); ax.axis("off")
    ax.set_title("(a) Ordering only; horizontal spacing is schematic")
    ax = axes[1]; ax.axis("off")
    colors = ["#326a9b", "#326a9b", "#326a9b"]
    buffers = ["observation / observation / origin", "observation / origin / simulated", "origin / simulated / simulated", "simulated / simulated / simulated"]
    for index, buffer in enumerate(buffers):
        x = index*.25
        for point in range(3):
            simulated = point >= 3-index
            ax.add_patch(Rectangle((x+.015+point*.06, .48), .05, .18,
                                   facecolor="#bd5c34" if simulated else "#326a9b"))
        ax.text(x+.1, .31, buffer.replace(" / ", "\n"), ha="center", fontsize=8)
        if index < 3:
            ax.annotate("", xy=(x+.26, .57), xytext=(x+.205, .57), arrowprops={"arrowstyle": "->"})
    ax.text(.02, .91, "(b) Three-position buffer: observations replaced by simulated positions", fontsize=10)
    ax.text(.02, .03, "Terrain: updates every 5 s; first secant d+5 s, stable span 10 s.\nOrdinary method: adjacent τ resampling cadence (Full τ=60 s); scoring events are not history updates.", fontsize=9)
    return fig


def fit_diagnostics(inputs):
    fits = {r["configuration"]: r for r in inputs.read("fit-diagnostics-v1.json")["terrain"]}
    design = inputs.read("feature-design-description-v1.json")["roles"]["train"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), layout="constrained")
    x = np.arange(10)
    values = {}
    for metric, label, color in (("train_fitted_mse_m2_per_s2", "training", "#326a9b"),
                                  ("validation_fitted_mse_m2_per_s2", "validation", "#bd5c34")):
        values[metric] = [fits[n][metric] for n in TERRAIN_ORDER]
        axes[0].plot(x, values[metric], "o-", label=label, color=color)
    axes[0].set_ylabel("Displacement-rate MSE (m²/s²)"); axes[0].legend(frameon=False)
    axes[0].set_title("Development fit, not independent generalization")
    width = [design[n]["raw_columns_with_masks_and_intercept"] for n in TERRAIN_ORDER]
    rank = [design[n]["raw_design_rank"] for n in TERRAIN_ORDER]
    axes[1].bar(x-.17, width, .34, color="#a3b8c8", label="raw columns")
    axes[1].bar(x+.17, rank, .34, color="#326a9b", label="raw rank")
    axes[1].set_ylabel("Count"); axes[1].legend(frameon=False)
    axes[1].set_title("Rank of original design, not augmented ridge")
    for ax in axes:
        ax.set_xticks(x, TERRAIN_ORDER, rotation=55, ha="right", fontsize=8); axes_style(ax)
    return fig, {**values, "raw_columns": width, "raw_rank": rank}


def overview(inputs, stats):
    configs = {c["configuration"]: c for c in stats["configs"]}
    profiles = inputs.read("all-method-region-description-v1.json")["profiles"]
    names = [p["configuration"] for p in profiles]
    es = np.array([configs[n]["es_by_time_m"] for n in names])
    area, coverage = [], []
    for profile in profiles:
        levels = [next(level for level in h["levels"] if level["nominal_level"] == .9)
                  for h in profile["horizons"]]
        area.append([level["mean_disk_area_km2"] for level in levels])
        coverage.append([100*(level["empirical_coverage"]-.9) for level in levels])
    fig, axes = plt.subplots(1, 3, figsize=(11.8, 10.4), layout="constrained")
    for ax, matrix, title, cmap, norm in zip(axes, (es, area, coverage),
                                            ("ES (m)", "90% mean disk area (km²)", "Coverage − 90% (pp)"),
                                            ("viridis", "viridis", "RdBu_r"),
                                            (None, None, TwoSlopeNorm(vmin=-90, vcenter=0, vmax=90))):
        plotted = ax.imshow(matrix, aspect="auto", cmap=cmap, norm=norm)
        ax.set_title(title); ax.set_xticks(range(4), ["1", "5", "15", "30"])
        ax.set_xlabel("Nominal minutes")
        ax.set_yticks(range(len(names)), [short(n) for n in names] if ax is axes[0] else [])
        fig.colorbar(plotted, ax=ax, shrink=.6, pad=.02)
    return fig, {"configurations": names, "ES_m": es.tolist(), "area_km2": area, "coverage_deviation_pp": coverage}


def forest(stats, micro=False):
    rows = [r for r in stats["comparisons"]
            if (max(abs(r["delta_estimate_m"]), *map(abs, r["simultaneous_interval_m"])) <= .01) == micro]
    fig, ax = plt.subplots(figsize=(10, max(3.0, .35*len(rows)+1.1)), layout="constrained")
    if not micro:
        ax.axvspan(-DELTA, DELTA, color="#c7dcc1", alpha=.4, label="registered practical band")
    for index, row in enumerate(rows):
        lo, hi = row["simultaneous_interval_m"]
        ax.plot([lo, hi], [index, index], color="#326a9b", linewidth=2)
        ax.scatter(row["delta_estimate_m"], index, color="#326a9b", s=28)
    ax.set_yticks(range(len(rows)), [short(r["candidate"])+" − "+short(r["control"]) for r in rows], fontsize=9)
    ax.invert_yaxis(); ax.axvline(0, color="#555555", linewidth=.7)
    ax.set_xlabel("Δ ES (m); candidate minus named control; original simultaneous intervals")
    ax.set_title("Numerical identity diagnostics: ≤ 1 cm scale" if micro else "Effect size relative to the registered practical boundary")
    if not micro:
        ax.legend(frameon=False)
    axes_style(ax)
    return fig, {"comparisons": [r["candidate"] for r in rows], "micro_scale": micro}


def runtime(inputs):
    rows = inputs.read("final-results-v1/tables/runtime_conditions.csv")
    subjects = list(dict.fromkeys((r["matrix"], r["subject"]) for r in rows))
    fig, axes = plt.subplots(1, 3, figsize=(12, 7), layout="constrained")
    payload = []
    for offset, condition, color in ((-.15, "runtime_cold", "#326a9b"), (.15, "runtime_warm", "#bd5c34")):
        for index, key in enumerate(subjects):
            row = next(r for r in rows if (r["matrix"], r["subject"]) == key and r["condition"] == condition)
            summary = json.loads(row["summary"])
            payload.append({"matrix": key[0], "subject": key[1], "condition": condition, "summary": summary})
            for ax, field in zip(axes, ("total_latency_p50_ms", "total_latency_p95_ms", "failure_count")):
                value = summary[field]
                if value is not None:
                    ax.barh(index+offset, value, .28, color=color, label=condition if index == 0 else None)
    for ax, title in zip(axes, ("p50 latency (ms)", "p95 latency (ms), five trials", "Failures / five trials")):
        ax.set_yticks(range(len(subjects)), [short(s[1]) for s in subjects] if ax is axes[0] else [])
        ax.invert_yaxis(); ax.set_title(title); axes_style(ax)
    for ax in axes[:2]:
        ax.set_xscale("log"); ax.legend(frameon=False, fontsize=8)
    return fig, payload


def availability(inputs):
    rows = inputs.read("final-results-v1/tables/comparisons.csv")
    modes = ["causal_prefix", "known_velocity", "point_only"]
    families = list(dict.fromkeys(r["family_id"] for r in rows))
    matrix, labels, qualification = [], [], []
    for family in families:
        values, notes = [], []
        for mode in modes:
            subset = [r for r in rows if r["family_id"] == family and r["origin_mode"] == mode]
            if not subset:
                raise ValueError("Missing original family/mode must not look complete")
            unavailable = any(r["verdict"] == "unavailable" or int(r["failed_rows"]) > 0 or int(r["missing_rows"]) > 0 for r in subset)
            values.append(0 if unavailable else 1)
            counts = dict(Counter(r["verdict"] for r in subset))
            notes.append("unavailable" if unavailable else "complete grid\n"+" / ".join(f"{n} {state}" for state,n in counts.items()))
            qualification.append({"family": family, "mode": mode, "whole_family_unavailable": unavailable,
                                  "verdict_counts": counts, "original_comparison_qualification": subset})
        matrix.append(values); labels.append(notes)
    fig, ax = plt.subplots(figsize=(10, 4.7), layout="constrained")
    ax.imshow(matrix, cmap=ListedColormap(["#c57a56", "#d2dfce"]), vmin=0, vmax=1, aspect="auto")
    ax.set_yticks(range(len(families)), families, fontsize=9)
    ax.set_xticks(range(3), modes)
    for i, row in enumerate(labels):
        for j, text in enumerate(row):
            ax.text(j, i, text, ha="center", va="center", fontsize=7.5)
    ax.set_title("Whole registered family availability; complete grid is not scientific acceptance")
    return fig, {"families": families, "modes": modes, "complete_grid": matrix, "qualification": qualification}


def render(output: Path, inputs: Inputs | None = None):
    inputs = inputs or Inputs()
    stats = inputs.read("preliminary-method-statistics-v1.json")
    if len(stats["configs"]) != 28 or len(stats["comparisons"]) != 21:
        raise ValueError("Expected original 28 identities and 21 primary comparisons")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new empty output directory; retain existing figure evidence")
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "pdf.fonttype": 42, "svg.fonttype": "none"})
    jobs = [
        ("G01", "geometry", geometry),
        ("G02", "design-matrix", design_matrix),
        ("G03", "population", lambda: population(inputs)),
        ("G04", "inertial-horizons", lambda: inertial(inputs, stats)),
        ("G05", "score-error-tradeoff", lambda: tradeoff(stats)),
        ("G06", "seeds-and-blocks", lambda: seed_blocks(stats)),
        ("G07", "history-timeline", history_timeline),
        ("G08", "development-fit", lambda: fit_diagnostics(inputs)),
        ("G09", "recorded-runtime", lambda: runtime(inputs)),
        ("G10", "metric-overview", lambda: overview(inputs, stats)),
        ("G11", "practical-effects", lambda: forest(stats)),
        ("G11", "identity-diagnostics", lambda: forest(stats, micro=True)),
        ("G13", "family-availability", lambda: availability(inputs)),
    ]
    records = []
    for task, name, make in jobs:
        result = make()
        fig, values = result if isinstance(result, tuple) else (result, None)
        files = {}
        for suffix in ("pdf", "png", "svg"):
            path = output / f"revision46-{name}.{suffix}"
            fig.savefig(path, dpi=180, bbox_inches="tight", metadata={"Creator": "PIRC17 reader revision"} if suffix == "pdf" else None)
            files[suffix] = {"name": path.name, "sha256": digest(path)}
        plt.close(fig)
        records.append({"task": task, "figure": name, "files": files, "values": values,
                        "schematic": task in {"G01", "G02", "G07"}})
    manifest = {"schema_version": "pirc17-reader-figures-v1", "source_base_commit": "8cbcb1140d804b25b553ab4e7cda0be3a0d34b1b",
                "source_sha256": inputs.bindings, "renderer_sha256": digest(Path(__file__)),
                "new_fits_forecasts_particle_scores_resampling_or_map_queries": 0,
                "figures": records, "human_accepted": False,
                "G12": "Local real-map work and public boundary are delivered separately; no private case input loaded"}
    (output / "revision46-figure-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = render(args.output_dir.resolve())
    print(json.dumps({"figure_groups": len(result["figures"]), "input_files": len(result["source_sha256"]),
                      "new_experiments": 0, "output": str(args.output_dir)}))


if __name__ == "__main__":
    main()
