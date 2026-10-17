"""Describe the original five forecast-seed means, without new inference.

Only two pinned, route-free aggregate JSON files are opened. No particle
arrays, scores, models, private paths, RNGs or bootstrap draws are used.
Seed ranges are NOT confidence intervals or a substitute for the saved
block-level intervals and the pending independent output audit.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/pirc17"
SOURCES = {
    "inference-description-v1.json": "10e56e792fff20aa2f96df9df4f55b5929f2d4ab5d81d05ef54629f151b11253",
    "preliminary-method-statistics-v1.json": "8900f3dee68d5fc9cafd5ced2e2394503432d2493251601c0ba9cb771cbefba1",
}
SEEDS = [20260814, 20260815, 20260816, 20260817, 20260818]
FAMILIES = [
    ("method-model-structure", "Model structure", "模型结构", "arm-01/full",
     ["arm-02/pointwise", "arm-03/single_gaussian", "arm-04/gmm_kernel", "arm-05/explicit_decomp"]),
    ("method-observation-interval", "Observation interval", "观测间隔", "arm-01/full",
     ["arm-06/dt30", "arm-06/dt120", "arm-06/dt300", "arm-06/dt600"]),
    ("method-objective-and-score", "Objective / score", "目标与评分", "arm-07/full",
     ["arm-08/qmle", "arm-09/mixed", "arm-09/pure_es", "arm-10/d2_mc", "arm-10/d2_closed"]),
    ("method-transfer-adaptation", "Training / adaptation", "训练与适应", "arm-11/full",
     ["arm-12/scratch", "arm-14/reptile", "arm-15/drift_only", "arm-15/two_step"]),
    ("method-numerical-propagation", "Numerical propagation", "数值传播", None,
     ["arm-19/em", "arm-19/euler", "arm-21/mc", "arm-21/crn"]),
]
LABELS = {
    "arm-02/pointwise": "Pointwise mixture", "arm-03/single_gaussian": "Single Gaussian",
    "arm-04/gmm_kernel": "Residual mixture", "arm-05/explicit_decomp": "Explicit features",
    "arm-06/dt30": "30 s observations", "arm-06/dt120": "120 s observations",
    "arm-06/dt300": "300 s observations", "arm-06/dt600": "600 s observations",
    "arm-08/qmle": "QMLE", "arm-09/mixed": "Mixed calibration",
    "arm-09/pure_es": "Pure ES calibration", "arm-10/d2_mc": "d2 MC score route",
    "arm-10/d2_closed": "d2 closed score route", "arm-12/scratch": "Scratch",
    "arm-14/reptile": "Reptile", "arm-15/drift_only": "Drift-only",
    "arm-15/two_step": "Two-step", "arm-19/em": "EM", "arm-19/euler": "Euler (EM alias)",
    "arm-21/mc": "MC", "arm-21/crn": "CRN",
}


def finite(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("finite numeric saved effects required; missing values never become zero")
    return value


def summarize(inference, stage):
    if (stage["forecast_seeds"] != SEEDS or stage["independent_blocks"] != 46
            or stage["primary_method_rows"] != 6440
            or stage["scientific_claim_authorized"] is not False
            or stage["independent_raw_output_audit_completed"] is not False
            or inference["scope"]["scientific_claim_authorized"] is not False
            or inference["scope"]["final_independent_saved_output_audit_completed"] is not False):
        raise ValueError("original complete primary stage, not a final verdict, required")
    expected = {(family, candidate): (control or ("arm-18/full" if candidate.startswith("arm-19/")
                                                 else "arm-20/full"))
                for family, _, _, control, candidates in FAMILIES for candidate in candidates}
    indexed = []
    for source in (inference["primary_method_diagnostics"], stage["comparisons"]):
        keys = [(r["family_id"], r["candidate"]) for r in source]
        if len(keys) != 21 or len(set(keys)) != 21 or set(keys) != set(expected):
            raise ValueError("all 21 unique original named comparisons required; no successful subset")
        indexed.append(dict(zip(keys, source)))
    diagnostics, original = indexed
    rows = []
    for key, control in expected.items():
        row, saved = diagnostics[key], original[key]
        if row["control"] != control or saved["control"] != control:
            raise ValueError("original candidate and named control must not change")
        seeds = row["seed_delta_m"]
        if not isinstance(seeds, list) or len(seeds) != 5:
            raise ValueError("five saved effects required in registered seed order")
        values = [finite(v) for v in seeds]
        for field in ("seed_delta_m", "delta_estimate_m", "simultaneous_interval_m"):
            if row[field] != saved[field]:
                raise ValueError("two original projections disagree; do not repair or resample")
        delta = finite(row["delta_estimate_m"])
        bounds = row["simultaneous_interval_m"]
        if not isinstance(bounds, list) or len(bounds) != 2 or finite(bounds[0]) > finite(bounds[1]):
            raise ValueError("original finite ordered block interval required")
        mean = math.fsum(values)/5
        # Same original reduction with a different floating summation order,
        # not a tolerance for changing scientific effects or classifying zero.
        if not math.isclose(mean, delta, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("saved seed means do not reconcile with original paired mean")
        counts = {"negative": sum(v < 0 for v in values), "positive": sum(v > 0 for v in values),
                  "exact_zero": sum(v == 0 for v in values)}
        direction = ("all_exact_zero" if counts["exact_zero"] == 5 else
                     "all_negative" if counts["negative"] == 5 else
                     "all_positive" if counts["positive"] == 5 else "mixed_or_zero")
        rows.append(dict(family_id=key[0], candidate=key[1], control=control,
                         seed_delta_m=values, original_delta_estimate_m=delta,
                         seed_min_m=min(values), seed_max_m=max(values),
                         seed_range_m=max(values)-min(values), sign_counts=counts,
                         direction_summary=direction,
                         original_simultaneous_interval_m=list(bounds)))
    return dict(schema_version="pirc17-existing-five-seed-description-v1",
                source_files_sha256=SOURCES, seed_ids=SEEDS, recording_hash_blocks=46,
                primary_saved_score_rows=6440, comparison_rows=21,
                seed_effect_definition="equal 46 recording-block mean of candidate minus named control weighted ES, holding one registered forecast seed fixed",
                seed_role="five fixed simulation RNG seeds per deterministic fitted configuration, not five refits or independent held-out studies; equal numeric seeds do not imply shared slot streams",
                sign_convention="negative favours candidate; exact-zero counts use unrounded saved values",
                seed_range_is_confidence_interval=False,
                direction_row_counts=dict(Counter(r["direction_summary"] for r in rows)),
                comparisons=rows, new_fits=0, new_forecasts=0, new_particle_scores=0,
                new_resampling_draws=0, forecast_arrays_opened=False,
                independent_saved_output_audit_completed=False, scientific_claim_authorized=False)


def display(value):
    """Metre values, with nonzero sub-centimetre effects never rounded to zero."""
    if value == 0:
        return "0"
    if abs(value) < .0001:
        return f"{value:.2e}".replace("e-0", "e-").replace("e+0", "e+")
    return f"{value:.5f}" if abs(value) < .1 else f"{value:.2f}"


def table_tex(description, language):
    if language not in ("en", "zh"):
        raise ValueError("bilingual source required")
    caption = ("Original five simulation-seed mean differences in weighted ES (m). Each entry averages the same 46 recording blocks. S1--S5 are 20260814--20260818 in order; the final column counts negative/positive/exact-zero entries before display rounding. Negative favours the candidate against its named Full reference. Scientific notation e-5 means times ten to the power minus five. These are not confidence intervals or five independent studies."
               if language == "en" else
               "原五个模拟种子的加权 ES 均值差（米）。每项平均同一46个记录块；S1--S5依次对应20260814--20260818。末列按未舍入原值统计负/正/精确零个数；负值表示相对具名Full对照候选更好。e-5表示乘以十的负五次方。这不是置信区间或五个独立研究。")
    header = ("Candidate & Control & S1 & S2 & S3 & S4 & S5 & $-/+/0$"
              if language == "en" else "候选 & 对照 & S1 & S2 & S3 & S4 & S5 & $-/+/0$")
    lines = [r"\begingroup", r"\footnotesize\setlength{\tabcolsep}{3pt}",
             r"\begin{longtable}{@{}p{.22\linewidth}p{.07\linewidth}rrrrrr@{}}",
             r"\caption{"+caption+r"}\label{tab:method-seed-stability}\\",
             r"\toprule", header+r"\\", r"\midrule\endfirsthead",
             r"\multicolumn{8}{l}{"+(r"Table~\thetable\ (continued)" if language == "en" else r"表~\thetable\ （续）")+r"}\\",
             r"\toprule", header+r"\\", r"\midrule\endhead", r"\bottomrule\endfoot"]
    for family, en, zh, _, _ in FAMILIES:
        lines.append(r"\multicolumn{8}{l}{\textit{"+(en if language == "en" else zh)+r"}}\\")
        for row in description["comparisons"]:
            if row["family_id"] != family:
                continue
            counts = row["sign_counts"]
            cells = [LABELS[row["candidate"]], "Full"+row["control"].split("/")[0].split("-")[1],
                     *[display(v) for v in row["seed_delta_m"]],
                     f"{counts['negative']}/{counts['positive']}/{counts['exact_zero']}"]
            lines.append(" & ".join(cells)+r"\\")
    lines += [r"\end{longtable}", r"\endgroup", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise ValueError("use a new empty output directory; retain earlier evidence")
    sources = {}
    for name, expected in SOURCES.items():
        raw = (PAPER/name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("pinned source bytes changed: "+name)
        sources[name] = json.loads(raw)
    result = summarize(sources["inference-description-v1.json"], sources["preliminary-method-statistics-v1.json"])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/"method-seed-stability-v1.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+"\n", encoding="utf-8")
    for language in ("en", "zh"):
        (args.output_dir/(language+"-method-seed-stability.tex")).write_text(table_tex(result, language), encoding="utf-8")
    print(json.dumps(dict(comparison_rows=len(result["comparisons"]), direction_row_counts=result["direction_row_counts"], new_experiments=0)))


if __name__ == "__main__":
    main()
