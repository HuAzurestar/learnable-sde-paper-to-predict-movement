"""Render bound anonymous point-error profiles; never read private targets."""
from __future__ import annotations

import argparse
import math
from pathlib import Path

from scripts.describe_pirc17_inertial import read_bound

SHA = "73e5eff2550fb1572a8a449500adf3f17c88be219932eb5c343d927be258176c"


def tex(data, language):
    if language not in ("en","zh"):
        raise ValueError("bilingual language required")
    if (data["schema_version"] != "pirc17-saved-center-point-error-description-v1"
            or data["recording_hash_blocks"] != 46 or data["probabilistic_forecasts"] != 690
            or data["deterministic_reference_paths"] != 46 or data["saved_forecast_rows_used"] != 736
            or data["distinct_target_positions"] != 184
            or data["nominal_horizon_seconds"] != [60,300,900,1800]
            or data["nominal_target_tolerance_seconds"] != 30
            or data["actual_target_bounds_seconds"] != [[49,67],[294,305],[889,910],[1785,1814]]):
        raise ValueError("complete original primary point-error scope required")
    gap=data["maximum_original_ade_fde_consistency_gap_m"]
    if type(gap) not in (int,float) or not math.isfinite(gap) or not 0 <= gap < 1e-12:
        raise ValueError("original saved ADE/FDE must match within reported roundoff")
    if any(data[k] for k in ("new_fits","new_forecasts","new_particle_scores","new_bootstrap_or_tests",
        "particle_arrays_opened","raw_trajectories_opened","map_queries","original_saved_scores_changed",
        "independent_saved_output_audit_completed","scientific_claim_authorized",
        "participant_independence_established","physical_clock_or_utc_certified",
        "original_final_figure_inventory_replaced","private_coordinates_clocks_recording_ids_or_paths_exported")):
        raise ValueError("descriptive anonymous saved arithmetic only")
    profiles=data["profiles"]
    if ([p["model"] for p in profiles] != ["Full","GMM","dt300","Inertial"]
            or [p["configuration"] for p in profiles] != ["arm-01/full","arm-04/gmm_kernel","arm-06/dt300",None]):
        raise ValueError("fixed original descriptive models/order required")
    for p,count in zip(profiles,[230,230,230,46]):
        v=p["point_error_by_time_m"]
        if (p["forecast_rows"] != count or p["recording_hash_blocks"] != 46 or len(v) != 4
                or any(type(x) not in (int,float) or not math.isfinite(x) or x < 0 for x in
                       [*v,p["ade_m"],p["fde_m"]])
                or not math.isclose(sum(v)/4,p["ade_m"],rel_tol=1e-12,abs_tol=1e-9)
                or not math.isclose(v[-1],p["fde_m"],rel_tol=1e-12,abs_tol=1e-9)):
            raise ValueError("complete finite saved-consistent point-error profiles required")
    en=language=="en"
    title="Point error at each saved target time" if en else "每个保存目标时刻的位置误差"
    intro=(r"ES evaluates an entire predictive distribution and is not the distance between its mean and the observed position. Table~\ref{tab:point-error-horizons} makes that distance explicit for the already-described Full/GMM/dt300 comparison and the inertial reference; it is not a new ranking of all 28 configurations. Use the original saved scoring-disk center $c_{m,b,s,k}$ (the 512-particle mean, or the deterministic reference position) and the same saved target $y_{b,k}$ in the same origin-local scoring frame. No forecast arrays, new particle scores, target interpolation or simulation are needed."
        if en else r"ES 评价整个预测分布，不是分布均值到真实位置的距离。表~\ref{tab:point-error-horizons} 将此前 Full/GMM/dt300 对照与惯性参考的这个距离单独列出，不构成全部28配置的新排行。使用原保存评分圆盘的中心 $c_{m,b,s,k}$（512粒子的均值，或确定性参考位置）和同一原目标 $y_{b,k}$，两者均在原起点局部评分坐标系中。不需打开预测数组、重新计算粒子评分、插值目标或模拟。")
    definition=(r"For model $m$, average errors over its $S_m$ original seeds within each recording-hash block, then equal-weight all 46 blocks. Here $S_m=5$ for the three probabilistic configurations and $S_m=1$ for the reference; a reference is not counted five times:"
        if en else r"对模型 $m$，先在每个记录哈希块内平均其 $S_m$ 个原预测种子的误差，再等权平均全部46块。三个概率配置的 $S_m=5$，惯性参考的 $S_m=1$，不将一条参考计成五份：")
    equation=[r"\begin{equation}",r"\bar e_{m,k}=\frac{1}{46}\sum_{b=1}^{46}",
              r"\frac{1}{S_m}\sum_{s=1}^{S_m}\lVert c_{m,b,s,k}-y_{b,k}\rVert_2.",
              r"\label{eq:point-error-horizon-mean}",r"\end{equation}"]
    caption=("Mean saved-center displacement error in metres; lower is better. The four columns use the original nominal 1/5/15/30-minute target slots, with actual retained-clock ranges 49--67, 294--305, 889--910 and 1785--1814 s and unchanged 30-second tolerance. Rows are saved forecasts, not independent targets or people. Descriptive values only; no per-horizon inference."
        if en else "原保存均值位置的平均位移误差，单位米，越低越好。四列是原名义1/5/15/30分钟目标；保存时钟实际范围49--67、294--305、889--910、1785--1814秒，原30秒容差不变。份数是保存预测，不是独立目标或人员。仅描述数值，不做分时域推断。")
    header="Model & Rows & 1 min & 5 min & 15 min & 30 min" if en else "模型 & 份数 & 1 分钟 & 5 分钟 & 15 分钟 & 30 分钟"
    names=["Full","GMM","dt300","Inertial" if en else "惯性参考"]
    lines=[r"\FloatBarrier",r"\subsection{"+title+"}",r"\label{sec:point-error-horizons}",intro,"",definition,*equation,"",
           r"\begin{table}[htbp]\centering\small",r"\caption{"+caption+r"}\label{tab:point-error-horizons}",
           r"\begin{tabular}{@{}lrrrrr@{}}\toprule",header+r"\\\midrule"]
    for name,p in zip(names,profiles):
        lines.append(name+f" & {p['forecast_rows']} & "+" & ".join(f"{v:.2f}" for v in p["point_error_by_time_m"])+r"\\")
    lines += [r"\bottomrule\end{tabular}\end{table}",""]
    consistency=(r"All 736 selected saved rows match the same 184 target positions. For every row, the arithmetic mean of these four errors and its last error reproduce the original saved ADE and FDE within floating-point roundoff; the maximum discrepancy is below $10^{-12}$ m. Averaging at each target before taking the Euclidean norm would be a different estimator and is not used."
        if en else r"全部736份所选保存结果对应同一184个目标位置。逐份检查四时刻误差的算术均值及最后一项，在浮点舍入精度内分别复现原保存 ADE 和 FDE，最大差异小于 $10^{-12}$ 米。先跨种子平均位置再取欧氏距离会得到另一估计量，本表未这样处理。")
    interpretation=(r"The inertial reference has lower mean point error at 1 and 5 minutes; Full has lower mean point error at 15 and 30 minutes. GMM has slightly lower descriptive mean errors than Full at all four slots. Conversely, dt300 has larger mean-position errors than Full at every slot despite its lower saved aggregate ES. Thus a distribution-score improvement is not automatically an improvement in mean-path location. Here dt300 denotes the training observation interval, not the integration step. No statistical superiority, independent-participant generalization or deployment accuracy follows from these post-outcome means; original final inference, output audit and review remain pending."
        if en else r"惯性参考在1、5分钟的平均点误差更低，Full 在15、30分钟更低。GMM 在四时域的描述性均值均略低于 Full；相反，dt300 虽有更低的原汇总 ES，四时域均值位置误差却均大于 Full。因此，分布评分改善不自动等于均值路径位置改善。dt300 指训练观测间隔，不是积分步长。事后均值不证明统计优越性、独立人员泛化或部署精度；原最终推断、输出核验及审阅仍待完成。")
    return "\n".join(lines+[consistency,"",interpretation,r"\FloatBarrier",""])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection",type=Path,required=True)
    parser.add_argument("--output-directory",type=Path,required=True)
    args=parser.parse_args()
    data=read_bound(args.projection,SHA)
    outputs={language:tex(data,language) for language in ("en","zh")}
    args.output_directory.mkdir(parents=True,exist_ok=True)
    for language,text in outputs.items():
        with (args.output_directory/(language+"-point-error-horizons.tex")).open("x",encoding="utf-8",newline="\n") as stream:
            stream.write(text)


if __name__ == "__main__":
    main()
