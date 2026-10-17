"""Render anonymous, already-saved block coverage and region-size descriptions."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper/pirc17/calibration-block-description-v1.json"
SOURCE_SHA = "4c844db56c697bb84b9657e90cb4993ba9dffae62588cc2f29cab8b04f005420"
BASE = ROOT / "paper/pirc17/calibration-description-v1.json"
BASE_SHA = "3d79b46f7cf368547c4e9773c4f843fce4646044eaaec27032994bb982c062f3"
SUBJECTS = ("arm-01/full", "arm-04/gmm_kernel", "arm-06/dt300")
NAMES = ("Full", "GMM kernel", "dt300")
HORIZONS = (60, 300, 900, 1800)
LEVELS = (.5, .8, .9, .95)
EXTRA = ("blocks", "coverage_distribution", "area_km2_distribution",
         "radius_m_distribution", "blocks_by_covered_seed_count")


def quartiles(values):
    q1, median, q3 = statistics.quantiles(values, n=4, method="inclusive")
    return {"minimum": min(values), "q25": q1, "median": median,
            "q75": q3, "maximum": max(values)}


def aggregate_view(value):
    data = copy.deepcopy(value)
    data["schema_version"] = "pirc17-saved-calibration-description-v1"
    data.pop("block_distribution_scope")
    for profile in data["profiles"]:
        for time in profile["horizons"]:
            for level in time["levels"]:
                for key in EXTRA:
                    level.pop(key)
    return data


def validate(data):
    if (data["schema_version"] != "pirc17-saved-calibration-block-description-v1"
            or data["complete_cached_rows"] != 690 or data["independent_blocks"] != 46
            or data["forecast_rng_seeds"] != 5
            or [p["configuration"] for p in data["profiles"]] != list(SUBJECTS)):
        raise ValueError("complete original 690-score three-model grid required")
    if data["scope"]["independent_output_audit"] or any(data["scope"][key] != 0 for key in
            ("new_fits", "new_predictions", "new_particle_scores", "new_tests_or_bootstrap")):
        raise ValueError("saved descriptive evidence only")
    info = data["block_distribution_scope"]
    if (not info["all_four_levels_and_horizons_retained"]
            or info["all_twenty_eight_models_described"]
            or info["seed_count_is_independent_target_count"]
            or info["public_route_case_permission_verified"]):
        raise ValueError("no wider population, independent-target or route-permission claim")
    for profile in data["profiles"]:
        if profile["forecast_rows"] != 230 or profile["independent_blocks"] != 46:
            raise ValueError("complete block/seed grid required")
        if [t["nominal_horizon_seconds"] for t in profile["horizons"]] != list(HORIZONS):
            raise ValueError("original four scoring slots required")
        for time in profile["horizons"]:
            if [v["nominal_level"] for v in time["levels"]] != list(LEVELS):
                raise ValueError("all four saved levels required")
            for value in time["levels"]:
                blocks = value["blocks"]
                if [b["block_number"] for b in blocks] != list(range(1, 47)):
                    raise ValueError("no missing, duplicated or reordered anonymous blocks")
                for block in blocks:
                    if set(block) != {"block_number", "covered_seed_count", "seed_coverage_fraction",
                                      "mean_disk_area_km2", "mean_disk_radius_m"}:
                        raise ValueError("no private identity or coordinate fields")
                    count = block["covered_seed_count"]
                    if type(count) is not int or count not in range(6):
                        raise ValueError("five-seed containment count required")
                    coverage = block["seed_coverage_fraction"]
                    if type(coverage) not in (int, float) or coverage != count / 5:
                        raise ValueError("within-block coverage fraction differs")
                    if any(type(block[key]) not in (int, float) or not math.isfinite(block[key])
                           or block[key] < 0 for key in ("mean_disk_area_km2", "mean_disk_radius_m")):
                        raise ValueError("finite nonnegative block size required")
                counts = [b["covered_seed_count"] for b in blocks]
                if value["blocks_by_covered_seed_count"] != [counts.count(i) for i in range(6)]:
                    raise ValueError("containment histogram differs from complete block records")
                for field, summary, mean in (
                        ("seed_coverage_fraction", "coverage_distribution", "empirical_coverage"),
                        ("mean_disk_area_km2", "area_km2_distribution", "mean_disk_area_km2"),
                        ("mean_disk_radius_m", "radius_m_distribution", "mean_disk_radius_m")):
                    values = [b[field] for b in blocks]
                    if value[summary] != quartiles(values) or not math.isclose(
                            statistics.mean(values), value[mean], rel_tol=1e-12, abs_tol=1e-12):
                        raise ValueError("saved block summary/aggregate mismatch")
            for low, high in zip(time["levels"], time["levels"][1:]):
                for a, b in zip(low["blocks"], high["blocks"]):
                    if any(a[key] > b[key] for key in ("covered_seed_count", "mean_disk_area_km2", "mean_disk_radius_m")):
                        raise ValueError("saved block levels are not nested")


def load_snapshot():
    raw, base = SOURCE.read_bytes(), BASE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA or hashlib.sha256(base).hexdigest() != BASE_SHA:
        raise ValueError("saved evidence hash changed")
    value = json.loads(raw)
    validate(value)
    if aggregate_view(value) != json.loads(base):
        raise ValueError("original published aggregate or provenance changed")
    return value


def table_rows(data):
    validate(data)
    rows = []
    for name, profile in zip(NAMES, data["profiles"]):
        for time in profile["horizons"]:
            value = time["levels"][2]
            coverage, area = value["coverage_distribution"], value["area_km2_distribution"]
            rows.append(" & ".join([
                name, str(time["nominal_horizon_seconds"] // 60),
                f"{100 * coverage['median']:.0f} [{100 * coverage['q25']:.0f}, {100 * coverage['q75']:.0f}]",
                f"{area['median']:.3f} [{area['q25']:.3f}, {area['q75']:.3f}]",
                str(value["blocks_by_covered_seed_count"][0]),
                str(value["blocks_by_covered_seed_count"][5])]))
    return rows


def render(output):
    data = load_snapshot()
    if output.exists() and any(output.iterdir()):
        raise ValueError("new empty output directory required")
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib.ticker import NullFormatter
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    fig, axes = plt.subplots(3, 4, figsize=(8.2, 6.5), sharey=True)
    positive = all(b["mean_disk_area_km2"] > 0 for profile in data["profiles"]
                   for time in profile["horizons"] for b in time["levels"][2]["blocks"])
    limits = []
    for index in range(4):
        areas = [b["mean_disk_area_km2"] for profile in data["profiles"]
                 for b in profile["horizons"][index]["levels"][2]["blocks"]]
        limits.append((min(areas) * .85, max(areas) * 1.18) if positive else (0, max(areas) * 1.05 + 1e-9))
    for row, (name, profile, colour) in enumerate(zip(NAMES, data["profiles"], ("#2166ac", "#b35806", "#1b7837"))):
        for column, time in enumerate(profile["horizons"]):
            ax = axes[row, column]
            blocks = time["levels"][2]["blocks"]
            ax.scatter([b["mean_disk_area_km2"] for b in blocks],
                       [100 * b["seed_coverage_fraction"] for b in blocks],
                       s=20, color=colour, alpha=.6, linewidths=0)
            if positive:
                ax.set_xscale("log")
                ticks = ((.03, .06, .1, .2), (.25, .5, 1), (1, 2, 4, 6), (3, 5, 10, 20))[column]
                ax.set_xticks(ticks, [f"{value:g}" for value in ticks])
                ax.xaxis.set_minor_formatter(NullFormatter())
            ax.set_xlim(*limits[column])
            ax.set_ylim(-5, 105)
            ax.set_yticks([0, 20, 40, 60, 80, 100])
            ax.grid(alpha=.2)
            if row == 0:
                ax.set_title(f"{time['nominal_horizon_seconds'] // 60} min (nominal)")
            if column == 0:
                ax.set_ylabel(f"{name}\nCovered seeds (%)")
    fig.suptitle("Nominal 90% disks: 46 recording blocks per panel; five RNG seeds per target\nSame area scale within each horizon; dots can overlap; descriptive, not calibrated", fontsize=10)
    fig.supxlabel("Mean disk area (km²)" + ("; logarithmic scale" if positive else ""), fontsize=10)
    fig.tight_layout(rect=(0, .03, 1, .94))
    stem = "preliminary-calibration-blocks"
    fig.savefig(output / (stem + ".pdf"), metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(output / (stem + ".png"), dpi=160)
    plt.close(fig)
    manifest = {"schema_version": "pirc17-calibration-block-figure-v1",
                "source_sha256": SOURCE_SHA, "base_aggregate_sha256": BASE_SHA,
                "renderer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "matplotlib_version": matplotlib.__version__, "panel_count": 12,
                "points_per_panel": 46, "shown_probability_level": .9,
                "area_axis_scale": "log" if positive else "linear",
                "shared_area_limits_by_nominal_horizon": limits,
                "figures": {stem: {extension: hashlib.sha256((output / (stem + "." + extension)).read_bytes()).hexdigest()
                                    for extension in ("pdf", "png")}},
                "new_fits_predictions_scores_or_inference": 0,
                "final_audit_performed": False, "public_route_case_permission_verified": False,
                "original_final_sixteen_figure_inventory_replaced": False}
    (output / "calibration-block-figure-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    render(parser.parse_args().output_directory)
    print("Anonymous saved block-coverage/area figure rendered; no new experiments.")
