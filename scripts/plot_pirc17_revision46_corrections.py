"""Versioned R15/R16 presentation repairs; old assets and hashes are untouched."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import plot_pirc17_preliminary, plot_pirc17_method_horizons, plot_pirc17_method_regions


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(output):
    if output.exists():
        raise ValueError("Use a new empty output path; no historical manifest may be replaced")
    output.mkdir(parents=True)
    records = []
    for module, stem, task in (
        (plot_pirc17_preliminary, "preliminary-full-horizons", "R15"),
        (plot_pirc17_method_horizons, "method-horizon-overview", "R16"),
        (plot_pirc17_method_regions, "method-region-overview", "R16"),
    ):
        with tempfile.TemporaryDirectory(prefix="pirc17-presentation-") as temp:
            temporary = Path(temp)
            manifest = module.render(temporary)
            files = {}
            for suffix in (".pdf", ".png"):
                asset = temporary / (stem+suffix)
                shutil.copyfile(asset, output / asset.name)
                files[asset.name] = digest(asset)
            records.append({"task": task, "figure": stem, "renderer": Path(module.__file__).name,
                "renderer_sha256": digest(Path(module.__file__)), "files_sha256": files,
                "original_source_sha256": manifest.get("source_sha256", manifest.get("snapshot_sha256")),
                "presentation_change": "uncropped axis" if task == "R15" else "coverage centred on nominal 90 percent"})
    manifest = {"schema_version": "pirc17-revision46-presentation-corrections-v1",
        "figures": records, "new_fits_forecasts_scores_or_resampling": 0,
        "old_figures_or_historical_hashes_overwritten": False, "human_accepted": False}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    render(parser.parse_args().output_dir)
    print("Three versioned presentation repairs rendered; no new scientific execution.")
