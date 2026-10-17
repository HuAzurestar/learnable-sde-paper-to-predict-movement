"""Typeset all existing public metric rows without scoring or selecting results.

Additional manuscript inputs, not replacements for the original 16 CSVs,
16 figure groups or paired/cost TeX fragments. Original audited cards must be
independently pinned; a self-consistent hash alone is not empirical authority.
No manuscript, PDF, acceptance status or source result is edited here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import uuid

from scripts import aggregate_pirc17 as source
from scripts import render_pirc17_paper_tables as tex

VERSION = "pirc17-paper-metric-fragments-v1"
LEVELS = (.5, .8, .9, .95)


def denominator(row):
    keys = ("expected_forecasts", "available_score_rows", "missing_score_rows")
    values = [row[k] for k in keys]
    if any(type(v) is not int or v < 0 for v in values):
        raise ValueError("nonnegative integer metric denominators required")
    if values[0] != values[1] + values[2]:
        raise ValueError("expected metric rows must equal available plus missing")
    counts = row["counts_by_status"]
    if any(type(v) is not int or v < 0 for v in counts.values()) or sum(counts.values()) != values[1]:
        raise ValueError("all available metric row statuses required")
    return " / ".join(str(v) for v in values)


def subject(row):
    return tex.tex_text(row["matrix"]) + r"\newline " + tex.tex_text(row["configuration"])


def disposition(row, language):
    label = tex.translated(("expected / available / missing: ", "计划／有记录／缺失："), language)
    return (subject(row) + r"\newline " + tex.tex_text(row["status"]) +
            r"\newline " + tex.tex_text(label + denominator(row)) +
            r"\newline " + tex.status_counts(row["counts_by_status"]))


def absolute_fragment(name, rows, language):
    caption = tex.translated((
        "Absolute recorded prediction metrics: " + tex.MODE_NAMES[rows[0]["origin_mode"]][0] +
        ". All five metrics are distances in metres; lower is better for the "
        "defined metric, not a statistical superiority claim. Distributional ES "
        "is distinct from mean-position ADE/FDE and weighted displacement error. "
        "Path ES uses the original trajectory estimator, not a best-particle path. "
        "All planned, available, missing and failed row statuses are retained; "
        "unavailable metrics are --, never successful-subset means or zero errors. "
        "Recording-hash groups and forecast seeds are not independent participants.",
        "保存绝对预测指标：" + tex.MODE_NAMES[rows[0]["origin_mode"]][1] +
        "。五项指标单位均为米，各自越小越好，不表示统计优势。分布ES不同于均值位置"
        "ADE/FDE和时间加权位移误差；路径ES保留原轨迹估计器，不选择最优粒子轨迹。"
        "计划、有记录、缺失和失败状态完整保留；不可用指标为--，不取成功子集均值或零误差。"
        "记录哈希组及预测种子不等于独立参与者。"), language)
    headers = tex.translated((
        ["Matrix / configuration; disposition", "Weighted ES", "Grid ADE",
         "Weighted position error", "FDE", "Path ES"],
        ["矩阵／配置；状态", "加权ES", "网格ADE", "加权位置误差", "FDE", "路径ES"]), language)
    cells = [[disposition(row, language)] + [tex.number(row[key]) for key in source.METRICS]
             for row in rows]
    return tex.longtable(name, caption, headers, [.31, .11, .11, .13, .11, .12], cells,
                         tex.translated(("continued", "续表"), language))


def elapsed_range(value):
    if value is None:
        return "--"
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError("two original elapsed-time endpoints required")
    endpoints = [tex.number(v) for v in value]
    if any(v is None for v in value) or value[0] > value[1]:
        raise ValueError("ordered recorded elapsed-time endpoints required")
    return "[" + ", ".join(endpoints) + "]"


def time_fragment(name, rows, language):
    caption = tex.translated((
        "Recorded timewise distribution metrics: " + tex.MODE_NAMES[rows[0]["origin_mode"]][0] +
        ". Original nominal target slots are 1/5/15/30 minutes; the original "
        "actual elapsed-time range is shown in seconds, not an interpolated target. "
        "ES is a distance in metres (lower is better). H is marginal position "
        "entropy in nats on the original fixed grid, not accuracy, joint path "
        "entropy or a lower-is-better ranking. These are repeated views of the "
        "same forecast rows, not new independent samples or per-horizon tests. "
        "Unavailable fields stay --; all original dispositions remain explicit.",
        "保存逐时刻分布指标：" + tex.MODE_NAMES[rows[0]["origin_mode"]][1] +
        "。原名义目标为1/5/15/30分钟，实际经过时间范围以秒显示，不插值构造目标。"
        "ES单位为米、越小越好；H为原固定网格的位置边缘熵（nat），不是准确率、联合路径熵"
        "或越小越好的排名。各时刻是同一预测行的重复视图，不增加独立样本或时域检验。"
        "不可用项保留--及原全部状态。"), language)
    headers = tex.translated((
        ["Matrix / configuration; disposition", "Nominal min", "Actual seconds",
         "ES (m)", "H (nats)"],
        ["矩阵／配置；状态", "名义分钟", "实际秒", "ES（米）", "H（nat）"]), language)
    cells = [[disposition(row, language), tex.number(row["nominal_seconds"] / 60),
              elapsed_range(row["actual_elapsed_seconds_range"]),
              tex.number(row["energy_score_m"]), tex.number(row["position_entropy_nats"])]
             for row in rows]
    return tex.longtable(name, caption, headers, [.40, .10, .17, .11, .11], cells,
                         tex.translated(("continued", "续表"), language))


def region_fragment(name, rows, language):
    caption = tex.translated((
        "Recorded position-region diagnostics: " + tex.MODE_NAMES[rows[0]["origin_mode"]][0] +
        ". Every original 1/5/15/30-minute target retains all four nominal "
        r"50/80/90/95\% regions. Coverage is the original observed fraction, not "
        "a promised probability, per-level confidence interval or independent "
        "sample count. Mean area is in square metres; smaller area is not better "
        "without coverage. These repeated time/level views do not multiply "
        "forecast or participant counts. -- means unavailable, not zero. "
        "No coverage, quantile, entropy or region is recomputed.",
        "保存位置区域诊断：" + tex.MODE_NAMES[rows[0]["origin_mode"]][1] +
        r"。每个原1/5/15/30分钟目标保留50/80/90/95\%四个名义区域。覆盖率为原观测比例，"
        "不是承诺概率、各层置信区间或独立样本数。平均面积单位为平方米，面积更小"
        "不自动表示更好，须结合覆盖率。时刻和区域层重复视图不增加预测或参与者数量。"
        "--表示不可用，不是零；不重算覆盖率、分位数、熵或区域。"), language)
    headers = tex.translated((
        ["Matrix / configuration; disposition", "Nominal min", "Region level",
         "Observed coverage", r"Mean area ($\mathrm{m}^2$)"],
        ["矩阵／配置；状态", "名义分钟", "名义区域层", "观测覆盖率", r"均值面积（$\mathrm{m}^2$）"]), language)
    cells = []
    for row in rows:
        coverage = row["coverage"]
        if coverage is not None:
            if not isinstance(coverage, list) or len(coverage) != len(LEVELS):
                raise ValueError("all four original region levels required")
            levels = {r["level"]: r for r in coverage}
            if len(levels) != len(LEVELS) or set(levels) != set(LEVELS):
                raise ValueError("all four unique original region levels required")
        else:
            levels = {}
        for level in LEVELS:
            recorded = levels.get(level)
            rate = None if recorded is None else recorded["coverage_rate"]
            area = None if recorded is None else recorded["mean_area_m2"]
            cells.append([disposition(row, language),
                          tex.number(row["nominal_seconds"] / 60),
                          tex.number(level), tex.number(rate), tex.number(area)])
    return tex.longtable(name, caption, headers, [.40, .09, .10, .14, .16], cells,
                         tex.translated(("continued", "续表"), language))


def fragments(cards, *, software_fixture=False):
    projected = source.project(cards)
    exact = {key: projected[key] for key in ("accuracy", "accuracy_times")}
    files, counts = {}, {}
    for language in tex.LANGUAGES:
        prefix = ("% Public-card metric formatting only; not manuscript integration or acceptance.\n")
        if software_fixture:
            prefix += ("% SOFTWARE FIXTURE ONLY. Not experimental evidence.\n" +
                       r"\paragraph{" + tex.translated((
                           "SOFTWARE FIXTURE ONLY -- no experimental evidence.",
                           "仅合成软件测试数据，不是实验结果。"), language) + "}\n")
        for mode in source.MODES:
            absolute = [r for r in exact["accuracy"] if r["origin_mode"] == mode]
            # The original time projection omits available_score_rows. Copy
            # that recorded denominator from the exact same table axis; do
            # not change the original projection or infer it from successes.
            by_id = {r["table_id"]: r for r in absolute}
            times = []
            for row in exact["accuracy_times"]:
                if row["origin_mode"] != mode:
                    continue
                parent = by_id[row["table_id"]]
                if any(row[key] != parent[key] for key in (
                        "status", "expected_forecasts", "missing_score_rows", "counts_by_status")):
                    raise ValueError("time view differs from its original metric denominator")
                times.append(dict(row, available_score_rows=parent["available_score_rows"]))
            if len(absolute) != 40 or len(times) != 160:
                raise ValueError("all 40 configurations and four time slots per mode required")
            for kind, rows, renderer, size in (
                ("absolute-quality", absolute, absolute_fragment, 40),
                ("time-quality", times, time_fragment, 160),
                ("time-regions", times, region_fragment, 640),
            ):
                name = kind + "-" + mode.replace("_", "-")
                path = language + "/" + name + ".tex"
                files[path] = (prefix + renderer(name, rows, language)).encode("utf-8")
                counts[path] = size
    return files, counts, exact


def generate(cards_path, expected_sha256, output_directory, *, software_fixture=False):
    cards = source.load_cards(cards_path, expected_sha256)
    files, counts, exact = fragments(cards, software_fixture=software_fixture)
    identity = dict(schema_version=VERSION, source_cards_sha256=expected_sha256,
                    renderer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    projection_code_sha256=hashlib.sha256(Path(source.__file__).read_bytes()).hexdigest(),
                    tex_helper_sha256=hashlib.sha256(Path(tex.__file__).read_bytes()).hexdigest(),
                    software_fixture_only=software_fixture)
    root = Path(output_directory) / source.digest(identity)
    manifest = dict(**identity, scope=cards["scope"],
                    source_export_sha256=cards["source_export_sha256"],
                    source_catalog_sha256=cards["source_catalog_sha256"],
                    fixed_forecast=cards["fixed_forecast"],
                    exact_projected_rows=exact,
                    files={name: dict(sha256=hashlib.sha256(raw).hexdigest(), rows=counts[name])
                           for name, raw in files.items()},
                    review_state="metric-fragments-not-integrated",
                    manuscript_written=False, scientific_claim_authorized=False,
                    human_accepted=False, new_forecasts=0, new_fits=0,
                    new_scores=0, new_resampling=0)
    files["manifest.json"] = source.canonical(
        dict(payload=manifest, sha256=source.digest(manifest))) + b"\n"
    # Simple missing-only publication: no ownership lock or waiting.
    for name, raw in files.items():
        target = root / name
        if target.is_symlink() or target.exists() and (
                not target.is_file() or target.read_bytes() != raw):
            raise ValueError("existing metric fragment differs; no overwrite")
    for name, raw in files.items():
        target = root / name
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.parent / ("." + target.name + "." + uuid.uuid4().hex + ".tmp")
        with temporary.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    return dict(output_directory=str(root), manifest_sha256=source.digest(manifest),
                fragment_rows=counts, manuscript_written=False, human_accepted=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cards", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--software-fixture", action="store_true")
    args = parser.parse_args(argv)
    print(json.dumps(generate(args.cards, args.sha256, args.output_directory,
                              software_fixture=args.software_fixture)))


if __name__ == "__main__":
    main()
