"""Fixed-protocol experiments, resumable by completed dataset result files."""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import random
from statistics import mean, median, stdev
from time import perf_counter
import numpy as np

from backend.study_loader import load_study_csv
from research.reconciled import build, derived, ROOT
from research.build_dataset import write_json
from research.experiment_engine import blocks, Outcomes, fit, FIELDS, paired_test
from research.evaluate import aggregate, pass_threshold

GENERATED=ROOT/'research/generated'
STUDY=GENERATED/'completed-study-v1'
TAGS=('p00','p25','p50','p75')
RULE_FIELDS=set(['emergency_fund','savings','insurance_coverage','sub_category','employed_members',
    'total_income_past_6_months','selfhelp_sought_income','selfhelp_reached_agencies']) | {
    k for k in FIELDS if k.startswith(('support_','ext_','vuln_')) or (k.startswith('crisis_') and k!='crisis_last_3_months')}


def records(path,tag='p50',kind='case_base'):
    return load_study_csv(path/f'{kind}_{tag}.csv').records


def dataset(seed):
    path=GENERATED/f'reconciled-{seed}'
    if not (path/'manifest.json').exists(): build(path,seed)
    return path


def metric(bs,data,weights=None,k=5):
    outcomes=Outcomes(bs,data)
    sums=[b.sums(np.ones(39) if weights is None else weights) for b in bs]
    objective,app,rows=outcomes.evaluate(sums,k,True)
    return dict(objective=objective,applicants=dict(zip(outcomes.ids,app.tolist())),events=rows)


def evidence(primary_base,primary_challenger,replicate_base,replicate_challenger,alpha):
    ids=sorted(primary_base['applicants'])
    assert ids==sorted(primary_challenger['applicants'])
    test=paired_test([primary_base['applicants'][a] for a in ids],[primary_challenger['applicants'][a] for a in ids])
    gaps=[b['objective']-c['objective'] for b,c in zip(replicate_base,replicate_challenger)]
    assert len(gaps)==30
    improvement=mean(gaps); noise=stdev(gaps)
    return dict(mean_scaled_improvement=improvement,noise_floor_sd=noise,gaps=gaps,wilcoxon=test,
                alpha=alpha,passes=improvement>noise and test['p']<alpha,
                primary_scaled_improvement=primary_base['objective']-primary_challenger['objective'])


def selection():
    dest=STUDY/'selection';dest.mkdir(parents=True,exist_ok=True)
    all_money=[]
    for seed in range(41000,41031):
        path=dest/f'money-{seed}.json'
        if path.exists(): result=json.loads(path.read_text())
        else:
            data=records(dataset(seed));result={}
            for money in ('plain','log','fuzzy'):
                result[money]=metric(blocks(data,data,money),data)
            write_json(path,result)
        all_money.append(result)
        print(f'money selection {seed} complete',flush=True)
    tests={m:evidence(all_money[0]['plain'],all_money[0][m],
        [r['plain'] for r in all_money[1:]],[r[m] for r in all_money[1:]],.025) for m in ('log','fuzzy')}
    passing=[m for m in ('log','fuzzy') if tests[m]['passes']]
    money=min(passing,key=lambda m:all_money[0][m]['objective']) if passing else 'plain'
    all_rank=[]
    for seed in range(41000,41031):
        path=dest/f'duration-{money}-{seed}.json'
        if path.exists(): result=json.loads(path.read_text())
        else:
            data=records(dataset(seed));result=metric(blocks(data,data,money,'rank'),data)
            write_json(path,result)
        all_rank.append(result)
        print(f'duration selection {seed} complete',flush=True)
    ranktest=evidence(all_money[0][money],all_rank[0],[r[money] for r in all_money[1:]],all_rank[1:],.05)
    chosen=dict(money=money,duration='rank' if ranktest['passes'] else 'categorical',
                money_evidence=tests,duration_evidence=ranktest)
    write_json(STUDY/'selected-settings.json',chosen)
    return chosen


def grouped_metric(rows):
    groups=defaultdict(list)
    for row in rows:
        if row['scaled_error'] is not None: groups[row['applicant_id']].append(row['scaled_error'])
    app={a:mean(v) for a,v in sorted(groups.items())}
    return dict(objective=mean(app.values()),applicants=app,events=rows)


def weight_run(path,master,chosen,dest):
    start=perf_counter()
    base={tag:records(path,tag) for tag in TAGS}
    data=base['p50']
    ids=sorted({r.applicant_id for r in data})
    random.Random(derived(master,'fold')).shuffle(ids)
    assignment={a:i%5 for i,a in enumerate(ids)}
    write_json(dest/'fold-assignment.json',assignment)
    full=blocks(data,data,chosen['money'],chosen['duration'])
    result={tag:dict(equal=metric(full,base[tag]),learned_rows=[],folds=[]) for tag in TAGS}
    reference=np.array([39/len(RULE_FIELDS) if f in RULE_FIELDS else 0 for f in FIELDS])
    for tag in TAGS: result[tag]['reference']=metric(full,base[tag],reference)
    del full
    for fold in range(5):
        train=[r for r in data if assignment[r.applicant_id]!=fold]
        test=[r for r in data if assignment[r.applicant_id]==fold]
        fitting=blocks(train,train,chosen['money'],chosen['duration'])
        testing=blocks(test,data,chosen['money'],chosen['duration'])
        for tag in TAGS:
            outcomes=Outcomes(fitting,base[tag])
            weights,trace=fit(fitting,outcomes,derived(master,'optimizer',fold+1))
            evaluated=metric(testing,base[tag],weights)
            result[tag]['learned_rows'].extend(evaluated['events'])
            top=np.argsort(-weights,kind='stable')[:10]
            result[tag]['folds'].append(dict(fold=fold,weights=dict(zip(FIELDS,weights.tolist())),
                rule_weight_fraction=float(sum(weights[i] for i,f in enumerate(FIELDS) if f in RULE_FIELDS)/39),
                zero_rule_fields_in_top_ten=[FIELDS[i] for i in top if FIELDS[i] not in RULE_FIELDS],
                final_fit_objective=trace[-1]['incumbent']))
            write_json(dest/f'{tag}-fold-{fold}-trace.json',trace)
        print(f'weights {master}: fold {fold+1}/5 complete',flush=True)
    for tag in TAGS:
        result[tag]['learned']=grouped_metric(result[tag].pop('learned_rows'))
        result[tag]['reference_gap']=result[tag]['learned']['objective']-result[tag]['reference']['objective']
        for method in ('equal','learned','reference'):
            result[tag][method]['summary']=aggregate(result[tag][method]['events'])
    result['runtime_seconds']=perf_counter()-start
    write_json(dest/'results.json',result)
    return result


def run_weights(chosen):
    dest=STUDY/'weights';dest.mkdir(exist_ok=True)
    primary=dest/'primary';primary.mkdir(exist_ok=True)
    if (primary/'results.json').exists(): first=json.loads((primary/'results.json').read_text())
    else: first=weight_run(GENERATED/'reconciled-primary',51000,chosen,primary)
    print(f'Primary five-fold/four-condition run: {first["runtime_seconds"]:.1f} seconds; fixed budget retained',flush=True)
    # Generate sequentially: the supplied generator loads module-level constants.
    # Independent fitting jobs can then run concurrently without shared mutation.
    for seed in range(51001,51031): dataset(seed)
    def replicate(seed):
        folder=dest/str(seed);folder.mkdir(exist_ok=True)
        if (folder/'results.json').exists(): result=json.loads((folder/'results.json').read_text())
        else: result=weight_run(dataset(seed),seed,chosen,folder)
        # Evidence needs paired applicant errors, not all event/trace payloads in RAM.
        return {tag:{method:{key:result[tag][method][key] for key in ('objective','applicants')}
                     for method in ('equal','learned')} for tag in TAGS}
    with ThreadPoolExecutor(max_workers=3) as workers:
        reps=list(workers.map(replicate,range(51001,51031)))
    tests={tag:evidence(first[tag]['equal'],first[tag]['learned'],
        [r[tag]['equal'] for r in reps],[r[tag]['learned'] for r in reps],.05) for tag in TAGS}
    write_json(STUDY/'weight-evidence.json',tests)
    # Repeated deterministic full evaluation timings, not independent observations.
    timings=[first['runtime_seconds']]
    for repetition in (2,3):
        folder=dest/f'timing-repeat-{repetition}';folder.mkdir(exist_ok=True)
        if (folder/'results.json').exists(): repeated=json.loads((folder/'results.json').read_text())
        else: repeated=weight_run(GENERATED/'reconciled-primary',51000,chosen,folder)
        for tag in TAGS:
            assert repeated[tag]['learned']==first[tag]['learned']
            assert repeated[tag]['folds']==first[tag]['folds']
        timings.append(repeated['runtime_seconds'])
    write_json(STUDY/'full-runtime.json',dict(runs_seconds=timings,median_seconds=median(timings),
        scope='Full five-fold evaluation of all four conditions, including distance construction, 200-candidate searches, held-out evaluation, reference/equal comparison and trace writes'))


def final_diagnostics(chosen):
    path=GENERATED/'reconciled-primary'
    out={}
    for tag in TAGS:
        data=records(path,tag);judged=records(path,tag,'judged')
        settings={}
        for name,money,duration in [('plain','plain','categorical'),('selected',chosen['money'],chosen['duration'])]:
            m=metric(blocks(judged,data,money,duration,True),data+judged)
            summary=aggregate(m['events']);m['summary']=summary
            m['main_test_pass']=pass_threshold(summary['non_transport']) if tag=='p50' else None
            settings[name]=m
        out[tag]=settings
    write_json(STUDY/'reviewed-results.json',out)
    primary=json.loads((STUDY/'weights/primary/results.json').read_text())
    assignment=json.loads((STUDY/'weights/primary/fold-assignment.json').read_text())
    sensitivity={}
    for tag in TAGS:
        data=records(path,tag);full=blocks(data,data,chosen['money'],chosen['duration'])
        sensitivity[tag]={str(k):dict(equal=metric(full,data,k=k),learned_rows=[]) for k in (3,5,7,10)}
        del full
        for fold in range(5):
            test=[r for r in data if assignment[r.applicant_id]==fold]
            bs=blocks(test,data,chosen['money'],chosen['duration'])
            w=np.array([primary[tag]['folds'][fold]['weights'][f] for f in FIELDS])
            for k in (3,5,7,10): sensitivity[tag][str(k)]['learned_rows'].extend(metric(bs,data,w,k)['events'])
        for k,row in sensitivity[tag].items():
            row['learned']=grouped_metric(row.pop('learned_rows'))
    write_json(STUDY/'k-sensitivity.json',sensitivity)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=['selection','weights','diagnostics','all'],default='all')
    args=parser.parse_args()
    STUDY.mkdir(exist_ok=True)
    if args.phase in ('selection','all'): chosen=selection()
    else: chosen=json.loads((STUDY/'selected-settings.json').read_text())
    if args.phase in ('weights','all'): run_weights(chosen)
    if args.phase in ('diagnostics','all'): final_diagnostics(chosen)
    write_json(STUDY/'code-hashes.json',{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in list((ROOT/'research').glob('*.py'))+[ROOT/'research/RECONCILIATION.md',ROOT/'research/METHOD_CHOICES_FOR_REVIEW.md']})


if __name__=='__main__': main()
