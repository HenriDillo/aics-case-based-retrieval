"""Post-failure user-authorized score correction. Historical generator is intact."""
from copy import deepcopy
import hashlib,importlib.util,json,math,statistics
from pathlib import Path
from backend.study_loader import load_study_csv,parse_value
from backend.study_schema import PRINTED_TO_CANONICAL
from research.reconciled import printed
from research.policy import SHARES,DIRECT,FLOORS
from research.build_dataset import write_csv,write_json,validate_amounts,pair_report

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('post_test_amount_rule_20261020',ROOT/'research/vendor/amount_rule_v2.py')
RULE=importlib.util.module_from_spec(spec);spec.loader.exec_module(RULE)
LEGACY_SCORE=RULE.raw_score
for purpose in ('Laboratory','Dialysis','Chemotherapy'):
    RULE.BASE_SHARE[purpose]=(SHARES[purpose][1],'Existing source-table completion, unchanged')
    RULE.CEILING[f'Medical:{purpose}']=SHARES[purpose][3]

# Each entry is one source field; signed contributions use their exact prior bounds.
ABSENCE={'emergency_fund':1.,'savings':.8,'insurance_coverage':.8}
FLAGS={**{f'support_{k}':-.35 for k in ('family','relatives','friends','employer','church')},
    'vuln_elderly_child_pwd_pregnant':.7,'vuln_member_incapacitated':.7,'vuln_unstable_employment':.6,
    **{f'crisis_{k}':.3 for k in ('hospitalization','death_of_member','catastrophic_event','disablement','loss_of_livelihood','others')},
    'ext_philhealth':-.6,'ext_health_card':-.5,'ext_guarantee_letter_other_agency':-.7,
    **{f'ext_{k}':-.3 for k in ('mss_discount','senior_citizen_discount','pwd_discount')},
    'selfhelp_sought_income':-.4,'selfhelp_reached_agencies':-.4}
BOUNDS={f:(0.,w) for f,w in ABSENCE.items()} | {f:(min(0.,w),max(0.,w)) for f,w in FLAGS.items()} | {'sub_category':(0.,1.3),'employed_members':(0.,.6),'total_income_past_6_months':(0.,1.)}
FIELDS=tuple(sorted(BOUNDS));assert len(FIELDS)==28
LOWER=sum(a for a,b in BOUNDS.values());TOTAL_RANGE=sum(b-a for a,b in BOUNDS.values())

def components(values):
    out={}
    for f in FIELDS:
        v=values[f]
        if v is None:out[f]=None;continue
        if f in ABSENCE:t=ABSENCE[f]*(v is False)
        elif f in FLAGS:t=FLAGS[f]*(v is True)
        elif f=='sub_category':
            text=', '.join(sorted(v)) if isinstance(v,frozenset) else str(v)
            t=.8*('No Regular Income' in text)+.5*('4Ps' in text)
        elif f=='employed_members':t=.6*(v==0)
        else:t=1. if v<RULE.FOOD_6M else .5 if v<RULE.POVERTY_6M else 0.
        lo,hi=BOUNDS[f];assert lo-1e-12<=t<=hi+1e-12
        out[f]=float(t)
    return out

def score_details(values):
    terms=components(values);observed=[f for f in FIELDS if terms[f] is not None]
    available=sum(BOUNDS[f][1]-BOUNDS[f][0] for f in observed)
    if available<=0:raise ValueError('All household-rule inputs unknown: stop generation')
    numerator=sum(terms[f]-BOUNDS[f][0] for f in observed)
    score=LOWER+TOTAL_RANGE*numerator/available
    if not LOWER-1e-10<=score<=LOWER+TOTAL_RANGE+1e-10:raise AssertionError('Corrected score outside fixed range')
    return {'score':score,'observed_fields':len(observed),'unknown_fields':[f for f in FIELDS if terms[f] is None],
        'available_range':available,'full_range':TOTAL_RANGE,'lower_bound':LOWER}

def raw_score(row):
    values={target:parse_value(target,row[source]) for source,target in PRINTED_TO_CANONICAL.items() if target in BOUNDS}
    return score_details(values)['score']

RULE.raw_score=raw_score

def calibrate(records):
    vals=[score_details(r.values)['score'] for r in records]
    return {'mu':statistics.mean(vals),'sd':statistics.pstdev(vals) or 1.,'n':len(vals)}

def generate(records,p,calibration,seed):
    result=deepcopy(records);details=[]
    for record in result:
        row=RULE.generate([printed(record)],p,seed=seed,calib=calibration)[0]
        v=record.values;purpose=v['purpose_of_assistance'];typ=v['assistance_type_granted']
        cost=None if purpose in DIRECT else v['documented_cost']
        cap=DIRECT[purpose][2] if purpose in DIRECT else SHARES[purpose][3]
        upper=min([n for n in (cost,cap) if n is not None],default=math.inf)
        low_grid=math.ceil(FLOORS.get(typ,0)/50)*50
        high_grid=math.floor(upper/50)*50 if math.isfinite(upper) else upper
        if low_grid>high_grid:raise ValueError('Infeasible fixed cost/floor constraint')
        v['amount_granted']=int(min(high_grid,max(low_grid,row['amount_granted'])))
        details.append(dict(row,**score_details(v)))
    return result,details

def check_pairs(records):
    amounts=[{'case_id':r.applicant_id,'amount_granted':r.values['amount_granted']} for r in records]
    ids={r['case_id'] for r in amounts}
    assert all({a,b}<=ids for a,b in RULE.PAIRS),'Missing identical-pair member'
    failures=RULE.check_pairs(amounts);assert not failures,failures
    report=pair_report(records)
    assert all(x['identical_content'] and x['equal_amount'] for x in report['exact'])
    by={r.applicant_id:r for r in records}
    for x in report['exact']:
        a,b=by[x['a']],by[x['b']]
        x['unknown_rule_fields_a']=[f for f in FIELDS if a.values[f] is None]
        x['unknown_rule_fields_b']=[f for f in FIELDS if b.values[f] is None]
        assert x['unknown_rule_fields_a']==x['unknown_rule_fields_b']
    assert all(x['differing_fields']==[x['expected_field']] for x in report['near'])
    return {'vendor_check_pairs_failures':failures,'all_four_pairs_present':True,**report}

def correct_dataset(source,dest):
    source=Path(source);dest=Path(dest)
    if dest.exists():raise ValueError('New corrected dataset directory required')
    manifest=json.loads((source/'manifest.json').read_text())
    base=load_study_csv(source/'case_base_p50.csv').records
    judged=load_study_csv(source/'judged_p50.csv').records
    calibration=calibrate(base);seed=manifest['amount_seed'];checks={};all_outputs={};diags={}
    complete=[]
    for r in base+judged:
        if all(r.values[f] is not None for f in FIELDS):
            before=LEGACY_SCORE(printed(r));after=score_details(r.values)['score']
            assert math.isclose(before,after,abs_tol=1e-12)
            complete.append(abs(before-after))
    for p in [0.,.25,.5,.75]:
        tag=f'p{round(p*100):02d}'
        # Pair validation is immediate after corrected forty-case generation.
        fixed,diag=generate(judged,p,calibration,seed)
        checks[tag]=check_pairs(fixed)
        reversed_fixed,_=generate(list(reversed(judged)),p,calibration,seed)
        check_pairs(reversed_fixed)
        assert {r.applicant_id:r.values['amount_granted'] for r in fixed}=={r.applicant_id:r.values['amount_granted'] for r in reversed_fixed}
        corrected,base_diag=generate(base,p,calibration,seed)
        assert not validate_amounts(fixed) and not validate_amounts(corrected)
        prior_base=load_study_csv(source/f'case_base_{tag}.csv').records
        prior_fixed=load_study_csv(source/f'judged_{tag}.csv').records
        for old,new in zip(prior_base+prior_fixed,corrected+fixed):
            assert {k:v for k,v in old.values.items() if k!='amount_granted'}=={k:v for k,v in new.values.items() if k!='amount_granted'}
            if p==0:assert old.values['amount_granted']==new.values['amount_granted'],'p00 noise/content changed'
        all_outputs[tag]=(corrected,fixed);diags[tag]={'case_base':base_diag,'judged':diag}
    dest.mkdir(parents=True)
    write_json(dest/'check-pairs.json',dict(stage='Immediately after corrected generation, before any retrieval or fit',conditions=checks,record_order_invariance=True))
    write_json(dest/'calibration.json',calibration)
    write_json(dest/'score-bounds.json',dict(fields=BOUNDS,lower=LOWER,full_range=TOTAL_RANGE,complete_records_checked=len(complete),max_complete_score_difference=max(complete,default=0)))
    for tag,(corrected,fixed) in all_outputs.items():
        for kind,items in [('case_base',corrected),('judged',fixed)]:
            target=dest/f'{kind}_{tag}.csv';write_csv(target,items)
            reread=load_study_csv(target).records
            assert [r.values for r in reread]==[r.values for r in items]
        write_json(dest/f'diagnostics_{tag}.json',diags[tag])
    inputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source.glob('*.csv')}
    write_json(dest/'manifest.json',dict(version='post-test-corrected-2026-10-20-v1',source=str(source),source_csv_hashes=inputs,amount_seed=seed,
        source_master_seed=manifest.get('master_seed'),calibration=calibration,input_values_unchanged=True,p00_amounts_unchanged=True,
        pair_checks_passed=True,record_order_invariance=True,conditions=[0,.25,.5,.75],correction='shifted bounded available-field score',
        output_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.glob('*.csv')}))
    return dest
