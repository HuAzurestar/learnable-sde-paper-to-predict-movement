"""Deterministic review figures from pinned PUBLIC PIRC17 cards only.

Not manuscript delivery, scientific qualification or acceptance. No private
reader, prediction, fitting, hypothesis test, quantile or bootstrap runs here.
Technical labels are preliminary, not a chosen manuscript language/template.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
import uuid

from scripts import aggregate_pirc17 as tables

VERSION = 'pirc17-public-review-figures-v1'
DPI = 140
FORMATS = ('png','pdf')


def specification(cards,*,software_fixture=False):
    """Exact plot inputs, also saved as public machine-readable provenance."""
    data=tables.project(cards)
    if any(cards['fixed_forecast'].get(k)!=v for k,v in dict(
            particles=512,max_step_seconds=5,nominal_horizon_seconds=1800).items()):
        raise ValueError('figure labels require the unchanged fixed512/5s/1800s forecast')
    figures={}
    def add(name,kind,title,rows,**options):
        figures[name]=dict(kind=kind,title=title,rows=rows,software_fixture_only=software_fixture,**options)
    for mode in tables.MODES:
        for matrix,prefix in (('terrain','weighted-es-'),('methods','method-')):
            add(f'paired-{matrix}-{mode}','paired',f'{matrix}: {mode}',
                [r for r in data['comparisons'] if r['origin_mode']==mode and r['family_id'].startswith(prefix)],
                practical_margin_m=cards['inference_config'].get('delta_m'),
                interval_scope='Original simultaneous within-family intervals only; secondary modes descriptive.',
                sign='Candidate minus control ES; negative favours candidate. No across-family FWER claim.')
        add('terrain-times-'+mode,'times','Terrain time profiles: '+mode,
            [r for r in data['accuracy_times'] if r['origin_mode']==mode and r['matrix']=='terrain'],
            displayed_region_level=.95,scope='Four nominal scoring times; segments guide the eye, not interpolated targets or scores. All region levels remain in source tables.')
        add('mechanisms-'+mode,'mechanisms','Mechanism evidence availability: '+mode,
            [r for r in data['mechanisms'] if r['origin_mode']==mode],
            scope='Availability counts and recorded mechanism flags, not predictive effects or global numerical convergence.')
    add('runtime-conditions','runtime','Isolated cold/warm runtime',data['runtime_conditions'],
        scope='Five trials per condition; original successful-trial p50/p95, all failures retained. Warmup excluded; no new quantiles.')
    add('terrain-dimensions','dimensions','Declared terrain input dimensions',data['terrain_configurations'],
        scope='Numeric and validity channels; history retained. Declared dimensions are not proof of successful fit or effect.')
    add('scientific-dispositions','dispositions','Scientific work dispositions',data['kernel_costs'],
        scope='All38 subjects/290 items each. Retained interruption is not a model-performance failure.')
    add('recorded-kernel-costs','kernel','Recorded prediction kernel cost',data['kernel_costs'],
        scope='Recorded-item mean only, not isolated latency or whole project cost; missing timings retained.')
    if len(figures)!=16:
        raise ValueError('complete sixteen-figure interface required')
    return dict(schema_version=VERSION,figures=figures,scope=cards['scope'],
        source_export_sha256=cards['source_export_sha256'],source_catalog_sha256=cards['source_catalog_sha256'],
        fixed_forecast=cards['fixed_forecast'],uncertainty=cards['uncertainty'],multiplicity=cards['multiplicity'],
        limitations=cards['limitations'],paper_wording_rule=cards['paper_wording_rule'],
        review_state='rendered-review-candidate',scientific_claim_authorized=False,human_accepted=False,
        manuscript_written=False,software_fixture_only=software_fixture,new_forecasts=0,new_fits=0,new_hypothesis_tests=0)


def render_environment():
    import matplotlib
    import matplotlib.ft2font
    import numpy
    import PIL
    font=Path(matplotlib.get_data_path())/'fonts/ttf/DejaVuSans.ttf'
    return dict(matplotlib=matplotlib.__version__,numpy=numpy.__version__,pillow=PIL.__version__,
        freetype=matplotlib.ft2font.__freetype_version__,font_sha256=hashlib.sha256(font.read_bytes()).hexdigest(),
        dpi=DPI,formats=list(FORMATS),backend='Agg PNG; PDF vector',style='matplotlib defaults + fixed DejaVu Sans')


def _number(value):
    if value is None: return math.nan
    if type(value) not in (int,float) or not math.isfinite(value):
        raise ValueError('finite plotted value or explicit absence required')
    return value


def _labels(axis,labels):
    axis.set_yticks(range(len(labels)),labels)
    axis.set_ylim(len(labels)-.5,-.5)
    axis.grid(axis='x',alpha=.2)


def _missing(axis,y,text='unavailable'):
    axis.text(.98,y,text,transform=axis.get_yaxis_transform(),ha='right',va='center',color='#666666',fontsize=7)


def _paired(fig,item):
    families=[f for f in tables.FAMILIES if any(r['family_id']==f for r in item['rows'])]
    rows=math.ceil(len(families)/2)
    axes=fig.subplots(rows,2,squeeze=False)
    fig.set_size_inches(12,3*rows+1.2)
    for axis,family in zip(axes.flat,families):
        records=[r for r in item['rows'] if r['family_id']==family]
        _labels(axis,[r['comparison_id'] for r in records])
        axis.set_title(family,fontsize=9)
        axis.set_xlabel('Candidate - control energy score (m)')
        axis.axvline(0,color='#444444',linewidth=.8)
        margin=item['practical_margin_m']
        if margin is not None:
            for x in (-_number(margin),_number(margin)):
                axis.axvline(x,color='#888888',linestyle=':',linewidth=.8)
        for y,r in enumerate(records):
            point=_number(r['delta_candidate_minus_control_m'])
            low,high=r['simultaneous_lower_m'],r['simultaneous_upper_m']
            if (low is None)!=(high is None) or low is not None and _number(low)>_number(high):
                raise ValueError('both ordered original interval endpoints required')
            if math.isnan(point):
                if low is not None: raise ValueError('interval cannot invent a missing point estimate')
                _missing(axis,y,r['verdict'])
            else:
                if low is not None:
                    # Bootstrap intervals need not contain the estimate. Draw
                    # endpoints directly, never clip or invent symmetric xerr.
                    axis.hlines(y,low,high,color='#2369a1',linewidth=2)
                axis.plot(point,y,'o',color='#2369a1',markersize=4)
                axis.annotate(r['verdict'],(point,y),xytext=(4,5),textcoords='offset points',fontsize=6)
    for axis in list(axes.flat)[len(families):]: axis.set_axis_off()


def _times(fig,item):
    axes=fig.subplots(2,2)
    fig.set_size_inches(11,7.5)
    keys=('energy_score_m','position_entropy_nats','coverage_rate','mean_area_m2')
    titles=('Energy score (m)','Marginal position entropy (nats)','95% region coverage (probability)','95% region area (m^2)')
    configurations=sorted({r['configuration'] for r in item['rows']})
    any_data=False
    for name in configurations:
        rows=sorted([r for r in item['rows'] if r['configuration']==name],key=lambda r:r['nominal_seconds'])
        for axis,key,title in zip(axes.flat,keys,titles):
            values=[]
            for r in rows:
                if key in keys[:2]: value=r[key]
                else:
                    level=None if r['coverage'] is None else next((c for c in r['coverage'] if c['level']==.95),None)
                    if r['coverage'] is not None and level is None:
                        raise ValueError('recorded coverage requires the displayed registered95% level')
                    value=None if level is None else level[key]
                values.append(_number(value))
            if any(math.isfinite(v) for v in values):
                axis.plot([r['nominal_seconds']/60 for r in rows],values,'o-',label=name,markersize=3,linewidth=1)
                any_data=True
            axis.set_title(title)
            axis.set_xlabel('Nominal scoring time (min)')
            axis.set_xticks([t/60 for t in tables.SCORING_SECONDS])
            axis.grid(alpha=.2)
    axes[1,0].axhline(.95,color='#888888',linestyle=':')
    axes[1,0].set_ylim(0,1.05)
    for axis in axes.flat:
        handles,labels=axis.get_legend_handles_labels()
        if handles: axis.legend(handles,labels,fontsize=6,ncol=2)
        else: axis.text(.5,.5,'No complete metric evidence',transform=axis.transAxes,ha='center',color='#666666')
    return any_data


def _rows(fig,item):
    rows=item['rows']
    kind=item['kind']
    count=3 if kind=='runtime' else 1
    axes=fig.subplots(1,count,squeeze=False)[0]
    fig.set_size_inches(12 if count==3 else 10,max(4.5,len(rows)*.23+2))
    if kind=='runtime':
        keys=sorted({(r['matrix'],r['subject']) for r in rows})
        fig.set_size_inches(14,7)
        for axis,title in zip(axes,('Successful-trial p50 (ms)','Successful-trial p95 (ms)','Failed trials (count / 5)')):
            _labels(axis,[m+':'+s for m,s in keys]); axis.set_title(title)
        for kind,offset,color in (('runtime_cold',-.15,'#2369a1'),('runtime_warm',.15,'#c07020')):
            for y,key in enumerate(keys):
                r=next(r for r in rows if (r['matrix'],r['subject'])==key and r['condition']==kind)
                for axis,field in zip(axes[:2],('total_latency_p50_ms','total_latency_p95_ms')):
                    value=None if r['summary'] is None else r['summary'][field]
                    if value is None: _missing(axis,y+offset,kind[8:]+': no latency')
                    else: axis.plot(_number(value),y+offset,'o',color=color,markersize=4,label=kind[8:] if y==0 else None)
                axes[2].plot(r['counts_by_status'].get('failed',0),y+offset,'o',color=color,markersize=4,
                    label=kind[8:] if y==0 else None)
                axes[2].annotate('missing: '+str(r['counts_by_status'].get('NOT_ADMITTED',0)),
                    (r['counts_by_status'].get('failed',0),y+offset),xytext=(5,0),textcoords='offset points',fontsize=6)
        axes[2].set_xlim(-.2,6)
        for axis in axes:
            handles,labels=axis.get_legend_handles_labels()
            if handles: axis.legend(handles,labels,fontsize=7)
        return
    axis=axes[0]
    labels=[r['configuration'] if kind=='dimensions' else r['slot_id'] if kind=='mechanisms'
            else r['matrix']+':'+r['subject'] for r in rows]
    _labels(axis,labels)
    if kind=='dimensions':
        values=[r['definition']['numeric_input_dimension'] for r in rows]
        axis.barh(range(len(rows)),values,label='numeric',color='#2369a1')
        axis.barh(range(len(rows)),values,left=values,label='validity',color='#8cbdde')
        axis.set_xlabel('Declared conditioner input channels'); axis.legend(fontsize=7)
    elif kind=='dispositions':
        left=[0]*len(rows)
        for status,color in (('success','#458b63'),('failed','#bd7539'),('NOT_ADMITTED','#b0b0b0')):
            values=[r['counts_by_status'].get(status,0) for r in rows]
            axis.barh(range(len(rows)),values,left=left,label=status,color=color)
            left=[a+b for a,b in zip(left,values)]
        axis.set_xlabel('Registered scientific work items (290 / subject)'); axis.legend(fontsize=7)
    elif kind=='kernel':
        for y,r in enumerate(rows):
            value=r['recorded_kernel_mean_seconds']
            if value is None: _missing(axis,y,'no recorded timings (0/290)')
            else:
                axis.plot(_number(value),y,'o',color='#2369a1',markersize=4)
                axis.annotate(str(r['recorded_timing_count'])+'/290 recorded',(value,y),xytext=(5,0),textcoords='offset points',fontsize=6)
        axis.set_xlabel('Recorded-item mean kernel time (s), NOT isolated latency')
    elif kind=='mechanisms':
        for y,r in enumerate(rows):
            expected=r['expected_count']
            if expected:
                color='#458b63' if r['passed'] is True else '#bd7539' if r['passed'] is False else '#b0b0b0'
                axis.barh(y,100*r['available_count']/expected,color=color)
            _missing(axis,y,r['status']+': '+str(r['available_count'])+'/'+str(expected))
        axis.set_xlim(0,130); axis.set_xlabel('Available registered mechanism instances (%)')
    else: raise ValueError('unknown figure kind')


def render(item,format):
    import matplotlib as mpl
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    if format not in FORMATS: raise ValueError('PNG or PDF required')
    with mpl.rc_context(rc=mpl.rcParamsDefault):
        mpl.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'text.usetex':False,
            'axes.unicode_minus':False,'pdf.compression':6})
        fig=Figure(dpi=DPI)
        FigureCanvasAgg(fig)
        try:
            if item['kind']=='paired': _paired(fig,item)
            elif item['kind']=='times': _times(fig,item)
            else: _rows(fig,item)
            marker=' | SOFTWARE FIXTURE' if item.get('software_fixture_only') else ' | REVIEW CANDIDATE'
            fig.suptitle(item['title']+marker,fontsize=11)
            fig.text(.5,.015,'Not human accepted; fixed N512 / max step5s / nominal30min. No new inference.',ha='center',fontsize=7)
            fig.tight_layout(rect=(0,.045,1,.95))
            stream=io.BytesIO()
            metadata={'Software':'PIRC17 public review renderer'} if format=='png' else {
                'Creator':'PIRC17 public review renderer','CreationDate':None,'ModDate':None}
            fig.savefig(stream,format=format,dpi=DPI,metadata=metadata)
            return stream.getvalue()
        finally:
            fig.clear()


def _publish(path,raw):
    if path.exists():
        if path.is_symlink() or path.read_bytes()!=raw:
            raise ValueError('existing figure differs; never overwrite reviewed output')
        return
    temporary=path.with_name('.'+path.name+'.'+uuid.uuid4().hex+'.tmp')
    with temporary.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary,path)


def generate(path,sha256,output_directory,*,software_fixture=False):
    cards=tables.load_cards(path,sha256)
    spec=specification(cards,software_fixture=software_fixture)
    identity=dict(schema_version=VERSION,source_cards_sha256=sha256,
        renderer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        table_consumer_sha256=hashlib.sha256(Path(tables.__file__).read_bytes()).hexdigest(),
        software_fixture_only=software_fixture,environment=render_environment())
    root=Path(output_directory)/tables.digest(identity)
    root.mkdir(parents=True,exist_ok=True)
    # Immutable manifest supplies byte hashes for a cheap restart. It is a
    # renderer completion record, not permission/qualification for any science.
    manifest_path=root/'manifest.json'
    previous=None
    if manifest_path.exists():
        previous=tables.load_cards(manifest_path,tables.digest(json.loads(manifest_path.read_bytes())['payload']))
        if previous['identity']!=identity or previous['specification_sha256']!=tables.digest(spec):
            raise ValueError('existing figure source differs')
    files={}
    for name,item in spec['figures'].items():
        for format in FORMATS:
            key=name+'.'+format
            target=root/key
            if previous is not None and target.is_file():
                binding=previous['files'][key]
                if target.is_symlink() or hashlib.sha256(target.read_bytes()).hexdigest()!=binding['sha256']:
                    raise ValueError('existing figure differs; never overwrite reviewed output')
                files[key]=binding
                continue
            raw=render(item,format)
            _publish(target,raw)
            files[key]=dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),figure_id=name)
    raw=tables.canonical(spec)+b'\n'
    _publish(root/'figure-inputs.json',raw)
    files['figure-inputs.json']=dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
    manifest=dict(identity=identity,specification_sha256=tables.digest(spec),files=files,
        review_state='rendered-review-candidate',scientific_claim_authorized=False,human_accepted=False,
        manuscript_written=False,new_forecasts=0,new_fits=0,new_hypothesis_tests=0)
    _publish(manifest_path,tables.canonical(dict(payload=manifest,sha256=tables.digest(manifest)))+b'\n')
    return dict(bundle_id=tables.digest(identity),manifest_sha256=tables.digest(manifest),
        output_directory=str(root),figure_count=len(spec['figures']),image_count=32)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cards',type=Path,required=True)
    parser.add_argument('--sha256',required=True)
    parser.add_argument('--output-directory',type=Path,required=True)
    parser.add_argument('--software-fixture',action='store_true',help='Watermark synthetic software demonstrations; never empirical results.')
    args=parser.parse_args(argv)
    print(json.dumps(generate(args.cards,args.sha256,args.output_directory,software_fixture=args.software_fixture)),flush=True)


if __name__=='__main__': main()
