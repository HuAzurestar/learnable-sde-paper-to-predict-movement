"""Typeset existing pinned public review cards; never infer or approve results.

Generated English/Chinese TeX fragments are inputs for subsequent manuscript
editing, not a completed paper. No current manuscript or PDF is overwritten.
All values, intervals, qualification states and failures come from the original
card producer. This command does not score, bootstrap, fit or predict.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import uuid

from scripts import aggregate_pirc17 as source

VERSION = 'pirc17-paper-table-fragments-v1'
LANGUAGES = ('en', 'zh')
FAMILY_NAMES = {
    'method-model-structure': ('Model structure', '模型结构'),
    'method-observation-interval': ('Observation interval', '观测间隔'),
    'method-objective-and-score': ('Fitting and score route', '拟合与评分路线'),
    'method-transfer-adaptation': ('Training and adaptation', '训练与适应'),
    'method-numerical-propagation': ('Numerical propagation', '数值传播'),
    'weighted-es-primary': ('Terrain primary/LOO', '地形主要及移除因素'),
    'weighted-es-lio': ('Terrain supporting LIO', '地形单独加入因素'),
}
MODE_NAMES = {
    'causal_prefix': ('Visible-prefix primary task', '可见前缀主要任务'),
    'known_velocity': ('Known-velocity secondary task', '已知速度次要任务'),
    'point_only': ('Point-only secondary task', '仅位置次要任务'),
}


def translated(pair, language):
    return pair[LANGUAGES.index(language)]


def tex_text(value):
    """Escape text, including machine identifiers, without executable TeX."""
    if value is None:
        return '--'
    escapes = {'\\': r'\textbackslash{}', '{': r'\{', '}': r'\}',
               '%': r'\%', '&': r'\&', '#': r'\#', '$': r'\$',
               '_': r'\_\allowbreak{}', '^': r'\textasciicircum{}',
               '~': r'\textasciitilde{}', '/': r'/\allowbreak{}'}
    return ''.join(escapes.get(c, c) for c in ' '.join(str(value).split()))


def number(value):
    if value is None:
        return '--'
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('finite recorded number or explicit absence required')
    # Display only; exact values stay in cards, original CSVs and this manifest.
    return format(value, '.4g')


def flag(value, language):
    if value is None:
        return translated(('not recorded', '未记录'), language)
    if type(value) is not bool:
        raise ValueError('recorded Boolean or explicit absence required')
    return translated(('pass', '通过') if value else ('fail', '未通过'), language)


def longtable(name, caption, headers, widths, rows, continuation='continued'):
    spec = '@{}' + ''.join('p{'+str(w)+r'\linewidth}' for w in widths) + '@{}'
    head = ' & '.join(headers) + r'\\'
    label = 'tab:public-card-' + name.replace('_', '-')
    lines = [r'\begingroup', r'\small', r'\setlength{\tabcolsep}{3pt}',
             r'\setlength{\LTcapwidth}{\linewidth}',
             r'\begin{longtable}{'+spec+'}',
             r'\caption{'+caption+r'}\label{'+label+r'}\\',
             r'\toprule', head, r'\midrule', r'\endfirsthead',
             r'\multicolumn{'+str(len(headers))+r'}{@{}l}{\tablename~\thetable\ ('+continuation+r')}\\',
             r'\toprule', head, r'\midrule', r'\endhead',
             r'\midrule', r'\endfoot', r'\bottomrule', r'\endlastfoot']
    for row in rows:
        if len(row) != len(headers):
            raise ValueError('table column count differs')
        lines.append(' & '.join(row)+r'\\')
    lines.extend([r'\end{longtable}', r'\endgroup', ''])
    return '\n'.join(lines)


def paired_fragment(name, rows, language):
    caption = translated((
        'Recorded paired comparisons: '+MODE_NAMES[rows[0]['origin_mode']][0]+
        '. Differences are candidate minus control energy score (m); negative '
        'favours the candidate, not automatically a beneficial terrain factor. '
        'Intervals are the original simultaneous within-family intervals. '
        'Secondary tasks are descriptive only. Missing values are --, not zero. '
        'Block counts denote registered record-hash groups, not verified independent participants. '
        'Tail, planning and resolution-invariance fields are separate recorded '
        'states; this table grants no scientific or human acceptance.',
        '保存配对比较：'+MODE_NAMES[rows[0]['origin_mode']][1]+
        '。差值为候选减对照的能量分数（米）；负值有利于候选，不自动表示地形因素有益。'
        '区间是原比较族内同时区间，次要任务仅作描述。缺失值为--，不是零。'
        '块数表示登记记录哈希组，不认证独立参与者。'
        '尾部、规划与分辨率不变裁定分别保留原状态；本表不授予科学或人工验收。'), language)
    headers = translated((['Family / comparison', 'Candidate / control',
        r'$\Delta$ [simultaneous interval], m', 'Recorded qualification / reason',
        'Blocks; expected / missing / failed rows'], ['比较族／比较', '候选／对照',
        r'$\Delta$及同时区间（米）', '保存资格状态／原因', '块；计划／缺失／失败行']), language)
    cells = []
    for row in rows:
        low, high = row['simultaneous_lower_m'], row['simultaneous_upper_m']
        number(low)
        number(high)
        if ((low is None) != (high is None) or
                low is not None and low > high or
                row['delta_candidate_minus_control_m'] is None and low is not None):
            raise ValueError('both ordered recorded endpoints and estimate required')
        family = translated(FAMILY_NAMES[row['family_id']], language)
        qualifications = tex_text(row['verdict']) + r'\newline ' + tex_text(row['reason'])
        qualifications += r'\newline ' + translated(('Tail: ', '尾部：'), language) + flag(row['tail_check_passed'], language)
        qualifications += '; ' + translated(('plan: ', '规划：'), language) + flag(row['planning_qualified'], language)
        qualifications += r'\newline ' + translated(('Resolution: ', '分辨率：'), language) + tex_text(row['precision_invariant_verdict'])
        cells.append([tex_text(family)+r'\newline '+tex_text(row['comparison_id']),
            tex_text(row['candidate'])+r'\newline / '+tex_text(row['control']),
            number(row['delta_candidate_minus_control_m'])+r'\newline ['+number(low)+', '+number(high)+']',
            qualifications,
            tex_text(row['independent_blocks'])+r'\newline '+tex_text(row['expected_rows'])+
            ' / '+tex_text(row['missing_rows'])+' / '+tex_text(row['failed_rows'])])
    return longtable(name, caption, headers, [.19, .18, .16, .29, .10], cells,
                     translated(('continued','续表'),language))


def cost_fragment(rows, language):
    caption = translated((
        'Recorded scientific prediction-kernel costs. Every subject retains '
        '290 planned forecasts across all original modes and seeds. Total and '
        'mean use only recorded timings; missing timings and all statuses remain '
        'visible. No recorded timings means -- for the displayed total, not '
        'zero-cost prediction. These are not isolated latency, CPU time, or project wall time.',
        '保存科学预测核耗时。每个配置保留全部原模式与种子的290项计划预测。'
        '总耗时与均值仅针对有计时记录的项；缺失计时和全部状态均保留。'
        '没有计时记录时合计显示--，不表示预测零成本。'
        '不是隔离延迟、CPU时间或项目墙钟工期。'), language)
    headers = translated((['Matrix / subject', 'Recorded / missing timings',
        'Total (s)', 'Mean (s)', 'All work statuses'], ['矩阵／配置', '有记录／缺失计时',
        '合计（秒）', '均值（秒）', '全部工作状态']), language)
    cells = [[tex_text(r['matrix'])+r'\newline '+tex_text(r['subject']),
        tex_text(r['recorded_timing_count'])+' / '+tex_text(r['missing_timing_count']),
        number(r['recorded_kernel_total_seconds']) if r['recorded_timing_count'] else '--',
        number(r['recorded_kernel_mean_seconds']),
        status_counts(r['counts_by_status'])] for r in rows]
    return longtable('kernel-costs', caption, headers, [.28, .17, .12, .12, .23], cells,
                     translated(('continued','续表'),language))


def status_counts(counts):
    return r'\newline '.join(tex_text(k)+': '+tex_text(v) for k,v in sorted(counts.items()))


def runtime_fragment(rows, language):
    caption = translated((
        'Original recorded provider-cold/resident-warm elapsed times: five trials '
        'per condition. Warmup is excluded. Cold creates a new provider, not a '
        'verified reset of OS or interpreter caches. Read these summaries with '
        'the manuscript host-interruption and clock limitations; neither '
        'affected summaries nor unflagged trials certify uninterrupted isolated '
        'latency or speedup. Original values and trial denominators are retained '
        'without sleep subtraction, trial exclusion or replacement measurement. '
        'p50/p95 are original successful-trial summaries, not population tail '
        'guarantees; failures and unavailable summaries remain visible. '
        'No quantiles are recomputed by this renderer.',
        '原保存特征提供器冷启动／驻留热启动墙钟耗时：每个条件五次，预热不计入。'
        '冷启动仅创建新提供器，不认证操作系统或解释器缓存已重置。'
        '本汇总须结合正文的主机中断与时钟限制阅读；受影响汇总及未标记试次均不认证'
        '无中断隔离延迟或加速。保留原值与试次分母，不扣除休眠时间、排除试次或补做测量。'
        'p50/p95保留原成功试次汇总，不是总体尾延迟保证；失败与不可用汇总均显示。'
        '本造表程序不重算分位数。'), language)
    headers = translated((['Matrix / subject', 'Condition / status', 'p50 (ms)',
        'p95 (ms)', 'All trial statuses'], ['矩阵／配置', '条件／状态', 'p50（毫秒）',
        'p95（毫秒）', '全部试次状态']), language)
    cells = []
    for row in rows:
        summary = row['summary'] or {}
        cells.append([tex_text(row['matrix'])+r'\newline '+tex_text(row['subject']),
            tex_text(row['condition'])+r'\newline '+tex_text(row['status']),
            number(summary.get('total_latency_p50_ms')),
            number(summary.get('total_latency_p95_ms')),
            status_counts(row['counts_by_status'])])
    return longtable('isolated-runtime', caption, headers, [.28, .23, .10, .10, .21], cells,
                     translated(('continued','续表'),language))


def fragments(cards, *, software_fixture=False):
    projected = source.project(cards)  # Original complete public interface only.
    files, counts = {}, {}
    for language in LANGUAGES:
        prefix = ('SOFTWARE FIXTURE ONLY. Not experimental evidence.\n' if software_fixture else '')
        prefix += 'Public-card rendering only; manuscript integration and acceptance remain pending.\n'
        prefix = '\n'.join('% '+line for line in prefix.splitlines())+'\n'
        if software_fixture:
            prefix += r'\paragraph{'+translated(('SOFTWARE FIXTURE ONLY -- no experimental evidence.',
                '仅合成软件测试数据，不是实验结果。'),language)+'}\n'
        for mode in source.MODES:
            for matrix, family_prefix in [('methods', 'method-'), ('terrain', 'weighted-es-')]:
                rows = [r for r in projected['comparisons']
                        if r['origin_mode']==mode and r['family_id'].startswith(family_prefix)]
                name = matrix+'-'+mode.replace('_', '-')
                path = language+'/'+name+'.tex'
                files[path] = (prefix+paired_fragment(name, rows, language)).encode('utf-8')
                counts[path] = len(rows)
        for name, key, renderer in [('kernel-costs', 'kernel_costs', cost_fragment),
                                     ('isolated-runtime', 'runtime_conditions', runtime_fragment)]:
            path = language+'/'+name+'.tex'
            files[path] = (prefix+renderer(projected[key], language)).encode('utf-8')
            counts[path] = len(projected[key])
    return files, counts, {k:projected[k] for k in ('comparisons','kernel_costs','runtime_conditions')}


def generate(cards_path, expected_sha256, output_directory, *, software_fixture=False):
    cards = source.load_cards(cards_path, expected_sha256)
    files, counts, exact_rows = fragments(cards, software_fixture=software_fixture)
    identity = dict(schema_version=VERSION, source_cards_sha256=expected_sha256,
        renderer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        software_fixture_only=software_fixture)
    root = Path(output_directory)/source.digest(identity)
    manifest = dict(**identity, scope=cards['scope'], source_export_sha256=cards['source_export_sha256'],
        source_catalog_sha256=cards['source_catalog_sha256'], exact_projected_rows=exact_rows,
        files={name:dict(sha256=hashlib.sha256(raw).hexdigest(),rows=counts[name]) for name,raw in files.items()},
        review_state='table-fragments-not-integrated', manuscript_written=False,
        scientific_claim_authorized=False, human_accepted=False,
        new_forecasts=0,new_fits=0,new_scores=0,new_resampling=0)
    files['manifest.json'] = source.canonical(dict(payload=manifest,sha256=source.digest(manifest)))+b'\n'
    # Preflight all existing paths before adding any file; never replace output.
    for name, raw in files.items():
        target = root/name
        if target.is_symlink() or target.exists() and (not target.is_file() or target.read_bytes()!=raw):
            raise ValueError('existing table fragment differs; no overwrite')
    for name, raw in files.items():
        target = root/name
        if target.exists():
            continue
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary = target.parent/('.'+target.name+'.'+uuid.uuid4().hex+'.tmp')
        with temporary.open('xb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary,target)
    return dict(output_directory=str(root),manifest_sha256=source.digest(manifest),
                fragment_rows=counts,manuscript_written=False,human_accepted=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cards',type=Path,required=True)
    parser.add_argument('--sha256',required=True)
    parser.add_argument('--output-directory',type=Path,required=True)
    parser.add_argument('--software-fixture',action='store_true')
    args = parser.parse_args(argv)
    print(json.dumps(generate(args.cards,args.sha256,args.output_directory,
                              software_fixture=args.software_fixture)))


if __name__=='__main__':
    main()
