"""Render only the pinned, complete primary-method preliminary aggregates.

No forecasts, targets, private coordinates, fitting, scoring, resampling or
qualification are performed. These three stage figures supplement, not
replace, the registered sixteen final review figures.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "paper/pirc17/preliminary-method-statistics-v1.json"
SNAPSHOT_SHA256 = "8900f3dee68d5fc9cafd5ced2e2394503432d2493251601c0ba9cb771cbefba1"
FAMILIES = (
    ("method-model-structure", "Model structure"),
    ("method-observation-interval", "Observation interval"),
    ("method-objective-and-score", "Objective / score"),
    ("method-transfer-adaptation", "Training / adaptation"),
    ("method-numerical-propagation", "Numerical propagation"),
)
DELTA_M = 41.100259

LABELS = {
    "arm-01/full": "Full reference (60 s)",
    "arm-02/pointwise": "Pointwise mixture",
    "arm-03/single_gaussian": "Single Gaussian",
    "arm-04/gmm_kernel": "Residual mixture",
    "arm-05/explicit_decomp": "Explicit features",
    "arm-06/dt30": "30 s observations",
    "arm-06/dt120": "120 s observations",
    "arm-06/dt300": "300 s observations",
    "arm-06/dt600": "600 s observations",
    "arm-08/qmle": "QMLE label",
    "arm-09/mixed": "Mixed calibration",
    "arm-09/pure_es": "Pure ES calibration",
    "arm-10/d2_mc": "d2 MC score route",
    "arm-10/d2_closed": "d2 closed score route",
    "arm-12/scratch": "Scratch adaptation",
    "arm-14/reptile": "Reptile initialization",
    "arm-15/drift_only": "Drift-only blend",
    "arm-15/two_step": "Two-step label",
    "arm-19/em": "EM",
    "arm-19/euler": "Euler (EM alias)",
    "arm-21/mc": "MC propagation",
    "arm-21/crn": "CRN propagation",
}


def effect_panels(data):
    """Display all 21 comparisons, with diagnostic scales explicitly separate."""
    panels = []
    for family, title in FAMILIES[:4]:
        rows = [r for r in data["comparisons"] if r["family_id"] == family]
        panels.append({"title": title, "control": rows[0]["control"],
                       "diagnostic_zoom": False, "rows": rows})
    numerical = [r for r in data["comparisons"]
                 if r["family_id"] == "method-numerical-propagation"]
    for title, slots in (("Integration aliases", {"arm-19/em", "arm-19/euler"}),
                         ("MC propagation", {"arm-21/mc"}),
                         ("CRN propagation", {"arm-21/crn"})):
        rows = [r for r in numerical if r["candidate"] in slots]
        panels.append({"title": title, "control": rows[0]["control"],
                       "diagnostic_zoom": True, "rows": rows})
    for panel in panels:
        values = [0.] + [v for r in panel["rows"]
                         for v in [*r["simultaneous_interval_m"], r["delta_estimate_m"]]]
        low, high = min(values), max(values)
        padding = .12 * max(high-low, 1e-12)
        panel["x_limits_m"] = [low-padding, high+padding]
        panel["practical_bounds_visible"] = [v for v in (-DELTA_M, DELTA_M)
                                             if low-padding <= v <= high+padding]
    return panels


def absolute_rows(data):
    """One Full anchor plus every candidate; no averaging of repeated controls."""
    configs = {r["configuration"]: r for r in data["configs"]}
    selected = [("Reference", configs["arm-01/full"])]
    for family, title in FAMILIES:
        for row in data["comparisons"]:
            if row["family_id"] == family:
                selected.append((title, configs[row["candidate"]]))
    return selected


def validate(data):
    if (data["schema_version"] != "pirc17-public-safe-preliminary-method-arithmetic-v1"
            or data["primary_method_rows"] != 6440 or data["independent_blocks"] != 46
            or len(data["forecast_seeds"]) != 5 or len(data["configs"]) != 28
            or len(data["comparisons"]) != 21 or data["scientific_claim_authorized"]
            or data["independent_raw_output_audit_completed"]):
        raise ValueError("Original preliminary primary scope required, not final qualification")
    configs = {row["configuration"]: row for row in data["configs"]}
    if len(configs) != 28:
        raise ValueError("Unique original configurations required")
    for row in configs.values():
        if (row["expected"] != 230 or row["counts"] != {"success": 230}
                or row["missing"] != 0 or row["status"] != "computed"):
            raise ValueError("No missing, failed or successful-subset chart")
        for key in ("weighted_es_m", "ade_m", "fde_m"):
            if not math.isfinite(row[key]):
                raise ValueError("Finite unmodified metrics required")
        if (len(row["es_by_time_m"]) != 4 or len(row["coverage_90_by_time"]) != 4
                or any(not math.isfinite(x) for x in row["es_by_time_m"])
                or any(not 0 <= x <= 1 for x in row["coverage_90_by_time"])):
            raise ValueError("Four original scoring times and real coverage required")
    counts = {}
    for row in data["comparisons"]:
        counts[row["family_id"]] = counts.get(row["family_id"], 0) + 1
        candidate, control = configs[row["candidate"]], configs[row["control"]]
        if not math.isclose(candidate["weighted_es_m"] - control["weighted_es_m"],
                            row["delta_estimate_m"], rel_tol=0, abs_tol=1e-8):
            raise ValueError("Contrast sign or source values changed")
        lo, hi = row["simultaneous_interval_m"]
        if not all(math.isfinite(x) for x in (lo, hi, row["delta_estimate_m"])) or lo > hi:
            raise ValueError("Original finite ordered interval required")
    if counts != dict(zip((x[0] for x in FAMILIES), (4, 4, 5, 4, 4))):
        raise ValueError("All five original families required")
    return configs


def load_snapshot():
    raw = SNAPSHOT.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SNAPSHOT_SHA256:
        raise ValueError("Pinned snapshot changed; do not silently replace inputs")
    data = json.loads(raw)
    validate(data)
    return data


def render(output):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    data = load_snapshot()
    if output.exists() and any(output.iterdir()):
        raise ValueError("New empty output directory required; old evidence is retained")
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12})
    plots = {}
    def save(name, fig):
        fig.savefig(output / (name + ".pdf"), metadata={"CreationDate": None, "ModDate": None})
        fig.savefig(output / (name + ".png"), dpi=150)
        plt.close(fig)
        plots[name] = {ext: hashlib.sha256((output / (name + "." + ext)).read_bytes()).hexdigest()
                       for ext in ("pdf", "png")}

    from matplotlib.ticker import FuncFormatter, MaxNLocator
    panels = effect_panels(data)
    fig, axes = plt.subplots(7, 1, figsize=(9, 10),
                             gridspec_kw={"height_ratios": [4, 4, 5, 4, 2, 1.4, 1.4]})
    for ax, panel in zip(axes, panels):
        rows = panel["rows"]
        for i, row in enumerate(rows):
            lo, hi = row["simultaneous_interval_m"]
            ax.plot([lo, hi], [i, i], color="#2166ac", linewidth=2)
            ax.plot(row["delta_estimate_m"], i, "o", color="#2166ac", markersize=4)
        ax.axvline(0, color="black", linewidth=.8)
        for margin in panel["practical_bounds_visible"]:
            ax.axvline(margin, color="#888888", linestyle=":", linewidth=.8)
        ax.set_yticks(range(len(rows)), [LABELS[r["candidate"]] for r in rows], fontsize=12)
        ax.set_xlim(*panel["x_limits_m"])
        ax.set_ylim(len(rows)-.5, -.5)
        ax.xaxis.set_major_locator(MaxNLocator(5))
        ax.tick_params(axis="x", labelsize=9)
        if panel["title"] == "CRN propagation":
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.1e}"))
        elif panel["title"] == "Integration aliases":
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.3f}"))
        control = panel["control"].split("/")[0].replace("arm-", "Full")
        suffix = "; diagnostic zoom" if panel["diagnostic_zoom"] else ""
        ax.set_title(panel["title"] + " vs " + control + suffix, loc="left", fontsize=11)
        ax.grid(axis="x", alpha=.2)
    axes[-1].set_xlabel("Candidate minus control ES (m): left favours candidate", fontsize=11)
    fig.suptitle("21 saved contrasts: 46 recording blocks x 5 forecast seeds\n"
                 "Different horizontal scales; numerical panels are diagnostic zooms\n"
                 "Saved within-family 95% intervals; +/-41.10 m shown only where in range", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 1), h_pad=.6)
    save("preliminary-method-effects", fig)

    display = absolute_rows(data)
    positions, y, previous = [], 0., None
    for group, row in display:
        if previous is not None and group != previous:
            y += .7
        positions.append(y)
        y += 1.
        previous = group
    rows = [row for _, row in display]
    fig, axes = plt.subplots(1, 2, figsize=(9, 8.6), sharey=True)
    for ax, key, title in zip(axes, ("weighted_es_m", "fde_m"),
                              ("Time-weighted energy score (m)", "Mean endpoint error (m)")):
        values = [r[key] for r in rows]
        lo, hi = min(values), max(values)
        span = hi-lo
        ax.set_xlim(lo-.15*span, hi+.45*span)
        for index, (pos, value) in enumerate(zip(positions, values)):
            ax.plot(value, pos, "D" if index == 0 else "o",
                    color="black" if index == 0 else "#2166ac", markersize=5)
            ax.text(value+.025*span, pos, f"{value:.1f}", va="center", fontsize=11)
        for index in range(1, len(display)):
            if display[index][0] != display[index-1][0]:
                ax.axhline((positions[index]+positions[index-1])/2, color="#dddddd", lw=.6)
        ax.set_xlabel(title + "\nLower is better")
        ax.grid(axis="x", alpha=.2)
        ax.set_axisbelow(True)
    axes[0].set_yticks(positions, [LABELS[r["configuration"]] for r in rows], fontsize=12)
    axes[0].invert_yaxis()
    fig.suptitle("Full01 reference and 21 candidates: 230 forecasts each\n"
                 "Zoomed dot axes, labelled means; descriptive, not a global winner test\n"
                 "Six extra Full/replay identities retained separately in the full table", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 1))
    save("preliminary-method-absolute", fig)

    full = next(r for r in rows if r["configuration"] == "arm-01/full")
    times = [1, 5, 15, 30]
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.1))
    axes[0].plot(times, full["es_by_time_m"], "o-", color="#2166ac")
    axes[0].set_ylabel("Marginal energy score (m); lower is better")
    axes[1].plot(times, [100*x for x in full["coverage_90_by_time"]], "o-", color="#2166ac")
    axes[1].axhline(90, color="#b35806", linestyle="--", label="Nominal 90%")
    axes[1].set_ylim(0, 103)
    axes[1].set_ylabel("Empirical disk coverage (%)")
    axes[1].legend(loc="lower right", fontsize=8)
    for ax in axes:
        ax.set_xticks(times)
        ax.set_xlabel("Nominal prediction horizon (min)")
        ax.grid(alpha=.2)
    fig.suptitle("Full01: four original targets; 46 blocks x 5 simulated ensembles", fontsize=10)
    fig.tight_layout()
    save("preliminary-full-horizons", fig)
    manifest = dict(schema_version="pirc17-preliminary-presentation-figures-v2",
                    snapshot_sha256=SNAPSHOT_SHA256, captured_utc=data["captured_utc"],
                    renderer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    matplotlib_version=matplotlib.__version__, figures=plots,
                    new_forecasts=0, new_fits=0, new_scores=0, new_statistical_inference=0,
                    final_audit_completed=False, scientific_claim_authorized=False,
                    original_final_sixteen_figure_inventory_replaced=False,
                    raw_locations_or_trajectory_examples=False,
                    effects_panels=[{k: p[k] for k in
                                    ("title", "control", "diagnostic_zoom", "x_limits_m", "practical_bounds_visible")}
                                    | {"candidates": [r["candidate"] for r in p["rows"]]} for p in panels],
                    absolute_display_slots=[r["configuration"] for r in rows],
                    absolute_unplotted_slots=[r["configuration"] for r in data["configs"]
                                             if r["configuration"] not in {x["configuration"] for x in rows}],
                    repeated_control_metrics_averaged=False,
                    full_twenty_eight_rows_retained_in_source_and_manuscript_table=True)
    (output / "preliminary-figure-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    render(args.output_directory)
    print("Three pinned preliminary figures rendered; no new inference or scientific qualification.")
