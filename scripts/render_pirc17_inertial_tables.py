"""Render a bound anonymous saved-score derivative; no new empirical work."""
from __future__ import annotations

import argparse
import math
from pathlib import Path

from scripts.describe_pirc17_inertial import read_bound

SHA = "80725a94a86bcd58d1bc71f8698221eee5c17e0276e14109425ecdac69f9eb82"


def tex(data, language):
    if language not in ("en", "zh"):
        raise ValueError("bilingual language required")
    if (data["paired_blocks"] != 46 or data["primary_full_forecasts_used"] != 230
            or data["primary_inertial_paths_used"] != 46 or data["auxiliary_inertial_paths_total"] != 58
            or data["nominal_horizon_seconds"] != [60,300,900,1800]
            or data["nominal_target_tolerance_seconds"] != 30):
        raise ValueError("original whole primary population required")
    if any(data[key] for key in ("new_fits", "new_forecasts", "new_particle_scores", "new_bootstrap_or_tests",
                                "independent_saved_output_audit_completed", "scientific_claim_authorized")):
        raise ValueError("descriptive saved-score evidence only")
    profiles = data["profiles"]
    if [p["model"] for p in profiles] != ["inertial", "Full"]:
        raise ValueError("both original reference and Full required")
    for p, count in zip(profiles, [46,230]):
        values = [p[k] for k in ("weighted_es_m", "ade_m", "fde_m")]+p["es_by_time_m"]
        if (p["forecast_rows"] != count or p["recording_hash_blocks"] != 46 or len(p["es_by_time_m"]) != 4
                or any(type(v) not in (int,float) or not math.isfinite(v) or v < 0 for v in values)):
            raise ValueError("complete finite original profiles required")
    en = language == "en"
    title = "A completed constant-velocity reference" if en else "已完成的恒速惯性参考"
    intro = (
        r"The registered inertial reference extrapolates the saved causal initial velocity: $\widehat x^{\mathrm{I}}(t)=x_0+t\widehat v_0$. It is a deterministic path, not a fitted SDE or five repeated particle forecasts. All 58 registered reference paths have saved scores; Tables~\ref{tab:inertial-primary} and~\ref{tab:inertial-horizons} use the entire prespecified 46-block primary population, not the 12 secondary origins. Each reference is paired with Full at the same origin, target identity and actual target times. Average the five Full forecast seeds within each block first, then weight all 46 recording-hash blocks equally; the reference is never counted five times."
        if en else
        r"登记的惯性参考使用保存的因果初始速度外推：$\widehat x^{\mathrm{I}}(t)=x_0+t\widehat v_0$。它是一条确定性路径，不是新拟合的 SDE，也不是五次重复的粒子预测。原58条参考路径均已有保存评分；表~\ref{tab:inertial-primary}、\ref{tab:inertial-horizons} 使用事前规定的完整46块主人群，不包含12个次要起点。每条参考与 Full 的起点、目标身份和实际目标时刻一致。先在每块内平均 Full 的五个预测种子，再等权平均46个记录哈希块；不把一条参考重复计成五份样本。")
    caption = ("Same primary origins and saved target slots. All errors are in metres and lower is better. ES evaluates the predictive distribution; ADE/FDE evaluate its mean path. Inertial is a point mass, so its ES equals displacement error. Counts are saved forecasts, not independent people or fitted models. Descriptive means only; no new confidence interval, significance test or qualification."
               if en else "相同主起点和保存目标时刻。全部误差单位为米，越低越好。ES 评价预测分布，ADE/FDE 评价均值路径；惯性参考是点质量分布，故其 ES 等于位移误差。份数指保存预测，不是独立人员或拟合模型数。仅描述均值，没有新增置信区间、显著性检验或资格结论。")
    header = "Model & Forecasts & Blocks & Weighted ES & ADE & FDE" if en else "模型 & 预测份数 & 块数 & 加权 ES & ADE & FDE"
    names = ["Inertial", "Full"] if en else ["惯性参考", "Full"]
    lines = [r"\FloatBarrier", r"\subsection{"+title+"}", r"\label{sec:inertial-primary}", intro, "",
             r"\begin{table}[htbp]\centering\small", r"\caption{"+caption+r"}\label{tab:inertial-primary}",
             r"\begin{tabular}{@{}lrrrrr@{}}\toprule", header+r"\\\midrule"]
    for name, p in zip(names, profiles):
        lines.append(f"{name} & {p['forecast_rows']} & 46 & {p['weighted_es_m']:.2f} & {p['ade_m']:.2f} & {p['fde_m']:.2f}"+r"\\")
    lines += [r"\bottomrule\end{tabular}\end{table}", ""]
    caption = ("Mean marginal ES in metres at the four nominal target slots; lower is better. Actual retained-clock targets are 49--67, 294--305, 889--910 and 1785--1814 seconds under the unchanged original 30-second tolerance. Neither target interpolation nor a new simulation is used."
               if en else "四个名义时域的平均边际 ES，单位米，越低越好。按未改变的原30秒容差，保存时钟上的实际目标分别为49--67、294--305、889--910、1785--1814秒；没有插值目标或新增模拟。")
    header = "Model & 1 min & 5 min & 15 min & 30 min" if en else "模型 & 1 分钟 & 5 分钟 & 15 分钟 & 30 分钟"
    lines += [r"\begin{table}[htbp]\centering\small",r"\caption{"+caption+r"}\label{tab:inertial-horizons}",
              r"\begin{tabular}{@{}lrrrr@{}}\toprule",header+r"\\\midrule"]
    for name, p in zip(names, profiles):
        lines.append(name+" & "+" & ".join(f"{v:.2f}" for v in p["es_by_time_m"])+r"\\")
    lines += [r"\bottomrule\end{tabular}\end{table}", ""]
    delta = data["full_minus_inertial_m"]
    if en:
        paragraph = f"Full-minus-inertial mean differences are {delta['weighted_es_m']:.2f} m for weighted ES, {delta['ade_m']:.2f} m for ADE and {delta['fde_m']:.2f} m for FDE. Full has strictly lower weighted ES in {data['strictly_lower_full_weighted_es_blocks']} of 46 blocks. However, the inertial reference has lower mean ES at 1 and 5 minutes, whereas Full has lower mean ES at 15 and 30 minutes. Thus the aggregate benefit is not uniform across horizons."
        limits = r"These are post-outcome descriptive comparisons of existing scores, not a registered component contrast or an independently audited superiority claim. No inference is made from the 34/46 count; recording hashes do not certify independent participants. The original validation-based $\delta=41.100259$ m is not recalibrated from this final-evaluation reference. Original output verification, final cards and human review remain pending; no superiority over the cited external models or deployment calibration follows."
    else:
        paragraph = f"Full 减惯性参考的均值差为：加权 ES {delta['weighted_es_m']:.2f} 米、ADE {delta['ade_m']:.2f} 米、FDE {delta['fde_m']:.2f} 米。46块中有{data['strictly_lower_full_weighted_es_blocks']}块的 Full 加权 ES 严格更低。但1、5分钟的惯性平均 ES 更低，15、30分钟的 Full 更低，因此汇总收益并非所有时域都一致。"
        limits = r"这是对既有评分的事后描述，不是登记的组件对比或独立核验后的优越性结论。不从34/46计数作统计推断，记录哈希也不认证独立参与者。原验证数据确定的 $\delta=41.100259$ 米不按此次最终评估惯性均值重新设定。原输出核验、最终卡片与人工审阅仍待完成；不能据此声称优于引用的外部模型或已满足部署校准。"
    return "\n".join(lines+[paragraph,"",limits,r"\FloatBarrier",""])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    data = read_bound(args.projection, SHA)
    outputs = {language: tex(data,language) for language in ("en","zh")}
    args.output_directory.mkdir(parents=True,exist_ok=True)
    for language, text in outputs.items():
        (args.output_directory/(language+"-inertial-primary-comparison.tex")).write_text(text,encoding="utf-8",newline="\n")


if __name__ == "__main__":
    main()
