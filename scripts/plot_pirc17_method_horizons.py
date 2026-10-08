"""Display all original primary method horizon aggregates, not new inference.

No private arrays, scoring, fitting, resampling, maps or empirical tests.
All 28 identities remain separate, including references and score aliases.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"
SOURCE_SHA = "8900f3dee68d5fc9cafd5ced2e2394503432d2493251601c0ba9cb771cbefba1"
SEEDS = [20260814, 20260815, 20260816, 20260817, 20260818]
GROUPS = [
    ("Model structure / Full01", "模型结构／Full01",
     ["arm-01/full", "arm-02/pointwise", "arm-03/single_gaussian", "arm-04/gmm_kernel", "arm-05/explicit_decomp"]),
    ("Observation interval / Full01", "观测间隔／Full01",
     ["arm-06/dt30", "arm-06/dt60", "arm-06/dt120", "arm-06/dt300", "arm-06/dt600"]),
    ("Objective / score / Full07", "目标与评分／Full07",
     ["arm-07/full", "arm-08/qmle", "arm-09/mixed", "arm-09/pure_es", "arm-10/d2_mc", "arm-10/d2_closed"]),
    ("Training / adaptation / Full11", "训练与适应／Full11",
     ["arm-11/full", "arm-12/scratch", "arm-14/reptile", "arm-15/drift_only", "arm-15/two_step"]),
    ("Numerical / Full18, Full20", "数值传播／Full18、Full20",
     ["arm-18/full", "arm-19/em", "arm-19/euler", "arm-20/full", "arm-21/mc", "arm-21/crn"]),
    ("Additional reference (not a family)", "额外参考（不是另一比较族）", ["arm-16/full"]),
]
LABELS = {
    "arm-01/full": "Full01", "arm-02/pointwise": "Pointwise mixture",
    "arm-03/single_gaussian": "Single Gaussian", "arm-04/gmm_kernel": "Residual mixture",
    "arm-05/explicit_decomp": "Explicit features", "arm-06/dt30": "30 s observations",
    "arm-06/dt60": "60 s (Full01 replay)", "arm-06/dt120": "120 s observations",
    "arm-06/dt300": "300 s observations", "arm-06/dt600": "600 s observations",
    "arm-07/full": "Full07", "arm-08/qmle": "QMLE", "arm-09/mixed": "Mixed calibration",
    "arm-09/pure_es": "Pure ES calibration", "arm-10/d2_mc": "d2 MC score route",
    "arm-10/d2_closed": "d2 closed score route", "arm-11/full": "Full11",
    "arm-12/scratch": "Scratch", "arm-14/reptile": "Reptile", "arm-15/drift_only": "Drift-only",
    "arm-15/two_step": "Two-step", "arm-16/full": "Full16 (extra reference)",
    "arm-18/full": "Full18", "arm-19/em": "EM (Full18 control)", "arm-19/euler": "Euler (EM alias)",
    "arm-20/full": "Full20", "arm-21/mc": "MC (Full20 control)", "arm-21/crn": "CRN (Full20 control)",
}


def finite(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("finite real saved metrics required; missing values are not zero")
    return value


def project(data):
    if (data["schema_version"] != "pirc17-public-safe-preliminary-method-arithmetic-v1"
            or data["primary_method_rows"] != 6440 or data["independent_blocks"] != 46
            or data["forecast_seeds"] != SEEDS or data["scientific_claim_authorized"] is not False
            or data["independent_raw_output_audit_completed"] is not False):
        raise ValueError("original complete primary preliminary scope required")
    source = data["configs"]
    keys = [r["configuration"] for r in source]
    expected = [slot for _, _, slots in GROUPS for slot in slots]
    if len(keys) != 28 or len(set(keys)) != 28 or set(keys) != set(expected):
        raise ValueError("all 28 original unique identities required; no selected winners")
    index = dict(zip(keys, source))
    rows = []
    for key in expected:
        row = index[key]
        if (row["matrix"] != "NEX326-methods" or row["origin_mode"] != "causal_prefix"
                or row["expected"] != 230 or row["counts"] != {"success": 230}
                or row["missing"] != 0 or row["status"] != "computed"):
            raise ValueError("no failed, missing, secondary-mode or successful-subset profiles")
        es, coverage = row["es_by_time_m"], row["coverage_90_by_time"]
        if (not isinstance(es, list) or not isinstance(coverage, list) or len(es) != 4 or len(coverage) != 4
                or any(finite(v) < 0 for v in es) or any(not 0 <= finite(v) <= 1 for v in coverage)):
            raise ValueError("four finite nonnegative ES and probability-valued coverage entries required")
        rows.append(dict(configuration=key, display_label=LABELS[key], saved_score_rows=230,
                         es_by_time_m=list(es), coverage_90_by_time=list(coverage)))
    return dict(schema_version="pirc17-existing-all-method-horizons-v1",
                original_stage_sha256=SOURCE_SHA, source_capture_utc=data["captured_utc"],
                recording_hash_blocks=46, forecast_seed_ids=SEEDS, primary_saved_score_rows=6440,
                nominal_horizon_minutes=[1, 5, 15, 30],
                target_scope="original nearest observed target slots under registered tolerance, not interpolated exact nominal clocks; previously saved detailed target projection binds three configurations, not all 28 prediction arrays",
                averaging_scope="each cell is the saved equal-block/equal-five-seed mean, not 230 independent observed targets",
                groups=[dict(title=en, title_zh=zh, configurations=slots) for en, zh, slots in GROUPS],
                configs=rows, es_units="m; lower is better, not mean position error",
                coverage_units="fraction; nominal disk probability .90, not higher-is-always-better",
                thirty_minute_es_range_m=[min(r["es_by_time_m"][3] for r in rows), max(r["es_by_time_m"][3] for r in rows)],
                thirty_minute_coverage_range=[min(r["coverage_90_by_time"][3] for r in rows), max(r["coverage_90_by_time"][3] for r in rows)],
                all_thirty_minute_coverages_below_nominal=all(r["coverage_90_by_time"][3] < .9 for r in rows),
                ranges_are_confidence_intervals=False, configs_are_independent_algorithms=False,
                new_fits=0, new_forecasts=0, new_scores=0, new_resampling=0,
                new_per_horizon_inference=0, forecast_arrays_opened=False,
                independent_saved_output_audit_completed=False, scientific_claim_authorized=False,
                original_final_sixteen_figure_inventory_replaced=False)


def table_tex(description, language):
    if language not in ("en", "zh"):
        raise ValueError("bilingual manuscript required")
    title = "Complete method horizon profiles" if language == "en" else "完整方法时域指标"
    intro = ("Every original primary configuration is shown separately, including the six extra reference/replay roles and both score-only routes. Each cell is marginal ES in metres / nominal 90\\% disk coverage in percent, over the same 46 blocks and five simulation seeds. These are descriptive means, not paired tests, confidence intervals or independent algorithms. Target slots retain the original observation-time tolerance; equal display rounding does not certify equal full-precision scores."
             if language == "en" else
             "分别保留全部原方法主配置，包括六个额外参考／回放角色及两个仅评分路线。每格为边际ES（米）／名义90\\%预测圆覆盖率（百分数），平均同一46块、五个模拟种子。这是描述均值，不是配对检验、置信区间或独立算法。目标时刻沿用原观测时间容差；展示舍入相同不认证完整精度的评分相同。")
    caption = ("All 28 saved primary configuration profiles. Cells: ES (m) / 90\\% disk coverage (\\%). ES lower is better; coverage should be interpreted against 90\\% and region size, not maximized alone. Each row uses 230 saved scores, not 230 independent targets."
               if language == "en" else
               "全部28个保存主配置的时域指标。每格：ES（米）／90\\%预测圆覆盖率（\\%）。ES越低越好；覆盖率应结合90\\%标称与区域大小，不单独最大化。每行使用230项保存评分，不是230个独立目标。")
    header = ("Configuration" if language == "en" else "配置")+" & 1 min & 5 min & 15 min & 30 min"
    lines = [r"\subsection{"+title+"}", r"\label{sec:all-method-horizons}", intro,
             r"\begingroup\footnotesize\setlength{\tabcolsep}{4pt}\renewcommand{\arraystretch}{.90}",
             r"\begin{longtable}{@{}p{.25\linewidth}rrrr@{}}",
             r"\caption{"+caption+r"}\label{tab:all-method-horizons}\\",
             r"\toprule", header+r"\\", r"\midrule\endfirsthead",
             r"\multicolumn{5}{l}{"+(r"Table~\thetable\ (continued)" if language == "en" else r"表~\thetable\ （续）")+r"}\\",
             r"\toprule", header+r"\\", r"\midrule\endhead", r"\bottomrule\endfoot"]
    index = {r["configuration"]: r for r in description["configs"]}
    for group in description["groups"]:
        lines.append(r"\multicolumn{5}{l}{\textit{"+group["title" if language == "en" else "title_zh"]+r"}}\\*")
        for key in group["configurations"]:
            row = index[key]
            cells = [row["display_label"], *[f"{es:.2f} / {100*cov:.2f}" for es, cov in zip(row["es_by_time_m"], row["coverage_90_by_time"])]]
            lines.append(" & ".join(cells)+r"\\")
    lines += [r"\end{longtable}", r"\endgroup", ""]
    return "\n".join(lines)


def figure_tex(language):
    caption = ("All 28 primary saved configurations at four nominal target slots; no intermediate-time prediction is added. Left: marginal ES (m), lower is better. Right: empirical nominal 90\\% disk coverage (\\%); 90\\% is the calibration reference, not 100\\%, and region sizes are not shown. Each cell averages the same 46 blocks and five seeds. ES is rounded to whole metres and coverage to one decimal for overview only; full-precision values and all roles remain in the saved projection and Table~\\ref{tab:all-method-horizons}. Row order follows the declared families, not performance. Aliases and distinct Full controls are not pooled; similar rounded cells do not establish equivalence. Descriptive, not new per-horizon tests or final qualification."
               if language == "en" else
               "全部28个主组保存配置在四个名义目标时域的概览；没有新增中间时刻预测。左：边际ES（米），越低越好。右：名义90\\%预测圆的实际覆盖率（\\%）；校准参考是90\\%而不是100\\%，本图不显示区域大小。每格平均同一46块、五个种子。概览ES舍入到整数米，覆盖率保留一位小数；完整精度和全部角色保留于保存投影及表~\\ref{tab:all-method-horizons}。行按登记家族而非性能排序；别名与不同Full对照不合并，舍入相似不证明等价。这是描述展示，不是新增逐时域检验或最终资格。")
    return "\n".join([r"\begin{figure}[p]", r"\centering",
                     r"\includegraphics[height=.79\textheight,width=\linewidth,keepaspectratio]{../figures/method-horizon-overview.pdf}",
                     r"\caption{"+caption+"}", r"\label{fig:all-method-horizons}", r"\end{figure}", ""])


def render(output):
    if output.exists() and any(output.iterdir()):
        raise ValueError("new empty output directory required; old evidence retained")
    raw = (PAPER/"preliminary-method-statistics-v1.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError("original source bytes changed; do not substitute a newer subset")
    description = project(json.loads(raw))
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib.colors import Normalize
    import numpy as np
    output.mkdir(parents=True, exist_ok=True)
    rows = description["configs"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 9.2), sharey=True)
    matrices = [np.array([r["es_by_time_m"] for r in rows]),
                100*np.array([r["coverage_90_by_time"] for r in rows])]
    titles = ["Marginal ES (m)\nLower is better", "90% disk coverage (%)\nNominal reference: 90%, not 100%"]
    for j, (ax, values, title) in enumerate(zip(axes, matrices, titles)):
        cmap = plt.get_cmap("Blues" if j == 0 else "viridis")
        norm = Normalize(vmin=0, vmax=math.ceil(float(values.max())/100)*100 if j == 0 else 100)
        im = ax.imshow(values, cmap=cmap, norm=norm, aspect="auto", interpolation="nearest")
        for row in range(28):
            for col in range(4):
                rgb = cmap(norm(values[row, col]))[:3]
                light = sum(a*b for a, b in zip(rgb, (.2126, .7152, .0722)))
                label = f"{values[row,col]:.0f}" if j == 0 else f"{values[row,col]:.1f}"
                ax.text(col, row, label, ha="center", va="center", fontsize=11,
                        color="black" if light > .55 else "white")
        ax.set_xticks(range(4), ["1", "5", "15", "30"])
        ax.set_xlabel("Nominal target slot (min)")
        ax.set_title(title, fontsize=11)
        count = 0
        for _, _, slots in GROUPS[:-1]:
            count += len(slots)
            ax.axhline(count-.5, color="#111111", linewidth=.8)
        bar = fig.colorbar(im, ax=ax, orientation="horizontal", pad=.065, fraction=.045)
        bar.ax.tick_params(labelsize=9)
        if j == 1:
            bar.set_ticks([0, 30, 60, 90, 100])
    axes[0].set_yticks(range(28), [r["display_label"] for r in rows], fontsize=11)
    axes[1].tick_params(axis="y", left=False, labelleft=False)
    fig.suptitle("All 28 identities: 46 recording blocks x 5 seeds each\n"
                 "Absolute saved means; aliases / references remain separate", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, .95), w_pad=1.3)
    fig.savefig(output/"method-horizon-overview.pdf", metadata={"CreationDate":None,"ModDate":None})
    fig.savefig(output/"method-horizon-overview.png", dpi=170)
    plt.close(fig)
    (output/"method-horizon-description-v1.json").write_text(
        json.dumps(description, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    for language in ("en", "zh"):
        (output/(language+"-method-horizon-tables.tex")).write_text(table_tex(description, language), encoding="utf-8")
        (output/(language+"-method-horizon-overview.tex")).write_text(figure_tex(language), encoding="utf-8")
    names = [p.name for p in output.iterdir()]
    manifest = dict(schema_version="pirc17-existing-method-horizon-render-v1", source_sha256=SOURCE_SHA,
                    renderer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    matplotlib_version=matplotlib.__version__, configs=28, horizon_slots=4,
                    files_sha256={name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in sorted(names)},
                    new_forecasts_scores_fits_resampling_or_horizon_tests=0,
                    independent_saved_output_audit_completed=False, scientific_claim_authorized=False,
                    original_final_sixteen_figure_inventory_replaced=False)
    (output/"method-horizon-manifest-v1.json").write_text(json.dumps(manifest, indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(configs=28, horizon_slots=4,
                         es_range_30m=description["thirty_minute_es_range_m"],
                         coverage_range_30m=description["thirty_minute_coverage_range"], new_experiments=0)))
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir",type=Path,required=True)
    args = parser.parse_args()
    render(args.output_dir)
