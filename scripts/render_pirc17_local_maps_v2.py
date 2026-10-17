"""Re-layout the six authorized local maps from the same saved cases.

Explicit private PSDE/runtime sources; no fitting, forecasting or rescoring.
Rereads the three bound routes and display layers for rendering only.
Outputs must be outside this public repository.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib import patheffects
from matplotlib.collections import LineCollection
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Patch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(path, case, prefix, target, route, route_seconds, models, rasters, vectors, slots, bounds_function):
    classes = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]
    colors = ["#006400", "#ffbb22", "#ffff4c", "#f096ff", "#fa0000", "#b4b4b4", "#f0f0f0", "#0064c8", "#0096a0", "#00cf75", "#fae6a0"]
    names = ["Trees", "Shrub", "Grass", "Cropland", "Built-up", "Bare", "Snow/ice", "Water", "Wetland", "Mangrove", "Moss/lichen"]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm([5,15,25,35,45,55,65,75,85,92.5,97.5,105], len(colors))
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    fig, axes = plt.subplots(2, 2, figsize=(6.5, 7.5))
    fig.subplots_adjust(left=.13, right=.98, top=.84, bottom=.31, wspace=.28, hspace=.62)
    history = np.asarray(prefix["terrain_prefix_positions_m"])
    truth = np.asarray(target["positions_m"])
    outline = [patheffects.Stroke(linewidth=4, foreground="white"), patheffects.Normal()]
    present = set()
    for row, k in enumerate(slots):
        observed = route[np.asarray(route_seconds) <= target["elapsed_seconds"][k]]
        bounds = bounds_function(models, k, history, observed)
        for col, model in enumerate(models):
            ax = axes[row, col]
            if "worldcover" in rasters:
                data, extent = rasters["worldcover"]
                ax.imshow(data, extent=extent, origin="upper", cmap=cmap, norm=norm, alpha=.24)
                present.update(np.unique(np.ma.asarray(data).compressed()))
            for key, colour in [("roads", "#777777"), ("rivers", "#087aca")]:
                if vectors.get(key):
                    ax.add_collection(LineCollection(vectors[key], colors=colour, linewidths=.55, alpha=.55))
            ax.plot(observed[:, 0], observed[:, 1], color="black", lw=1.1, path_effects=outline, zorder=4)
            ax.plot(history[:, 0], history[:, 1], color="#007a35", lw=1.8, path_effects=outline, zorder=7)
            ax.scatter(*history[-1], marker="*", s=65, color="#007a35", edgecolor="white", linewidth=.7, zorder=10)
            ax.scatter(*truth[k], marker="X", s=53, color="black", edgecolor="white", linewidth=.8, zorder=11)
            if model["status"] != "success":
                raise ValueError("Original selected case status changed; never replace it")
            p, region = model["positions"][:, k], model["regions"][k]
            ax.scatter(p[:, 0], p[:, 1], s=3.3, color="#aa4900", alpha=.43, zorder=3)
            ax.scatter(*region["center_m"], marker="D", s=35, color="#aa4900", edgecolor="white", linewidth=.6, zorder=9)
            ax.add_patch(Circle(region["center_m"], region["radius_m"], fill=False, edgecolor="#753b92", linestyle="--", lw=1.5, zorder=6))
            nominal = [1, 5, 15, 30][k]
            ax.set_title(f'{model["subject"]} | {nominal} min ({target["elapsed_seconds"][k]:.0f} s)\n'
                         f'Error {region["mean_error_m"]:.1f} m; R90 {region["radius_m"]:.1f} m\n'
                         f'Target {"inside" if region["covered"] else "OUTSIDE"}', fontsize=9, pad=6)
            ax.set(xlim=(bounds[0], bounds[2]), ylim=(bounds[1], bounds[3]), aspect="equal")
            ax.set_xlabel("East (m)", fontsize=9)
            ax.set_ylabel("North (m)" if col == 0 else "", fontsize=9)
            ax.tick_params(labelsize=8.5)
            ax.locator_params(axis="both", nbins=3)
    fig.suptitle(f'Case {case} | base vs all-terrain | fixed seed 20260814\n'
                 'Same metric axes within a row; zoom changes across times', fontsize=10, y=.98)
    handles = [Line2D([], [], color="#007a35", lw=2, label="Visible history"),
               Line2D([], [], marker="*", color="#007a35", lw=0, markersize=9, label="Forecast origin"),
               Line2D([], [], color="black", lw=1, label="Observed future: hindsight only"),
               Line2D([], [], marker="X", color="black", lw=0, label="Actual target"),
               Line2D([], [], marker=".", color="#aa4900", lw=0, label="512 saved particles / panel"),
               Line2D([], [], marker="D", color="#aa4900", lw=0, label="Ensemble mean"),
               Line2D([], [], color="#753b92", linestyle="--", label="Original 90% disk"),
               Line2D([], [], color="#777777", label="Roads (Overture)"),
               Line2D([], [], color="#087aca", label="Rivers (HydroRIVERS)")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.5, .105), ncol=2, fontsize=8.5, frameon=False)
    cover_handles = [Patch(facecolor=c, alpha=.35, label=n) for code, c, n in zip(classes, colors, names) if code in present]
    fig.legend(handles=cover_handles, loc="lower center", bbox_to_anchor=(.5, .025), ncol=4, fontsize=8.5, frameon=False, title="WorldCover display classes", title_fontsize=8.5)
    fig.text(.5, .007, "Future truth is not a prediction input. Four marginal clouds are not a continuous predicted route.", ha="center", fontsize=8.5)
    fig.savefig(path.with_suffix(".pdf"), metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(path.with_suffix(".png"), dpi=170)
    plt.close(fig)


def run(psde, runtime, original, output):
    psde, runtime, original, output = [p.resolve() for p in (psde, runtime, original, output)]
    if output == ROOT or ROOT in output.parents or output.exists():
        raise ValueError("New external private output directory required")
    sys.path.insert(0, str(psde))
    from experiments.pirc17.checkpoint_resume import load
    from experiments.pirc17.protocol_core import read_json, unpack
    from experiments.pirc17.case_review import saved_arrays, observed_route, map_layers
    from experiments.pirc17.case_terrain import comparison_bounds, slot_bounds
    from experiments.pirc17.features import LocalFrame
    source = original / "terrain-manifest.json"
    manifest = read_json(source)
    if (tuple(c["rank"] for c in manifest["cases"]) != (0, 3, 4)
            or manifest["public_route_release_authorized"]):
        raise ValueError("Original private three-case scope required")
    settings, imported = load(runtime)
    if settings["context_sha256"] != manifest["context_sha256"]:
        raise ValueError("Original saved context changed")
    context = unpack(read_json(settings["context"]), expected_sha256=settings["context_sha256"])
    prefixes = {p["sample_id"]: p for p in context["causal_prefixes"]}
    targets = {t["sample_id"]: t for t in unpack(context["scoring_inputs"])["targets"]}
    progress = read_json(runtime / "progress.json")
    output.mkdir(parents=True)
    files = {}
    for letter, case in zip("ABC", manifest["cases"]):
        geo = case["geography"]
        prefix, target = prefixes[geo["sample_id"]], targets[geo["sample_id"]]
        route, evidence = observed_route(settings, prefix, target, geo)
        models = []
        for previous in case["models"]:
            arrays, binding = saved_arrays(settings, imported, progress, case["rank"], subject=previous["subject"], matrix="terrain")
            if binding["array_sha256"] != previous["forecast"]["array_sha256"]:
                raise ValueError("Saved forecast bytes changed")
            positions, seconds = arrays
            if seconds.tolist() != target["elapsed_seconds"]:
                raise ValueError("Original target times changed")
            # Region centres/radii and annotations are copied, not re-scored.
            models.append({**previous, "positions": positions})
        bounds = comparison_bounds(route, models)
        rasters, vectors, _ = map_layers(settings, unpack(context["map_catalog"]), LocalFrame(*prefix["scoring_frame"]), bounds)
        for slots, suffix in [((0, 1), "01-05min"), ((2, 3), "15-30min")]:
            stem = f'case-{case["rank"]:02d}-{suffix}'
            render(output / stem, letter, prefix, target, route, evidence["elapsed_seconds"], models, rasters, vectors, slots, slot_bounds)
            for extension in ("pdf", "png"):
                file = output / (stem+"."+extension)
                files[file.name] = digest(file)
        print(f"Case {letter}: two maps re-laid out from unchanged forecasts", flush=True)
    receipt = dict(schema_version="pirc17-private-map-layout-v2", original_manifest_sha256=digest(source),
                   original_case_projection_sha256=digest(original / "case-horizons.json"),
                   renderer_sha256=digest(Path(__file__)), files_sha256=files,
                   original_case_count=3, original_forecasts=6, particle_marks=12288,
                   new_fits_forecasts_scores_or_resampling=0, display_source_reread=True,
                   public_distribution_authorized=False, local_review_only=True)
    (output / "map-layout-manifest.json").write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("psde", "runtime", "original", "output"):
        parser.add_argument("--"+name, type=Path, required=True)
    run(**vars(parser.parse_args()))
