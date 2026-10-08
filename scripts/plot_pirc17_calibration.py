"""Render pinned saved-region aggregates, with no predictions or inference."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper/pirc17/calibration-description-v1.json"
SOURCE_SHA = "3d79b46f7cf368547c4e9773c4f843fce4646044eaaec27032994bb982c062f3"
SUBJECTS = ("arm-01/full", "arm-04/gmm_kernel", "arm-06/dt300")
HORIZONS = (60, 300, 900, 1800)
LEVELS = (.5, .8, .9, .95)


def validate(data):
    if (data["schema_version"] != "pirc17-saved-calibration-description-v1"
            or data["complete_cached_rows"] != 690 or data["independent_blocks"] != 46
            or data["forecast_rng_seeds"] != 5
            or [p["configuration"] for p in data["profiles"]] != list(SUBJECTS)):
        raise ValueError("original complete 690-score scope required")
    scope = data["scope"]
    if any(scope[k] != 0 for k in ("new_fits", "new_predictions", "new_particle_scores", "new_tests_or_bootstrap")) or scope["independent_output_audit"]:
        raise ValueError("descriptive saved-score evidence only")
    for profile in data["profiles"]:
        if profile["forecast_rows"] != 230 or profile["independent_blocks"] != 46:
            raise ValueError("no partial or successful-subset plot")
        if [t["nominal_horizon_seconds"] for t in profile["horizons"]] != list(HORIZONS):
            raise ValueError("four original nominal targets required")
        for time in profile["horizons"]:
            if [v["nominal_level"] for v in time["levels"]] != list(LEVELS):
                raise ValueError("all four original probability levels required")
            for v in time["levels"]:
                values = [v[k] for k in ("empirical_coverage", "mean_disk_area_km2", "mean_disk_radius_m")]
                if not all(math.isfinite(x) for x in values) or not 0 <= values[0] <= 1 or min(values[1:]) < 0:
                    raise ValueError("finite coverage and nonnegative radius/area required")


def render(output):
    raw = SOURCE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError("pinned saved calibration evidence changed")
    data = json.loads(raw)
    validate(data)
    if output.exists() and any(output.iterdir()):
        raise ValueError("new empty output directory required")
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.8))
    full = data["profiles"][0]
    colours = ("#2166ac", "#b35806", "#1b7837", "#762a83")
    for t, colour in zip(full["horizons"], colours):
        axes[0].plot([100*x for x in LEVELS], [100*v["empirical_coverage"] for v in t["levels"]],
                     "o-", color=colour, label=f"{t['nominal_horizon_seconds']//60} min")
    axes[0].plot([45, 100], [45, 100], "--", color="grey", label="Nominal = observed")
    axes[0].set(xlabel="Nominal disk probability (%)", ylabel="Observed target coverage (%)",
                title="(a) Full: all four levels", xlim=(45, 100), ylim=(0, 103))
    axes[0].set_xticks([50, 80, 90, 95])
    axes[0].legend(fontsize=8, loc="upper left")
    for p, colour, name in zip(data["profiles"], colours, ("Full", "GMM kernel", "dt300")):
        axes[1].plot([1, 5, 15, 30], [t["levels"][2]["mean_disk_area_km2"] for t in p["horizons"]],
                     "o-", color=colour, label=name)
    axes[1].set(xlabel="Nominal forecast horizon (min)", ylabel="Mean 90% disk area (km²)",
                title="(b) Region size: not accuracy alone")
    axes[1].set_xticks([1, 5, 15, 30])
    axes[1].legend(fontsize=9, loc="upper left")
    for ax in axes:
        ax.grid(alpha=.2)
    fig.suptitle("Saved primary scores: 46 blocks x 5 ensembles per model; descriptive only", fontsize=11)
    fig.tight_layout()
    stem = "preliminary-calibration-area"
    fig.savefig(output / (stem + ".pdf"), metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(output / (stem + ".png"), dpi=160)
    plt.close(fig)
    hashes = {ext: hashlib.sha256((output / (stem + "." + ext)).read_bytes()).hexdigest() for ext in ("pdf", "png")}
    manifest = {"schema_version": "pirc17-calibration-presentation-v1", "source_sha256": SOURCE_SHA,
                "renderer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "matplotlib_version": matplotlib.__version__, "figures": {stem: hashes},
                "new_fits_predictions_scores_or_inference": 0, "final_audit_performed": False,
                "original_final_sixteen_figure_inventory_replaced": False}
    (output / "calibration-figure-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    render(args.output_directory)
    print("Pinned calibration/area figure rendered; no new experiments or inference.")
