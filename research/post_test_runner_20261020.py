"""Prospectively recorded post-failure amendments; outputs never replace old runs."""
import argparse,hashlib,json,random
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from statistics import mean,median
from time import perf_counter
import numpy as np
from backend.study_loader import load_study_csv
from research.corrected_amounts_20261020 import correct_dataset,FIELDS as HOUSEHOLD_FIELDS
from research.reconciled import derived
from research.experiment_engine import blocks,Outcomes,fit,FIELDS
from research.run_experiments import metric,grouped_metric,evidence
from research.evaluate import aggregate,pass_threshold
from research.build_dataset import write_json

ROOT=Path(__file__).resolve().parents[1];GEN=ROOT/'research/generated'
DEST=GEN/'post-test-correction-2026-10-20-v1'
TAGS=('p00','p25','p50','p75')
CHOSEN={'money':'plain','duration':'categorical'}
RULE_FIELDS=set(HOUSEHOLD_FIELDS)|{'purpose_of_assistance'}

def data(path,tag='p50',kind='case_base'):
    return load_study_csv(path/f'{kind}_{tag}.csv').records

def ensure_corrected(name):
    folder=DEST/'data'/name
    if (folder/'manifest.json').exists():return folder
    return correct_dataset(GEN/('reconciled-primary' if name=='primary' else f'reconciled-{name}'),folder)

def weight_run(path,master,pool,dest):
    start=perf_counter();base={tag:data(path,tag) for tag in TAGS};inputs=base['p50']
    ids=sorted({r.applicant_id for r in inputs});random.Random(derived(master,'fold')).shuffle(ids)
    assignment={a:i%5 for i,a in enumerate(ids)}
    source=GEN/'completed-study-v1/weights'/('primary' if master==51000 else str(master))/'fold-assignment.json'
    assert assignment==json.loads(source.read_text()),'Fold assignment changed'
    write_json(dest/'fold-assignment.json',assignment)
    full=blocks(inputs,inputs,**CHOSEN,pool=pool)
    reference=np.array([39/len(RULE_FIELDS) if f in RULE_FIELDS else 0 for f in FIELDS])
    result={tag:dict(equal=metric(full,base[tag]),reference=metric(full,base[tag],reference),learned_rows=[],folds=[]) for tag in TAGS}
    del full
    for fold in range(5):
        train=[r for r in inputs if assignment[r.applicant_id]!=fold];test=[r for r in inputs if assignment[r.applicant_id]==fold]
        fitting=blocks(train,train,**CHOSEN,pool=pool);testing=blocks(test,inputs,**CHOSEN,pool=pool)
        for tag in TAGS:
            outcomes=Outcomes(fitting,base[tag]);weights,trace=fit(fitting,outcomes,derived(master,'optimizer',fold+1),budget=200)
            evaluated=metric(testing,base[tag],weights);result[tag]['learned_rows'].extend(evaluated['events'])
            for row in evaluated['events']:
                assert len(row['neighbors'])==5
                if pool=='purpose':assert 'purpose_of_assistance' not in row['active_fields']
            order=np.argsort(-weights,kind='stable')[:10]
            result[tag]['folds'].append(dict(fold=fold,weights=dict(zip(FIELDS,weights.tolist())),
                rule_weight_fraction=float(sum(weights[i] for i,f in enumerate(FIELDS) if f in RULE_FIELDS)/39),
                household_rule_weight_fraction=float(sum(weights[i] for i,f in enumerate(FIELDS) if f in HOUSEHOLD_FIELDS)/39),
                zero_rule_fields_in_top_ten=[FIELDS[i] for i in order if FIELDS[i] not in RULE_FIELDS],
                final_fit_objective=trace[-1]['incumbent']))
            assert len(trace)==200
            write_json(dest/f'{tag}-fold-{fold}-trace.json',trace)
    for tag in TAGS:
        result[tag]['learned']=grouped_metric(result[tag].pop('learned_rows'))
        result[tag]['reference_gap']=result[tag]['learned']['objective']-result[tag]['reference']['objective']
        for method in ('equal','learned','reference'):result[tag][method]['summary']=aggregate(result[tag][method]['events'])
    result['runtime_seconds']=perf_counter()-start;result['pool']=pool
    write_json(dest/'results.json',result)
    return result

def reviewed(path,pool):
    out={}
    for tag in TAGS:
        base=data(path,tag);judged=data(path,tag,'judged')
        bs=blocks(judged,base,**CHOSEN,reviewed=True,pool=pool)
        result=metric(bs,base+judged);result['summary']=aggregate(result['events']);result['main_test_pass']=pass_threshold(result['summary']['non_transport']) if tag=='p50' else None
        out[tag]=result
    return out

def run_pool(pool):
    out=DEST/pool;out.mkdir(exist_ok=True)
    if pool=='purpose' and not (DEST/'purpose-pool-feasibility.json').exists():
        from research.post_test_feasibility_20261020 import audit
        write_json(DEST/'purpose-pool-feasibility.json',audit(DEST/'data'))
    path=ensure_corrected('primary')
    reviewed_path=out/'reviewed-results.json'
    if not reviewed_path.exists():write_json(reviewed_path,reviewed(path,pool))
    print(pool+' corrected reviewed-case test complete',flush=True)
    folder=out/'weights/primary';folder.mkdir(parents=True,exist_ok=True)
    primary=json.loads((folder/'results.json').read_text()) if (folder/'results.json').exists() else weight_run(path,51000,pool,folder)
    print(pool+' primary five-fold/four-condition complete',flush=True)
    def replicate(seed):
        folder=out/f'weights/{seed}';folder.mkdir(parents=True,exist_ok=True)
        # Explicitly record a whole infeasible replication; never discard queries,
        # reduce k, change folds, or calculate a 30-set floor from 29 sets.
        if pool=='purpose':
            audit=json.loads((DEST/'purpose-pool-feasibility.json').read_text())
            failures=[r for r in audit['failures'] if r['dataset']==str(seed)]
            if failures:
                failure=dict(seed=seed,status='infeasible_fixed_k5_training_pool',failures=failures,
                    action='No fallback or query omission; fixed 30-set evidence unavailable')
                write_json(folder/'INFEASIBLE.json',failure)
                print(f'{pool} replicate {seed} explicitly infeasible: fewer than five eligible training references',flush=True)
                return failure
        result=json.loads((folder/'results.json').read_text()) if (folder/'results.json').exists() else weight_run(DEST/f'data/{seed}',seed,pool,folder)
        print(f'{pool} replicate {seed} complete',flush=True)
        return {tag:{m:{k:result[tag][m][k] for k in ('objective','applicants')} for m in ('equal','learned')} for tag in TAGS}
    with ThreadPoolExecutor(max_workers=3) as worker:reps=list(worker.map(replicate,range(51001,51031)))
    unavailable=[r for r in reps if r.get('status')=='infeasible_fixed_k5_training_pool']
    if unavailable:
        from research.experiment_engine import paired_test
        ids=sorted(primary['p50']['equal']['applicants'])
        tests={tag:dict(status='unavailable_incomplete_fixed_30_replications',passes=False,
            mean_scaled_improvement=None,noise_floor_sd=None,
            completed_replications=30-len(unavailable),infeasible_replications=unavailable,
            alpha=.05,wilcoxon=paired_test([primary[tag]['equal']['applicants'][a] for a in ids],[primary[tag]['learned']['applicants'][a] for a in ids]),
            primary_scaled_improvement=primary[tag]['equal']['objective']-primary[tag]['learned']['objective'],
            reason='The fixed thirty-set evidence rule cannot be evaluated; no 29-set substitution') for tag in TAGS}
    else:
        tests={tag:evidence(primary[tag]['equal'],primary[tag]['learned'],[r[tag]['equal'] for r in reps],[r[tag]['learned'] for r in reps],.05) for tag in TAGS}
    write_json(out/'weight-evidence.json',tests)
    timings=[primary['runtime_seconds']]
    for n in (2,3):
        folder=out/f'weights/timing-repeat-{n}';folder.mkdir(exist_ok=True)
        repeated=json.loads((folder/'results.json').read_text()) if (folder/'results.json').exists() else weight_run(path,51000,pool,folder)
        for tag in TAGS:
            assert repeated[tag]['learned']==primary[tag]['learned']
            assert repeated[tag]['folds']==primary[tag]['folds']
        timings.append(repeated['runtime_seconds'])
    write_json(out/'runtime.json',dict(runs_seconds=timings,median_seconds=median(timings),scope='Primary five-fold/four-condition evaluation, fixed 200-evaluation searches and trace writes'))
    sensitivity={}
    assignment=json.loads((out/'weights/primary/fold-assignment.json').read_text())
    for tag in TAGS:
        inputs=data(path,tag);full=blocks(inputs,inputs,**CHOSEN,pool=pool)
        sensitivity[tag]={str(k):{'equal':metric(full,inputs,k=k),'learned_rows':[]} for k in (3,5,7,10)}
        del full
        for fold in range(5):
            test=[r for r in inputs if assignment[r.applicant_id]==fold];bs=blocks(test,inputs,**CHOSEN,pool=pool)
            w=np.array([primary[tag]['folds'][fold]['weights'][f] for f in FIELDS])
            for k,row in sensitivity[tag].items():row['learned_rows'].extend(metric(bs,inputs,w,k=int(k))['events'])
        for row in sensitivity[tag].values():row['learned']=grouped_metric(row.pop('learned_rows'))
    write_json(out/'k-sensitivity.json',sensitivity)
    write_json(out/'COMPLETE.json',dict(pool=pool,conditions=list(TAGS),replications_attempted=30,
        completed_replications=30-len(unavailable),infeasible_replications=unavailable,
        weight_evidence_complete=not unavailable,reviewed_test_complete=True,settings=CHOSEN))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['prepare','type','purpose','all'],default='all');args=parser.parse_args()
    DEST.mkdir(parents=True,exist_ok=True)
    if args.phase in ('prepare','all'):
        # Every pair check across every corrected dataset precedes any evaluation.
        for name in ['primary']+[str(i) for i in range(51001,51031)]:
            ensure_corrected(name);print('Corrected data and immediate pair checks passed: '+name,flush=True)
        write_json(DEST/'ALL_PAIR_CHECKS_PASSED.json',dict(datasets=31,conditions=4,identical_pairs_per_condition=4,order_invariant=True))
        write_json(DEST/'code-frozen-before-evaluation.json',{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'research/corrected_amounts_20261020.py',ROOT/'research/experiment_engine.py',Path(__file__),ROOT/'research/POST_TEST_DECISION_2026-10-20_v01.md']})
    if args.phase in ('type','purpose','all'):
        assert (DEST/'ALL_PAIR_CHECKS_PASSED.json').exists()
    if args.phase in ('type','all'):run_pool('type')
    if args.phase in ('purpose','all'):
        assert (DEST/'type/COMPLETE.json').exists(),'Original corrected type-pool must finish first'
        run_pool('purpose')

if __name__=='__main__':main()
