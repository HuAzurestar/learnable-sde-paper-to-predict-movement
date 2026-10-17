"""Standalone table transport fixtures: no empirical values or qualification."""
from copy import deepcopy
import csv
import json

import pytest

from scripts import aggregate_pirc17 as module


@pytest.fixture
def cards():
    methods=[]
    for arm,slots in sorted(module.EXPECTED_EXECUTIONS.items()):
        for slot in sorted(slots):
            excluded=arm in {13,17,22}
            name=f'arm-{arm:02d}/{slot}'
            methods.append(dict(card_id='method:'+name,slot_id=name,
                definition=dict(arm_id=arm,role='policy-excluded' if excluded else 'SOFTWARE declared role',
                    disposition='EXCLUDED' if excluded else 'REQUIRED',exclusion_reason='SOFTWARE exemption' if excluded else None),
                comparison_reference=None,kernel_cost_reference=None,predictive_result=None,
                scientific_rejection_implied_by_exclusion=False))
    families={mode:{family:dict(family_id=family,origin_mode=mode,partition='final_eval',
        hypothesis_tests_performed=False,independent_block_count=0,expected_rows=0,missing_rows=[],failed_rows=[],
        inference=None,descriptive=None,results={str(i):dict(verdict='unavailable',reason='SOFTWARE absent full evidence',
        planning=None,precision_invariant_verdict='unavailable') for i in range(size)})
        for family,size in module.FAMILIES.items()} for mode in module.MODES}
    metric_names=[('NEX326-methods',r['slot_id']) for r in methods if r['definition']['disposition']=='REQUIRED']
    terrains=['base','all-terrain',*[p+g for p in ('loo-','lio-') for g in module.GROUPS]]
    metric_names += [('terrain',name) for name in terrains]+[('NEX326-diagnostic','SOFTWARE reference'),('inertial','all')]
    costs={m+':'+s:dict(matrix=m,subject=s,expected_forecasts=290,counts_by_status={'NOT_ADMITTED':290},
        recorded_timing_count=0,missing_timing_count=290,recorded_kernel_total_seconds=0,
        recorded_kernel_mean_seconds=None,scope='SOFTWARE timing absent',isolated_runtime_references=[])
        for m,s in metric_names if m in {'NEX326-methods','terrain'}}
    owners={name:dict(definition=dict(fit_identity='terrain-fit:'+name,
        numeric_input_dimension=2 if name=='base' else 28 if name=='all-terrain' else 10,
        validity_input_dimension=2 if name=='base' else 28 if name=='all-terrain' else 10,
        conditioner_input_dimension=4 if name=='base' else 56 if name=='all-terrain' else 20,
        baseline_history_retained=True,retrain_independently=True),status='unavailable',
        owner_closure_verified=True,independent_fit_verified=False,fit_receipt_sha256=None,parameter_identity=None)
        for name in terrains}
    required=[r['slot_id'] for r in methods if r['definition']['disposition']=='REQUIRED']
    gates={mode:{slot:dict(slot_id=slot,definition_sha256=module.digest('SOFTWARE '+slot),
        statistic='SOFTWARE no measured statistic',operator='le',threshold=1,units='SOFTWARE',
        status='unavailable',value=None,passed=None,expected_count=0 if slot in module.DIAGNOSTIC_SLOTS else 1,
        available_count=0,rows_sha256=module.digest('SOFTWARE absent rows'),source_scope='SOFTWARE fixture only')
        for slot in required} for mode in module.MODES}
    replay_rows=[dict(matrix=m,subject=s,original_work_id=module.digest('SOFTWARE original '+m+s),
        replay_work_id=module.digest('SOFTWARE replay '+m+s),original_sha256=None,replay_sha256=None,
        original_status='NOT_ADMITTED',replay_status='NOT_ADMITTED',original_prediction_identity=None,
        replay_prediction_identity=None,status='NOT_ADMITTED',output_identity_equal=None,
        successful_prediction_reproduced=False) for m,s in metric_names if m in {'NEX326-methods','terrain'}]
    runtime_subjects=[]
    for m,s in [('terrain',name) for name in terrains]+[('NEX326-methods',slot) for slot in required[:5]]:
        rows=[dict(work_id=module.digest('SOFTWARE trial '+m+s+kind+str(i)),kind=kind,repetition=i,
            status='NOT_ADMITTED',forecast_sha256=None,warm_condition_verified=None,measurement=None)
            for kind,n in [('runtime_cold',5),('runtime_warmup',1),('runtime_warm',5)] for i in range(n)]
        conditions={kind:dict(required_trials=5,status='unavailable',counts_by_status={'NOT_ADMITTED':5},
            summary=None,reason='SOFTWARE no admitted trial',observed_sampled_peak_rss_bytes=None,
            observed_process_lifetime_peak_rss_bytes=None,successful_inclusive_stage_p50_ms=None)
            for kind in ('runtime_cold','runtime_warm')}
        runtime_subjects.append(dict(matrix=m,subject=s,rows=rows,conditions=conditions,
            warmup_excluded_from_latency_quantiles=True,memory_scope='SOFTWARE sampled lower bound; lifetime is not per trial'))
    value=dict(schema_version=module.CARD_VERSION,review_state='candidate-not-human-accepted',
        test02_qualification_asserted=False,scientific_claim_authorized=False,numerically_qualified=False,
        human_accepted=False,new_forecasts=0,new_fits=0,method_slot_cards=methods,
        method_arm_cards=[dict(card_id=f'arm:{arm:02d}',definition={'arm_id':arm},
            slot_card_ids=[r['card_id'] for r in methods if r['definition']['arm_id']==arm],
            disposition='EXCLUDED' if arm in {13,17,22} else 'REQUIRED') for arm in range(1,23)],
        terrain_cards=[dict(card_id='terrain:'+g,verdict=dict(verdict='unavailable',reason='SOFTWARE missing pairs'),
            primary={'family_id':'weighted-es-primary','comparison':g},supporting={'family_id':'weighted-es-lio','comparison':g},
            raw_factor_ids=[],attribution_scope='SOFTWARE no effect',kernel_cost_references=[],
            ownership={name:deepcopy(owners[name]) for name in ('base','all-terrain','loo-'+g,'lio-'+g)}) for g in module.GROUPS],
        input_cards=[dict(card_id=f'input:SOFTWARE-{i}',factor=dict(factor_id=f'SOFTWARE-{i}',selected_variant_ids=[],
            coverage={},coverage_scope='SOFTWARE metadata only'),disposition='screened-out',verdict='inconclusive',
            reason='SOFTWARE not evaluated',verdict_references=[]) for i in range(13)],
        variant_inventory=[dict(variant={'variant_id':f'SOFTWARE-{i}'},input_card_id='input:SOFTWARE-0',
            disposition='not-selected',verdict='inconclusive',independent_variant_effect_tested=False,
            limitation='SOFTWARE not evaluated') for i in range(35)],
        family_evidence=families,metric_tables=[dict(origin_mode=mode,matrix=m,configuration=s,
            status='unavailable',expected_forecasts=0,available_score_rows=0,missing_score_rows=0,
            counts_by_status={},means=None) for mode in module.MODES for m,s in metric_names],
        kernel_costs=costs,history=dict(role='baseline-only',terrain_verdict=None),
        mechanism_evidence=gates,numerical_score_and_variance_witnesses={mode:dict(
            per_origin_diagnostics={slot:[] for slot in module.DIAGNOSTIC_SLOTS},variance=None) for mode in module.MODES},
        isolated_runtime_and_replay=dict(registered_counts=dict(replays=38,cold=75,warmup=15,warm=75),
            replay_rows=replay_rows,replay_counts_by_status={'NOT_ADMITTED':38},runtime_subjects=runtime_subjects,
            settings={},hardware={},timing_scope={'stages':'SOFTWARE inclusive, do not sum'},
            replay_scope='SOFTWARE first origin only',verification_scope='SOFTWARE no remeasurement',
            latency_scope='SOFTWARE five descriptive trials'),
        runner_cost_snapshot={'auxiliary_scoring_analysis_audit_costs_included':False},
        overall_terrain=dict(family_id='weighted-es-primary',comparison='all-vs-base'),
        scope={k:module.digest('SOFTWARE '+k) for k in ('protocol_sha256','execution_sha256','matrix_sha256',
            'population_sha256','audit_sha256','analysis_sha256')},snapshot_binding={'snapshot_id':'SOFTWARE no private input'},
        source_export_sha256=module.digest('SOFTWARE export'),source_catalog_sha256=module.digest('SOFTWARE catalog'),
        fixed_forecast={'nominal_horizon_seconds':1800,'particles':512,'max_step_seconds':5},
        inference_config={'bootstrap_iterations':2000},seed_role='SOFTWARE fixed forecast seeds, not training fits',
        multiplicity='SOFTWARE within-family only',uncertainty='SOFTWARE none computed',method_fidelity={'paper_equivalent':False},
        limitations=['SOFTWARE tables are not scientific results'],paper_wording_rule='SOFTWARE no empirical claim')
    return value


def write_cards(path,value):
    sha=module.digest(value)
    path.write_bytes(module.canonical(dict(payload=value,sha256=sha)))
    return sha


def test_full_separate_tables_keep_absence_and_do_not_compute_statistics(cards):
    tables=module.project(cards)
    assert {k:len(v) for k,v in tables.items()}==dict(comparisons=90,accuracy=120,terrain=4,methods=36,
        arms=22,factors=13,variants=35,kernel_costs=38,terrain_configurations=10,mechanisms=84,
        diagnostic_witnesses=15,variance_witnesses=3,replays=38,runtime_trials=165,runtime_conditions=30,accuracy_times=480)
    assert all(r['delta_candidate_minus_control_m'] is None for r in tables['comparisons'])
    assert all(r['time_weighted_energy_score_m'] is None for r in tables['accuracy'])
    assert sum(r['disposition']=='EXCLUDED' for r in tables['methods'])==8
    assert all(not r['scientific_rejection_implied_by_exclusion'] for r in tables['methods'])
    assert all(r['missing_timing_count']==290 for r in tables['kernel_costs'])
    assert all(r['end_to_end_ms'] is None and not r['included_in_latency_quantiles'] for r in tables['runtime_trials'])
    assert all(r['summary'] is None for r in tables['runtime_conditions'])
    assert all(r['energy_score_m'] is None for r in tables['accuracy_times'])
    assert all(r['passed'] is None for r in tables['mechanisms'])


@pytest.mark.parametrize('fault',['claim','duplicate_method','missing_arm','history_verdict','missing_factor',
    'missing_variant','family','secondary_test','success_subset','missing_cost','cost_mean','wrong_exemption'])
def test_rejects_incomplete_or_misleading_table_input(cards,fault):
    value=deepcopy(cards)
    if fault=='claim': value['scientific_claim_authorized']=True
    elif fault=='duplicate_method': value['method_slot_cards'][0]=deepcopy(value['method_slot_cards'][1])
    elif fault=='missing_arm': value['method_arm_cards'].pop()
    elif fault=='history_verdict': value['history']['terrain_verdict']='retain'
    elif fault=='missing_factor': value['input_cards'].pop()
    elif fault=='missing_variant': value['variant_inventory'].pop()
    elif fault=='family': value['family_evidence']['causal_prefix'].pop('weighted-es-lio')
    elif fault=='secondary_test': value['family_evidence']['point_only']['weighted-es-primary']['hypothesis_tests_performed']=True
    elif fault=='success_subset': value['metric_tables'][0]['means']={k:0 for k in module.METRICS}
    elif fault=='missing_cost': value['kernel_costs'].pop(next(iter(value['kernel_costs'])))
    elif fault=='cost_mean': next(iter(value['kernel_costs'].values()))['recorded_kernel_mean_seconds']=0
    else: value['method_slot_cards'][0]['scientific_rejection_implied_by_exclusion']=True
    with pytest.raises(ValueError): module.project(value)


def test_file_roundtrip_missing_only_reuse_and_immutable_provenance(cards,tmp_path):
    source=tmp_path/'public-review.json'
    sha=write_cards(source,cards)
    result=module.generate(source,sha,tmp_path/'tables')
    assert module.generate(source,sha,tmp_path/'tables')==result
    root=tmp_path/'tables'/result['bundle_id']
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))['payload']
    assert manifest['source_cards_sha256']==sha
    assert manifest['scientific_claim_authorized'] is False and manifest['manuscript_written'] is False
    assert manifest['authors_selected'] is False and manifest['template_selected'] is False
    assert str(tmp_path) not in json.dumps(manifest)
    rows=list(csv.DictReader((root/'comparisons.csv').read_text(encoding='utf-8').splitlines()))
    assert len(rows)==90 and all(r['delta_candidate_minus_control_m']=='' for r in rows)
    target=root/'terrain.csv'
    original=target.read_bytes(); target.unlink()  # Owned generated test output only.
    assert module.generate(source,sha,tmp_path/'tables')==result and target.read_bytes()==original
    target.write_bytes(b'SOFTWARE corrupted output')
    with pytest.raises(ValueError,match='never overwrite'):
        module.generate(source,sha,tmp_path/'tables')


def test_wrong_pin_is_rejected_before_output(cards,tmp_path):
    source=tmp_path/'public-review.json'; write_cards(source,cards)
    with pytest.raises(ValueError,match='pinned'):
        module.generate(source,module.digest('wrong source'),tmp_path/'absent')
    assert not (tmp_path/'absent').exists()


@pytest.mark.parametrize('fault',['owner_conflict','history_removed','dimension','shared_fit','missing_mechanism',
    'missing_mode','missing_diagnostic','diagnostic_denominator','missing_replay','replay_failure_success',
    'replay_counts','runtime_subject','runtime_trial','warmup_quantiles','runtime_counts','runtime_invented_summary'])
def test_rejects_partial_or_misleading_runtime_mechanism_transport(cards,fault):
    value=deepcopy(cards)
    owner=value['terrain_cards'][0]['ownership']['base']
    runtime=value['isolated_runtime_and_replay']
    subject=runtime['runtime_subjects'][0]
    if fault=='owner_conflict': owner['status']='computed'
    elif fault=='history_removed': value['terrain_cards'][0]['ownership']['loo-road']['definition']['baseline_history_retained']=False
    elif fault=='dimension': value['terrain_cards'][0]['ownership']['lio-road']['definition']['conditioner_input_dimension']=0
    elif fault=='shared_fit': value['terrain_cards'][0]['ownership']['lio-road']['definition']['fit_identity']='terrain-fit:base'
    elif fault=='missing_mechanism': value['mechanism_evidence']['causal_prefix'].pop(next(iter(value['mechanism_evidence']['causal_prefix'])))
    elif fault=='missing_mode': value['numerical_score_and_variance_witnesses'].pop('point_only')
    elif fault=='missing_diagnostic': value['numerical_score_and_variance_witnesses']['causal_prefix']['per_origin_diagnostics'].pop('arm-18/full')
    elif fault=='diagnostic_denominator': value['mechanism_evidence']['causal_prefix']['arm-18/full']['expected_count']=1
    elif fault=='missing_replay': runtime['replay_rows'].pop()
    elif fault=='replay_failure_success': runtime['replay_rows'][0].update(status='reproduced_failure',successful_prediction_reproduced=True)
    elif fault=='replay_counts': runtime['replay_counts_by_status']={'NOT_ADMITTED':37}
    elif fault=='runtime_subject': runtime['runtime_subjects'].pop()
    elif fault=='runtime_trial': subject['rows'].pop()
    elif fault=='warmup_quantiles': subject['warmup_excluded_from_latency_quantiles']=False
    elif fault=='runtime_counts': subject['conditions']['runtime_cold']['counts_by_status']={'success':5}
    else: subject['conditions']['runtime_cold'].update(status='computed',summary={'total_latency_p50_ms':0})
    with pytest.raises(ValueError): module.project(value)


def test_copies_observed_timing_without_summing_nested_stages_or_promoting_failures(cards):
    subject=cards['isolated_runtime_and_replay']['runtime_subjects'][0]
    for i,row in enumerate(subject['rows']):
        row['status']='failed' if row['kind']=='runtime_cold' and row['repetition']==4 else 'success'
        row['warm_condition_verified']=True if row['kind']=='runtime_warm' else None
        row['measurement']=dict(hardware_sha256=module.digest('SOFTWARE hardware'),actual_horizon_seconds=1797,
            trial=dict(end_to_end_ms=100+i,inclusive_stage_ms={'rollout':90,'terrain_io_and_query':80},
                sampled_peak_rss_bytes=1234,process_lifetime_peak_rss_bytes=5678))
    for kind,condition in subject['conditions'].items():
        condition.update(status='computed',summary=dict(total_latency_p50_ms=123,total_latency_p95_ms=456,
            latency_denominator='successful_trials_only; all failures retained separately'),
            counts_by_status={'success':4,'failed':1} if kind=='runtime_cold' else {'success':5})
    replay=cards['isolated_runtime_and_replay']['replay_rows'][0]
    replay.update(original_status='failed',replay_status='failed',status='reproduced_failure',output_identity_equal=True)
    cards['isolated_runtime_and_replay']['replay_counts_by_status']={'NOT_ADMITTED':37,'reproduced_failure':1}
    tables=module.project(cards)
    rows=[r for r in tables['runtime_trials'] if r['subject']==subject['subject'] and r['matrix']==subject['matrix']]
    assert len(rows)==11 and sum(r['included_in_latency_quantiles'] for r in rows)==9
    assert rows[0]['end_to_end_ms']==100 and rows[0]['inclusive_stage_ms']['rollout']==90
    assert all(r['actual_horizon_seconds']==1797 for r in rows)
    conditions=[r for r in tables['runtime_conditions'] if r['subject']==subject['subject'] and r['matrix']==subject['matrix']]
    assert all(r['summary']['total_latency_p95_ms']==456 for r in conditions)
    failed=next(r for r in tables['replays'] if r['status']=='reproduced_failure')
    assert failed['successful_prediction_reproduced'] is False


def test_separate_scoring_times_copy_entropy_and_coverage_without_new_hypotheses(cards):
    row=cards['metric_tables'][0]
    row.update(status='computed',expected_forecasts=1,available_score_rows=1,counts_by_status={'success':1},
        means={**{k:2 for k in module.METRICS},'by_time':[dict(nominal_seconds=t,actual_elapsed_seconds_range=[t-1,t+1],
            energy_score_m=3,position_entropy_nats=4,coverage=[dict(level=.95,coverage_rate=.9,mean_area_m2=5)])
            for t in module.SCORING_SECONDS]})
    tables=module.project(cards)
    rows=[r for r in tables['accuracy_times'] if (r['origin_mode'],r['matrix'],r['configuration'])==
        (row['origin_mode'],row['matrix'],row['configuration'])]
    assert len(rows)==4 and all(r['energy_score_m']==3 and r['position_entropy_nats']==4 for r in rows)
    assert rows[-1]['coverage'][0]['mean_area_m2']==5
