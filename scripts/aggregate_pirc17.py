"""Render pinned PIRC17 PUBLIC review cards into reproducible CSV tables.

This is a consumer interface, not a manuscript, statistical engine, scientific
qualification or acceptance. It never loads positions, private snapshots,
models or legacy NEX326 numbers. The caller must obtain qualified cards through
the separate PIRC17 workflow; a self-consistent hash is not source authority.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import uuid

from scripts.aggregate_nex326 import EXPECTED_EXECUTIONS

CARD_VERSION = 'pirc17-public-review-evidence-cards-v1'
VERSION = 'pirc17-public-review-tables-v2'
MAX_BYTES = 128*1024*1024
MODES = ('causal_prefix','known_velocity','point_only')
GROUPS = ('road','river','worldcover','surface')
FAMILIES = {'weighted-es-primary':5,'weighted-es-lio':4,'method-model-structure':4,
    'method-observation-interval':4,'method-objective-and-score':5,
    'method-transfer-adaptation':4,'method-numerical-propagation':4}
METRICS = ('time_weighted_energy_score_m','ade_grid_mean_m','time_weighted_displacement_error_m','fde_m','path_energy_score_m')
DIAGNOSTIC_SLOTS = {'arm-18/full','arm-19/em','arm-19/euler','arm-10/d2_mc','arm-10/d2_closed'}
SCORING_SECONDS = (60,300,900,1800)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def check_sha(value):
    if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('explicit lowercase SHA256 required')
    return value


def load_cards(path,expected_sha256):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size>MAX_BYTES:
        raise ValueError('bounded regular public cards JSON required')
    def pairs(items):
        value={}
        for key,item in items:
            if key in value: raise ValueError('duplicate public JSON key')
            value[key]=item
        return value
    def constant(value): raise ValueError('nonfinite JSON constant forbidden')
    raw = path.read_bytes()
    if len(raw)>MAX_BYTES: raise ValueError('public cards grew beyond bound')
    record=json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)
    if (set(record)!={'payload','sha256'} or record['sha256']!=check_sha(expected_sha256)
            or digest(record['payload'])!=record['sha256']):
        raise ValueError('pinned public cards content differs')
    return record['payload']


def _index(rows,key,count):
    result={r[key]:r for r in rows}
    if len(rows)!=count or len(result)!=count: raise ValueError('complete unique card inventory required')
    return result


def evidence_views(cards,terrain,required_slots,cost_keys):
    """Transport the remaining public evidence; never remeasure or infer it.

    These checks protect table axes, not admission to prediction. Missing
    mechanism/timing evidence stays missing; failed replay is not success.
    """
    owners={}
    for group in GROUPS:
        entries=terrain['terrain:'+group]['ownership']
        if set(entries)!={'base','all-terrain','loo-'+group,'lio-'+group}:
            raise ValueError('exact per-group trained ownership references required')
        for name,row in entries.items():
            if name in owners and canonical(owners[name])!=canonical(row):
                raise ValueError('repeated terrain owner evidence differs')
            owners[name]=row
    configurations=[]
    for name,row in sorted(owners.items()):
        definition=row['definition']
        numeric=definition['numeric_input_dimension']
        if (type(numeric) is not int or numeric<=0 or definition['validity_input_dimension']!=numeric
                or definition['conditioner_input_dimension']!=2*numeric
                or definition['baseline_history_retained'] is not True
                or definition['retrain_independently'] is not True):
            raise ValueError('original numeric/validity dimensions and history/refit role required')
        configurations.append(dict(configuration=name,**row))
    if (len(owners)!=10 or owners['base']['definition']['conditioner_input_dimension']!=4
            or owners['all-terrain']['definition']['conditioner_input_dimension']!=56
            or len({r['definition']['fit_identity'] for r in owners.values()})!=10):
        raise ValueError('all ten distinct trained owners with fixed baseline/full dimensions required')
    if set(cards['mechanism_evidence'])!=set(MODES) or set(cards['numerical_score_and_variance_witnesses'])!=set(MODES):
        raise ValueError('all three public mechanism and witness modes required')
    mechanisms,diagnostics,variances=[],[],[]
    for mode in MODES:
        gates=cards['mechanism_evidence'][mode]
        if set(gates)!=required_slots:
            raise ValueError('all28 required mechanism slots per mode required')
        for slot,g in sorted(gates.items()):
            if (g['slot_id']!=slot or g['status'] not in {'computed','unavailable'}
                    or not 0<=g['available_count']<=g['expected_count']
                    or g['status']=='unavailable' and (g['value'] is not None or g['passed'] is not None)
                    or g['status']=='computed' and (g['value'] is None or type(g['passed']) is not bool)):
                raise ValueError('mechanism absence cannot become a statistic or a pass')
            mechanisms.append(dict(origin_mode=mode,**g))
        details=cards['numerical_score_and_variance_witnesses'][mode]
        if set(details['per_origin_diagnostics'])!=DIAGNOSTIC_SLOTS:
            raise ValueError('all five numerical/score witness inventories required')
        for slot,rows in sorted(details['per_origin_diagnostics'].items()):
            axes=[(r['origin_id'],r['independent_block_id'],r['seed']) for r in rows]
            if (len(rows)!=gates[slot]['expected_count'] or len(set(axes))!=len(axes)
                    or sum(r['measurements'] is not None for r in rows)!=gates[slot]['available_count']):
                raise ValueError('full admitted numerical/score witness denominator required')
            diagnostics.append(dict(origin_mode=mode,slot_id=slot,expected_count=len(rows),
                available_count=gates[slot]['available_count'],
                public_witnesses=sorted(rows,key=lambda r:(r['independent_block_id'],r['origin_id'],r['seed']))))
        variances.append(dict(origin_mode=mode,status='unavailable' if details['variance'] is None else 'recorded',
            evidence=details['variance'],scope='Descriptive fixed-seed variance evidence, not an extra hypothesis family.'))
    runtime=cards['isolated_runtime_and_replay']
    if runtime['registered_counts']!=dict(replays=38,cold=75,warmup=15,warm=75):
        raise ValueError('original finite replay/runtime counts required')
    replays=runtime['replay_rows']
    keys=[r['matrix']+':'+r['subject'] for r in replays]
    if len(keys)!=38 or len(set(keys))!=38 or set(keys)!=cost_keys:
        raise ValueError('all38 scientific subjects must retain replay evidence')
    for r in replays:
        if (r['successful_prediction_reproduced'] is not (r['status']=='reproduced')
                or r['status']=='reproduced' and (r['original_status']!='success'
                    or r['replay_status']!='success' or r['output_identity_equal'] is not True)
                or r['status']=='reproduced_failure' and (r['original_status']!='failed'
                    or r['replay_status']!='failed' or r['output_identity_equal'] is not True)):
            raise ValueError('failure replay is not a successful prediction')
    if dict(Counter(r['status'] for r in replays))!=runtime['replay_counts_by_status']:
        raise ValueError('replay status denominator differs')
    subjects=runtime['runtime_subjects']
    keys=[r['matrix']+':'+r['subject'] for r in subjects]
    if (len(keys)!=15 or len(set(keys))!=15 or not set(keys)<=cost_keys
            or len([r for r in subjects if r['matrix']=='terrain'])!=10):
        raise ValueError('all15 registered isolated runtime subjects required')
    trials,conditions=[],[]
    expected={(kind,i) for kind,n in (('runtime_cold',5),('runtime_warmup',1),('runtime_warm',5)) for i in range(n)}
    for subject in sorted(subjects,key=lambda r:(r['matrix'],r['subject'])):
        rows=subject['rows']
        if (len(rows)!=11 or {(r['kind'],r['repetition']) for r in rows}!=expected
                or set(subject['conditions'])!={'runtime_cold','runtime_warm'}
                or subject['warmup_excluded_from_latency_quantiles'] is not True):
            raise ValueError('five cold/one warmup/five warm axes required; warmup is not latency')
        for r in sorted(rows,key=lambda r:(r['kind'],r['repetition'])):
            measured=r['measurement']
            trial=None if measured is None else measured['trial']
            trials.append(dict(matrix=subject['matrix'],subject=subject['subject'],**r,
                actual_horizon_seconds=None if measured is None else measured['actual_horizon_seconds'],
                hardware_sha256=None if measured is None else measured['hardware_sha256'],
                end_to_end_ms=None if trial is None else trial['end_to_end_ms'],
                inclusive_stage_ms=None if trial is None else trial['inclusive_stage_ms'],
                sampled_peak_rss_bytes=None if trial is None else trial['sampled_peak_rss_bytes'],
                process_lifetime_peak_rss_bytes=None if trial is None else trial['process_lifetime_peak_rss_bytes'],
                included_in_latency_quantiles=(r['kind']!='runtime_warmup' and r['status']=='success'
                    and subject['conditions'][r['kind']]['status']=='computed'),memory_scope=subject['memory_scope']))
        for kind,condition in sorted(subject['conditions'].items()):
            selected=[r for r in rows if r['kind']==kind]
            complete=all(r['measurement'] is not None and r['status'] in {'success','failed'}
                and (kind!='runtime_warm' or r['warm_condition_verified'] is True) for r in selected)
            if (condition['required_trials']!=5
                    or condition['counts_by_status']!=dict(Counter(r['status'] for r in selected))
                    or condition['status']!=('computed' if complete else 'unavailable')
                    or condition['status']=='unavailable' and condition['summary'] is not None
                    or condition['status']=='computed' and condition['summary'] is None):
                raise ValueError('runtime summaries must retain failures and missing measurements')
            conditions.append(dict(matrix=subject['matrix'],subject=subject['subject'],condition=kind,**condition,
                warmup_excluded_from_latency_quantiles=True,memory_scope=subject['memory_scope']))
    return dict(terrain_configurations=configurations,mechanisms=mechanisms,diagnostic_witnesses=diagnostics,
        variance_witnesses=variances,replays=sorted(replays,key=lambda r:(r['matrix'],r['subject'])),
        runtime_trials=trials,runtime_conditions=conditions)


def project(cards):
    if (cards['schema_version']!=CARD_VERSION or cards['review_state']!='candidate-not-human-accepted'
            or any(cards.get(k) is not False for k in ('test02_qualification_asserted','scientific_claim_authorized',
                                                      'numerically_qualified','human_accepted'))
            or cards.get('new_forecasts')!=0 or cards.get('new_fits')!=0):
        raise ValueError('exact public review-candidate interface required; renderer grants no acceptance')
    methods=_index(cards['method_slot_cards'],'slot_id',36)
    expected={f'arm-{arm:02d}/{slot}' for arm,slots in EXPECTED_EXECUTIONS.items() for slot in slots}
    if set(methods)!=expected or sum(r['definition']['disposition']=='EXCLUDED' for r in methods.values())!=8:
        raise ValueError('all36 method slots including8 exclusions required')
    for slot,row in methods.items():
        arm=int(slot.split('/')[0][4:])
        if (row['definition']['arm_id']!=arm
                or (row['definition']['disposition']=='EXCLUDED')!=(arm in {13,17,22})
                or row['scientific_rejection_implied_by_exclusion'] is not False):
            raise ValueError('exact user-exempted arms retained without scientific rejection')
    arms=_index(cards['method_arm_cards'],'card_id',22)
    if set(arms)!={f'arm:{i:02d}' for i in range(1,23)}:
        raise ValueError('all22 method arms required')
    terrain=_index(cards['terrain_cards'],'card_id',4)
    if set(terrain)!={'terrain:'+g for g in GROUPS} or cards['history']['terrain_verdict'] is not None:
        raise ValueError('four terrain groups and history baseline-only required')
    factors=_index(cards['input_cards'],'card_id',13)
    variants=_index([dict(r,variant_id=r['variant']['variant_id']) for r in cards['variant_inventory']],'variant_id',35)
    if set(cards['family_evidence'])!=set(MODES): raise ValueError('all three origin modes required')
    comparisons=[]
    for mode in MODES:
        families=cards['family_evidence'][mode]
        if set(families)!=set(FAMILIES): raise ValueError('all seven frozen comparison families required')
        for family in sorted(families):
            report=families[family]
            if (len(report['results'])!=FAMILIES[family] or report['origin_mode']!=mode or report['family_id']!=family
                    or report['partition']!='final_eval' or mode!='causal_prefix' and report['hypothesis_tests_performed']):
                raise ValueError('registered family/mode/partition/descriptive role changed')
            for comparison,result in sorted(report['results'].items()):
                numeric=(report.get('inference') or {}).get('results',{}).get(comparison,{})
                descriptive=(report.get('descriptive') or {}).get('results',{}).get(comparison,{})
                interval=numeric.get('simultaneous_interval_m') or [None,None]
                marginal=numeric.get('marginal_interval_m') or [None,None]
                plan=result.get('planning') or {}
                comparisons.append(dict(origin_mode=mode,family_id=family,comparison_id=comparison,
                    partition='final_eval',candidate=numeric.get('candidate',descriptive.get('candidate')),
                    control=numeric.get('control',descriptive.get('control')),verdict=result['verdict'],reason=result['reason'],
                    independent_blocks=report['independent_block_count'],expected_rows=report['expected_rows'],
                    missing_rows=len(report['missing_rows']),failed_rows=len(report['failed_rows']),
                    hypothesis_tests_performed=report['hypothesis_tests_performed'],
                    delta_candidate_minus_control_m=numeric.get('delta_estimate_m',descriptive.get('delta_estimate_m')),
                    improvement_m=numeric.get('improvement_m',descriptive.get('improvement_m')),
                    simultaneous_lower_m=interval[0],simultaneous_upper_m=interval[1],
                    marginal_lower_m=marginal[0],marginal_upper_m=marginal[1],
                    holm_adjusted_p_zero=numeric.get('holm_adjusted_p_zero'),
                    paired_block_sd_m=descriptive.get('paired_block_sd_m'),
                    standardized_paired_delta=descriptive.get('standardized_paired_delta'),
                    seed_delta_m=numeric.get('seed_delta_m',descriptive.get('seed_delta_m')),
                    tail_check_passed=numeric.get('tail_check_passed'),planning_qualified=plan.get('qualified'),
                    planning_reason=plan.get('reason'),precision_invariant_verdict=result['precision_invariant_verdict']))
    metrics=_index([dict(r,table_id=f"{r['origin_mode']}:{r['matrix']}:{r['configuration']}") for r in cards['metric_tables']],'table_id',120)
    accuracy=[]
    for key,r in sorted(metrics.items()):
        means=r['means']
        if (r['status']=='computed' and (means is None or r['missing_score_rows'] or
                r['counts_by_status'].get('success')!=r['expected_forecasts'])
                or r['status']=='unavailable' and means is not None):
            raise ValueError('no successful-subset metric estimates allowed')
        accuracy.append(dict(table_id=key,origin_mode=r['origin_mode'],matrix=r['matrix'],configuration=r['configuration'],
            status=r['status'],expected_forecasts=r['expected_forecasts'],available_score_rows=r['available_score_rows'],
            missing_score_rows=r['missing_score_rows'],counts_by_status=r['counts_by_status'],
            **{k:None if means is None else means[k] for k in METRICS},
            by_time=None if means is None else means['by_time']))
    costs=cards['kernel_costs']
    terrain_names={'base','all-terrain',*[p+g for p in ('loo-','lio-') for g in GROUPS]}
    cost_keys={'terrain:'+name for name in terrain_names}|{'NEX326-methods:'+name for name,r in methods.items()
        if r['definition']['disposition']=='REQUIRED'}
    if set(costs)!=cost_keys: raise ValueError('all38 registered scientific cost subjects required')
    for row in costs.values():
        if (row['expected_forecasts']!=290 or row['recorded_timing_count']+row['missing_timing_count']!=290
                or not 0<=row['recorded_timing_count']<=290 or sum(row['counts_by_status'].values())!=290):
            raise ValueError('complete cost denominator and explicit missing timings required')
        seconds=row['recorded_kernel_total_seconds']
        mean=row['recorded_kernel_mean_seconds']
        if (type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<0
                or row['recorded_timing_count']==0 and (seconds!=0 or mean is not None)
                or row['recorded_timing_count']>0 and (type(mean) not in (int,float)
                    or not math.isfinite(mean) or mean<0 or mean!=seconds/row['recorded_timing_count'])):
            raise ValueError('recorded kernel cost arithmetic differs; never invent missing latency')
    tables=dict(comparisons=comparisons,accuracy=accuracy,
        terrain=[dict(card_id=k,verdict=r['verdict']['verdict'],reason=r['verdict']['reason'],
            primary=r['primary'],supporting=r['supporting'],raw_factor_ids=r['raw_factor_ids'],
            attribution_scope=r['attribution_scope'],kernel_cost_references=r['kernel_cost_references']) for k,r in sorted(terrain.items())],
        methods=[dict(card_id=r['card_id'],slot_id=k,arm_id=r['definition']['arm_id'],role=r['definition']['role'],
            disposition=r['definition']['disposition'],exclusion_reason=r['definition']['exclusion_reason'],
            comparison_reference=r['comparison_reference'],kernel_cost_reference=r['kernel_cost_reference'],
            predictive_result=r['predictive_result'],scientific_rejection_implied_by_exclusion=False) for k,r in sorted(methods.items())],
        arms=[dict(card_id=k,definition=r['definition'],slot_card_ids=r['slot_card_ids'],disposition=r['disposition']) for k,r in sorted(arms.items())],
        factors=[dict(card_id=k,factor_id=r['factor']['factor_id'],disposition=r['disposition'],verdict=r['verdict'],
            reason=r['reason'],verdict_references=r['verdict_references'],selected_variant_ids=r['factor']['selected_variant_ids'],
            coverage=r['factor']['coverage'],coverage_scope=r['factor']['coverage_scope']) for k,r in sorted(factors.items())],
        variants=[dict(variant_id=k,definition=r['variant'],input_card_id=r['input_card_id'],disposition=r['disposition'],
            verdict=r['verdict'],independent_variant_effect_tested=r['independent_variant_effect_tested'],limitation=r['limitation']) for k,r in sorted(variants.items())],
        kernel_costs=[dict(cost_id=k,**r) for k,r in sorted(costs.items())])
    tables.update(evidence_views(cards,terrain,{k for k,r in methods.items()
        if r['definition']['disposition']=='REQUIRED'},cost_keys))
    times=[]
    for key,r in sorted(metrics.items()):
        source=None if r['means'] is None else r['means']['by_time']
        if source is not None and (len(source)!=4 or tuple(t['nominal_seconds'] for t in source)!=SCORING_SECONDS):
            raise ValueError('all four registered descriptive scoring times required')
        for i,seconds in enumerate(SCORING_SECONDS):
            t=None if source is None else source[i]
            times.append(dict(table_id=key,origin_mode=r['origin_mode'],matrix=r['matrix'],configuration=r['configuration'],
                status=r['status'],nominal_seconds=seconds,expected_forecasts=r['expected_forecasts'],
                missing_score_rows=r['missing_score_rows'],counts_by_status=r['counts_by_status'],
                **{name:None if t is None else t[name] for name in ('actual_elapsed_seconds_range',
                    'energy_score_m','position_entropy_nats','coverage')}))
    tables['accuracy_times']=times
    # Also rejects NaN/infinity embedded in any exported nested diagnostic.
    canonical(tables)
    return tables


def csv_bytes(rows):
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
    writer.writeheader()
    for row in rows:
        writer.writerow({k:'' if v is None else canonical(v).decode('utf-8') if isinstance(v,(dict,list)) else v
                         for k,v in row.items()})
    return stream.getvalue().encode('utf-8')


def generate(path,expected_sha256,output_directory):
    cards=load_cards(path,expected_sha256)
    tables=project(cards)
    code_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    identity=dict(schema_version=VERSION,source_cards_sha256=expected_sha256,renderer_sha256=code_sha)
    root=Path(output_directory)/digest(identity)
    root.mkdir(parents=True,exist_ok=True)
    files={name+'.csv':csv_bytes(rows) for name,rows in tables.items()}
    manifest=dict(**identity,scope=cards['scope'],snapshot_binding=cards['snapshot_binding'],
        source_export_sha256=cards['source_export_sha256'],source_catalog_sha256=cards['source_catalog_sha256'],
        fixed_forecast=cards['fixed_forecast'],inference_config=cards['inference_config'],seed_role=cards['seed_role'],
        multiplicity=cards['multiplicity'],uncertainty=cards['uncertainty'],history=cards['history'],
        overall_terrain=cards['overall_terrain'],method_fidelity=cards['method_fidelity'],
        limitations=cards['limitations'],paper_wording_rule=cards['paper_wording_rule'],
        isolated_runtime_metadata={k:v for k,v in cards['isolated_runtime_and_replay'].items()
                                   if k not in {'runtime_subjects','replay_rows'}},
        runner_cost_snapshot=cards['runner_cost_snapshot'],
        files={name:dict(sha256=hashlib.sha256(raw).hexdigest(),rows=len(tables[name[:-4]])) for name,raw in files.items()},
        review_state='rendered-review-candidate',scientific_claim_authorized=False,human_accepted=False,
        manuscript_written=False,authors_selected=False,template_selected=False,new_forecasts=0,new_fits=0)
    files['manifest.json']=canonical(dict(payload=manifest,sha256=digest(manifest)))+b'\n'
    # Ordinary missing-only deterministic rendering, no lock/wait/recovery gate.
    # Publish each new file atomically; prior different bytes are never replaced.
    for name,raw in files.items():
        target=root/name
        if target.exists():
            if target.is_symlink() or target.read_bytes()!=raw:
                raise ValueError('existing public table bundle differs; never overwrite reviewed output')
            continue
        temporary=root/('.'+name+'.'+uuid.uuid4().hex+'.tmp')
        with temporary.open('xb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary,target)
    return dict(bundle_id=digest(identity),manifest_sha256=digest(manifest),output_directory=str(root),
                table_row_counts={name:len(rows) for name,rows in tables.items()})


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cards',type=Path,required=True)
    parser.add_argument('--sha256',required=True,help='Independently pinned public cards content SHA256.')
    parser.add_argument('--output-directory',type=Path,required=True)
    args=parser.parse_args(argv)
    print(json.dumps(generate(args.cards,args.sha256,args.output_directory)),flush=True)


if __name__=='__main__':
    main()
