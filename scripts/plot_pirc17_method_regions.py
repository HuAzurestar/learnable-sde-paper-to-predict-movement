"""Render complete saved region means; never fit, forecast, score or resample."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from scripts.plot_pirc17_method_horizons import GROUPS, LABELS, SEEDS, SOURCE_SHA as STAGE_SHA

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"
SOURCE_SHA = "43247e7bbec10dc5f087b412c2b1b223f89b9adb33c64f97ba5ce1187a9092d8"
HORIZONS = [60, 300, 900, 1800]
LEVELS = [.5, .8, .9, .95]


def finite(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("finite saved means required; missing values are not zero")
    return value


def validate(data):
    expected = [key for _, _, keys in GROUPS for key in keys]
    if (data["schema_version"] != "pirc17-saved-all-method-regions-v1"
            or data["original_stage_sha256"] != STAGE_SHA
            or data["complete_cached_rows"] != 6440 or data["recording_hash_blocks"] != 46
            or data["forecast_seed_ids"] != SEEDS):
        raise ValueError("original complete 6440-score primary population required")
    scope = data["scope"]
    for field in ("all_twenty_eight_models_described", "all_four_levels_and_horizons_retained",
                  "original_three_model_profiles_exact"):
        if scope[field] is not True:
            raise ValueError("complete original scope required")
    for field in ("new_fits", "new_forecasts", "new_particle_scores", "new_tests_or_bootstrap"):
        if type(scope[field]) is not int or scope[field] != 0:
            raise ValueError("saved descriptive statistics only")
    for field in ("forecast_arrays_opened", "independent_saved_output_audit_completed",
                  "scientific_claim_authorized", "conditional_calibration_established",
                  "mean_area_computed_as_area_of_mean_radius", "size_alone_is_quality_ranking",
                  "all_prediction_array_target_clocks_certified", "physical_utc_certified",
                  "public_route_publication_permission_verified",
                  "original_final_sixteen_figure_inventory_replaced",
                  "private_routes_paths_or_origin_ids_exported"):
        if scope[field] is not False:
            raise ValueError("do not upgrade descriptive evidence or export private origins")
    profiles = data["profiles"]
    keys = [p["configuration"] for p in profiles]
    if len(keys) != 28 or len(set(keys)) != 28 or set(keys) != set(expected):
        raise ValueError("all 28 unique original identities required; no selected winners")
    for profile in profiles:
        if profile["forecast_rows"] != 230 or profile["independent_blocks"] != 46:
            raise ValueError("no partial or successful-subset regions")
        if [h["nominal_horizon_seconds"] for h in profile["horizons"]] != HORIZONS:
            raise ValueError("all four original target slots required")
        for horizon in profile["horizons"]:
            levels = horizon["levels"]
            if [v["nominal_level"] for v in levels] != LEVELS:
                raise ValueError("all four original probability levels required")
            previous = (-1, -1, -1)
            for level in levels:
                coverage, radius, area = (finite(level[field]) for field in
                    ("empirical_coverage", "mean_disk_radius_m", "mean_disk_area_km2"))
                if not 0 <= coverage <= 1 or min(radius, area) < 0:
                    raise ValueError("probability-valued coverage and nonnegative size required")
                # Jensen's inequality, not equality: E[r^2] >= E[r]^2.
                if area + 1e-10 < math.pi * radius**2 / 1e6:
                    raise ValueError("mean disk area cannot be smaller than area of mean radius")
                if any(v + 1e-12 < p for v, p in zip((coverage, radius, area), previous)):
                    raise ValueError("nested saved levels must have nondecreasing aggregate profiles")
                previous = coverage, radius, area
    index = {p["configuration"]: p for p in profiles}
    return [index[key] for key in expected]


def reconcile(data, stage, calibration):
    rows = validate(data)
    old = {r["configuration"]: r for r in stage["configs"]}
    for row in rows:
        for t, horizon in enumerate(row["horizons"]):
            if not math.isclose(horizon["levels"][2]["empirical_coverage"],
                                old[row["configuration"]]["coverage_90_by_time"][t],
                                rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError("original all-28 coverage means changed")
    index = {p["configuration"]: p for p in rows}
    for old_profile in calibration["profiles"]:
        if index[old_profile["configuration"]] != old_profile:
            raise ValueError("previous three-model complete profiles changed")
    return rows


def coverage_envelope(data):
    """Describe the entire frozen grid, not uncertainty or independent models."""
    rows = validate(data)
    summary = []
    for t, horizon in enumerate(HORIZONS):
        for j, nominal in enumerate(LEVELS):
            cells = [row["horizons"][t]["levels"][j] for row in rows]
            coverage = [cell["empirical_coverage"] for cell in cells]
            area = [cell["mean_disk_area_km2"] for cell in cells]
            # Only guard floating arithmetic equality; not a calibration tolerance.
            equal = sum(math.isclose(v, nominal, rel_tol=0, abs_tol=1e-12)
                        for v in coverage)
            below = sum(v < nominal and not math.isclose(
                v, nominal, rel_tol=0, abs_tol=1e-12) for v in coverage)
            summary.append(dict(nominal_horizon_seconds=horizon, nominal_level=nominal,
                configuration_count=len(rows), coverage_min=min(coverage),
                coverage_max=max(coverage), mean_area_min_km2=min(area),
                mean_area_max_km2=max(area), below_nominal=below,
                equal_nominal=equal, above_nominal=len(rows)-below-equal))
    return summary


def coverage_envelope_tex(data, language):
    if language not in ("en", "zh"):
        raise ValueError("bilingual presentation required")
    en = language == "en"
    title = "Coverage across all saved probability levels" if en else "全部保存概率水平的覆盖情况"
    caption = ("All 28 original configuration identities at every saved probability level and target slot. Ranges are minima--maxima of configuration means, not confidence intervals, individual-target ranges or population uncertainty. Each configuration uses the same 46 blocks and five seeds; aliases and Full controls remain included, so counts are not independent algorithms or evidence replications. The final column counts configuration means below/equal to/above the nominal probability, using unrounded values (floating equality tolerance $10^{-12}$ only, not a statistical calibration margin). Exact agreement at one level does not certify calibration. Area is the mean of individual disk areas; no averaging over configurations, new tests or recalibration."
               if en else "全部28个原配置身份在各保存概率水平及目标时域的描述。范围是配置均值的最小—最大值，不是置信区间、单个目标范围或总体不确定性。每配置均用相同46块、五个种子；保留别名和Full对照，故计数不是独立算法数或证据重复数。末列统计配置均值低于／等于／高于名义概率的数量，按未舍入值比较（仅用$10^{-12}$浮点相等容差，不是统计校准界）。单档恰好相等不认证校准。面积平均各预测圆面积；不跨配置求平均，不新增检验或重新校准。")
    header = (r"Minutes & Nominal (\%) & Coverage range (\%) & Area range (km$^2$) & Below/equal/above"
              if en else r"分钟 & 名义（\%） & 覆盖范围（\%） & 面积范围（km$^2$） & 低于／等于／高于")
    lines = [r"\Needspace{.65\textheight}",
             r"\subsection{"+title+"}", r"\label{sec:all-level-coverage}",
             r"\begingroup\small\setlength{\tabcolsep}{4pt}",
             r"\begin{longtable}{@{}rrrrr@{}}",
             r"\caption{"+caption+r"}\label{tab:all-level-coverage}\\",
             r"\toprule", header+r"\\", r"\midrule\endfirsthead",
             r"\multicolumn{5}{l}{"+(r"Table~\thetable\ (continued)" if en else r"表~\thetable\ （续）")+r"}\\",
             r"\toprule", header+r"\\", r"\midrule\endhead", r"\bottomrule\endfoot"]
    for i, row in enumerate(coverage_envelope(data)):
        if i and i % 4 == 0:
            lines.append(r"\midrule")
        lines.append(f"{row['nominal_horizon_seconds']//60} & {100*row['nominal_level']:.0f} & "
            f"{100*row['coverage_min']:.2f}--{100*row['coverage_max']:.2f} & "
            f"{row['mean_area_min_km2']:.3f}--{row['mean_area_max_km2']:.3f} & "
            f"{row['below_nominal']} / {row['equal_nominal']} / {row['above_nominal']}"+r"\\")
    return "\n".join(lines+[r"\end{longtable}", r"\endgroup", ""])


def table_tex(data, language):
    rows = validate(data)
    if language not in ("en", "zh"):
        raise ValueError("bilingual presentation required")
    en = language == "en"
    title = "Complete primary predictive-region sizes" if en else "完整主方法预测区域大小"
    caption = ("All 28 original primary configurations. Each cell: mean radius (m) / mean area (km$^2$) / empirical coverage (\\%) of the nominal 90\\% marginal disk. Each row uses the same 46 blocks and five seeds (230 saved scores), not 230 independent targets. Area averages individual disk areas; it is not the area of the mean radius. Descriptive only; all four probability levels remain in the saved aggregate."
               if en else "全部28个原方法主配置。每格：名义90\\%边际预测圆的平均半径（米）／平均面积（km$^2$）／实际覆盖率（\\%）。每行均为同一46块、五个种子（230份保存评分），不是230个独立目标。面积平均各圆面积，不是平均半径所对应的面积。仅为描述；四个概率水平均保留于保存汇总。")
    header = ("Configuration" if en else "配置") + " & 1 min & 5 min & 15 min & 30 min"
    lines = [r"\subsection{"+title+"}", r"\label{sec:all-method-regions}",
             r"\begingroup\footnotesize\setlength{\tabcolsep}{3pt}\renewcommand{\arraystretch}{.90}",
             r"\begin{longtable}{@{}p{.25\linewidth}rrrr@{}}",
             r"\caption{"+caption+r"}\label{tab:all-method-regions}\\",
             r"\toprule", header+r"\\", r"\midrule\endfirsthead",
             r"\multicolumn{5}{l}{"+(r"Table~\thetable\ (continued)" if en else r"表~\thetable\ （续）")+r"}\\",
             r"\toprule", header+r"\\", r"\midrule\endhead", r"\bottomrule\endfoot"]
    index = {row["configuration"]: row for row in rows}
    for group_en, group_zh, subjects in GROUPS:
        lines += [r"\midrule", r"\multicolumn{5}{l}{\textit{"+(group_en if en else group_zh)+r"}}\\*"]
        for key in subjects:
            values = [h["levels"][2] for h in index[key]["horizons"]]
            cells = [f"{v['mean_disk_radius_m']:.0f} / {v['mean_disk_area_km2']:.3f} / {100*v['empirical_coverage']:.1f}" for v in values]
            lines.append(LABELS[key]+" & "+" & ".join(cells)+r"\\")
    return "\n".join(lines+[r"\end{longtable}", r"\endgroup", ""]) + coverage_envelope_tex(data, language)


def figure_tex(language):
    if language not in ("en", "zh"):
        raise ValueError("bilingual presentation required")
    caption = ("Complete 28-configuration region-size and coverage display at four original target slots. Left: mean nominal 90\\% disk area (km$^2$); colour uses a logarithmic scale to show both short- and long-horizon areas, while cell labels give ordinary areas. Right: empirical target containment (\\%), whose nominal reference is 90\\%, not 100\\%. Neither area nor coverage is a stand-alone quality ranking. Row order follows the declared method families, not observed performance; aliases and Full controls remain distinct. Each cell averages five seeds within each of 46 blocks and then equally over blocks. Descriptive means without new tests, prediction or recalibration; radii and exact values appear in Table~\\ref{tab:all-method-regions} and the saved aggregate."
               if language == "en" else "28配置在四个原目标时域的完整区域大小—覆盖展示。左：名义90\\%预测圆平均面积（km$^2$）；颜色采用对数尺度，以同时显示短、长时域面积，格内标注仍为普通面积。右：实际目标包含率（\\%），标称参考是90\\%而不是100\\%。面积和覆盖率都不能单独作为质量排名。行按登记方法家族而非观察性能排列，保留别名和各Full对照。每格先平均各块五个种子，再等权平均46块。仅为描述均值，没有新增检验、预测或重新校准；半径和精确值见表~\\ref{tab:all-method-regions}及保存汇总。")
    return "\n".join([r"\begin{figure}[p]", r"\centering",
        r"\includegraphics[height=.76\textheight,width=\linewidth,keepaspectratio]{../figures/method-region-overview.pdf}",
        r"\caption{"+caption+"}", r"\label{fig:all-method-regions}", r"\end{figure}", ""])


def render(output):
    if output.exists() and any(output.iterdir()):
        raise ValueError("new empty output directory required")
    raw = (PAPER/"all-method-region-description-v1.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError("pinned complete saved-region evidence changed")
    stage_raw = (PAPER/"preliminary-method-statistics-v1.json").read_bytes()
    if hashlib.sha256(stage_raw).hexdigest() != STAGE_SHA:
        raise ValueError("original complete primary stage changed")
    calibration_raw = (PAPER/"calibration-description-v1.json").read_bytes()
    data = json.loads(raw)
    if hashlib.sha256(calibration_raw).hexdigest() != data["original_three_model_calibration_sha256"]:
        raise ValueError("previous complete three-model evidence changed")
    rows = reconcile(data, json.loads(stage_raw), json.loads(calibration_raw))
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib.colors import LogNorm, TwoSlopeNorm
    import numpy as np
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":11})
    areas = np.array([[h["levels"][2]["mean_disk_area_km2"] for h in p["horizons"]] for p in rows])
    coverage = 100*np.array([[h["levels"][2]["empirical_coverage"] for h in p["horizons"]] for p in rows])
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 9.2), sharey=True)
    norms = [LogNorm(vmin=.005, vmax=20), TwoSlopeNorm(vmin=0, vcenter=90, vmax=100)]
    titles = ["Mean 90% disk area (km²)\nLog colour scale; ordinary labels",
              "90% disk coverage (%)\nNominal reference: 90%, not 100%"]
    for j, (ax, values, norm, title) in enumerate(zip(axes, (areas, coverage), norms, titles)):
        cmap = plt.get_cmap("Blues" if j == 0 else "RdBu_r")
        im = ax.imshow(values, cmap=cmap, norm=norm, aspect="auto", interpolation="nearest")
        for row in range(28):
            for col in range(4):
                value = values[row,col]
                rgb = cmap(norm(value))[:3]
                light = sum(a*b for a,b in zip(rgb,(.2126,.7152,.0722)))
                label = f"{value:.3f}" if j == 0 and value < .1 else (f"{value:.2f}" if j == 0 else f"{value:.1f}")
                ax.text(col,row,label,ha="center",va="center",fontsize=10.5,color="black" if light>.55 else "white")
        ax.set_xticks(range(4),["1","5","15","30"])
        ax.set_xlabel("Nominal target slot (min)")
        ax.set_title(title,fontsize=11)
        count=0
        for _,_,subjects in GROUPS[:-1]:
            count += len(subjects)
            ax.axhline(count-.5,color="#111111",linewidth=.8)
        bar=fig.colorbar(im,ax=ax,orientation="horizontal",pad=.065,fraction=.045)
        ticks = [.01,.1,1,10] if j == 0 else [0,30,60,90,100]
        bar.set_ticks(ticks, labels=[str(t) for t in ticks])
        bar.ax.tick_params(labelsize=9)
    axes[0].set_yticks(range(28),[LABELS[p["configuration"]] for p in rows],fontsize=11)
    axes[1].tick_params(axis="y",left=False,labelleft=False)
    fig.suptitle("All 28 identities: 46 recording blocks x 5 seeds each\n"
                 "Saved marginal disks; size alone is not forecast quality",fontsize=11)
    fig.tight_layout(rect=(0,0,1,.95),w_pad=1.3)
    fig.savefig(output/"method-region-overview.pdf",metadata={"CreationDate":None,"ModDate":None})
    fig.savefig(output/"method-region-overview.png",dpi=170)
    plt.close(fig)
    for language in ("en","zh"):
        (output/(language+"-method-region-tables.tex")).write_text(table_tex(data,language),encoding="utf-8")
        (output/(language+"-method-region-overview.tex")).write_text(figure_tex(language),encoding="utf-8")
    manifest=dict(schema_version="pirc17-existing-method-region-render-v1",source_sha256=SOURCE_SHA,
        renderer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),configs=28,
        target_slots=4,retained_probability_levels=4,displayed_nominal_probability=.9,
        all_level_coverage_summary=coverage_envelope(data),
        matplotlib_version=matplotlib.__version__,new_fits_forecasts_scores_or_inference=0,
        final_audit_performed=False,original_final_sixteen_figure_inventory_replaced=False,
        files_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())})
    (output/"method-region-manifest-v1.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory",type=Path,required=True)
    render(parser.parse_args().output_directory)
    print("Complete28 saved region display rendered;no new experiments or inference.")
