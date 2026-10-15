"""Render post-hoc aggregate terrain evidence; no model or private cache access."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from scripts.describe_pirc17_terrain import CONFIGS, INDEX_SHA, CACHE_SHA


def validate(data):
    if (data["schema_version"] != "pirc17-terrain-posthoc-description-v1"
            or data["source_index_sha256"] != INDEX_SHA or data["source_cache_sha256"] != CACHE_SHA
            or [r["configuration"] for r in data["rows"]] != CONFIGS):
        raise ValueError("original bound ten-configuration description required")
    p = data["population"]
    if (p["original_blocks"], p["jointly_complete_blocks"], p["original_slots"], p["successful_slots"], p["failed_slots"]) != (46,43,2300,2297,3):
        raise ValueError("explicit original and complete-case denominators required")
    if data["scope"]["registered_full_family_inference"] != "unavailable" or not data["scope"]["posthoc_descriptive_only"]:
        raise ValueError("descriptive presentation cannot replace registered inference")


def render(source, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import TwoSlopeNorm
    data = json.loads(source.read_text(encoding="utf-8"))
    validate(data)
    if output.exists():
        raise ValueError("fresh output directory required")
    output.mkdir(parents=True)
    rows = data["rows"]
    profiles = [r["common_complete_profile"] for r in rows]
    base = profiles[0]
    delta_es = np.array([p["es_by_horizon_m"] for p in profiles]) - np.array(base["es_by_horizon_m"])
    coverage = 100*np.array([p["coverage90_by_horizon"] for p in profiles])
    delta_fde = np.array([p["fde_m"] - base["fde_m"] for p in profiles])
    plt.rcParams.update({"font.size":9, "pdf.fonttype":42, "axes.titlesize":10})
    fig, axes = plt.subplots(1,3,figsize=(6.5,5.9),gridspec_kw={"width_ratios":[1.25,1.25,1]})
    fig.subplots_adjust(left=.20,right=.98,top=.79,bottom=.23,wspace=.44)
    limit = max(1,float(np.abs(delta_es).max()))
    im = axes[0].imshow(delta_es, cmap="RdBu_r",norm=TwoSlopeNorm(vmin=-limit,vcenter=0,vmax=limit),aspect="auto")
    cm = axes[1].imshow(coverage, cmap="YlGnBu",vmin=0,vmax=100,aspect="auto")
    for ax, array in zip(axes[:2], [delta_es,coverage]):
        ax.set_xticks(range(4),["1","5","15","30"])
        ax.set_xlabel("Horizon\n(saved min)")
        ax.set_yticks(range(10), CONFIGS if ax is axes[0] else [""]*10)
        ax.tick_params(length=0)
        for i in range(10):
            for j in range(4):
                dark = abs(array[i,j]) > .65*limit if ax is axes[0] else array[i,j] > 70
                ax.text(j,i,f"{array[i,j]:.1f}",ha="center",va="center",color="white" if dark else "black",fontsize=8.5)
    axes[0].set_title("(a) ES vs base\n(m; lower better)")
    axes[1].set_title("(b) 90% disks\nCoverage (%)")
    axes[2].barh(range(10),delta_fde,color=["#2166ac" if v<0 else "#b2182b" for v in delta_fde])
    axes[2].set_ylim(9.5,-.5)
    axes[2].set_yticks(range(10),[""]*10)
    axes[2].axvline(0,color="black",lw=.7)
    axes[2].set_xlim(min(-25,float(delta_fde.min())-15),float(delta_fde.max())+52)
    for i,value in enumerate(delta_fde):
        axes[2].text(value+3 if value>=0 else 3,i,f"{value:+.1f}",ha="left",va="center",fontsize=8.5)
    axes[2].set_title("(c) 30-min FDE\nvs base (m)")
    axes[2].set_xlabel("Lower\nis better")
    for ax in axes:
        for split in (1.5,5.5):
            ax.axhline(split,color="#777777",lw=.8)
    fig.suptitle("Terrain predictions: 43 complete recording blocks, 5 seeds each\nPost-hoc subset of 46 blocks; 3 failed slots in the original grid",fontsize=10,y=.96)
    fig.colorbar(im,ax=axes[0],orientation="horizontal",fraction=.055,pad=.18,label="ES change (m)")
    fig.colorbar(cm,ax=axes[1],orientation="horizontal",fraction=.055,pad=.18,label="Inclusion (%)")
    # Colour bars shrink only their parent heatmaps. Align the third panel's
    # plotting area too, so each row refers to the same configuration.
    left_pos, right_pos = axes[0].get_position(), axes[2].get_position()
    axes[2].set_position([right_pos.x0,left_pos.y0,right_pos.width,left_pos.height])
    fig.text(.02,.035,"Same selected blocks in every panel; no significance tests or causal attribution.\nLOO: remove a group from all-terrain; LIO: add a group to base.",fontsize=8.5)
    for ext in ("pdf","png"):
        fig.savefig(output/("terrain-evidence."+ext),dpi=180,metadata={"Creator":"PIRC17 saved aggregate renderer", "CreationDate":None, "ModDate":None} if ext=="pdf" else None)
    plt.close(fig)
    for language in ("en","zh"):
        title = ("Terrain predictions on the same 43 complete recording blocks (five seeds each). ES averages four targets; $\\Delta$ES is relative to base. FDE, coverage and area use 30 minutes. Success counts retain all 230 original slots per configuration. These are post-hoc descriptive means, not the registered full-family effects."
                 if language=="en" else "相同43个完整记录块的地形预测（每块五种子）。ES平均四目标，$\\Delta$ES均相对base；FDE、覆盖和面积取30分钟。成功数保留各配置原230槽位分母。这是事后描述均值，不是登记完整家族效应。")
        headers = "Configuration & ES (m) & $\\Delta$ES (m) & FDE (m) & Cover (\\%) & Area (km$^2$) & Success" if language=="en" else "配置 & ES（米） & $\\Delta$ES（米） & FDE（米） & 覆盖（\\%） & 面积（km$^2$） & 成功数"
        text = "\\begin{table}[!htbp]\\centering\n\\caption{"+title+"}\\label{tab:terrain-description}\n\\small\\setlength{\\tabcolsep}{3pt}\n\\begin{tabular}{lrrrrrr}\\toprule\n"+headers+"\\\\\\midrule\n"
        for row,p in zip(rows,profiles):
            text += f"{row['configuration']} & {p['es_m']:.2f} & {p['es_m']-base['es_m']:+.2f} & {p['fde_m']:.2f} & {100*p['coverage90_by_horizon'][-1]:.2f} & {p['area90_by_horizon_km2'][-1]:.3f} & {row['full_grid_successful_slots']}/230\\\\\n"
        text += "\\bottomrule\\end{tabular}\n\\end{table}\n"
        (output/("summary-table-"+language+".tex")).write_text(text,encoding="utf-8")
    manifest = {"schema_version":"pirc17-terrain-description-render-v1", "source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
                "renderer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "common_blocks":43, "original_blocks":46, "new_empirical_execution":False,
                "displayed":{"delta_es_by_horizon_m":delta_es.tolist(),"coverage90_pct":coverage.tolist(),"delta_fde30_m":delta_fde.tolist()},
                "files_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()}}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print("One three-panel terrain figure and bilingual ten-configuration tables rendered from saved aggregate scalars.")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args()
    render(args.source,args.output_dir)
