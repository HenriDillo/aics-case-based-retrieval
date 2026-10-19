"""Build four amount conditions and audit files without changing source inputs.

python -m research.build_dataset --output research/generated/v26
Output directory must not already exist. No retrieval is run by this command.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import statistics

from backend.study_loader import load_study_csv
from backend.study_schema import MATCHING_FIELDS, NOT_APPLICABLE, PRINTED_TO_CANONICAL
from .amounts import (assign_costs, calibrate, content, generate, income_band,
                      repair_wage_labels)
from .policy import (AMOUNT_SEED,COST_SEED,DIRECT,EXACT_PAIRS,FLOORS,NEAR_PAIRS,
                     SETTINGS,SHARES,SOURCE_URL,VERSION)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')


def write_csv(path, records):
    printed = records[0].source == 'printed_v11'
    headers = list(records[0].raw)
    if not printed and 'documented_cost' not in headers:
        headers.append('documented_cost')
    with path.open('w',encoding='utf-8-sig',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=headers)
        writer.writeheader()
        for record in records:
            # Preserve untouched source cells exactly, including unknown markers.
            row = dict(record.raw)
            for key in ('sub_category','documented_cost','amount_granted'):
                label = next((k for k,v in PRINTED_TO_CANONICAL.items() if v==key),key) if printed else key
                value = record.values.get(key)
                if key == 'documented_cost' and printed:
                    continue  # existing documented-cost text is authoritative
                if key == 'sub_category':
                    original = load_subcategory(row[label])
                    if original == value:
                        continue
                row[label] = ('' if value is None else
                              ('|'.join(sorted(value)) or NOT_APPLICABLE) if isinstance(value,frozenset)
                              else str(value))
            writer.writerow(row)


def load_subcategory(raw):
    from backend.study_loader import parse_value
    return parse_value('sub_category',raw)


def validate_amounts(records):
    failures = []
    for r in records:
        v=r.values
        purpose,typ,amount,cost=v['purpose_of_assistance'],v['assistance_type_granted'],v['amount_granted'],v.get('documented_cost')
        if amount % 50 or amount < FLOORS.get(typ,0):
            failures.append([r.applicant_id,r.event_id,'rounding/floor'])
        cap = DIRECT[purpose][2] if purpose in DIRECT else SHARES[purpose][3]
        if cap is not None and amount > cap:
            failures.append([r.applicant_id,r.event_id,'ceiling'])
        if purpose not in DIRECT and amount > cost:
            failures.append([r.applicant_id,r.event_id,'cost exceeded'])
        if purpose in DIRECT and cost != NOT_APPLICABLE:
            failures.append([r.applicant_id,r.event_id,'unexpected direct-type cost'])
        if typ == 'Transportation' and amount != cost:
            failures.append([r.applicant_id,r.event_id,'ticket mismatch'])
    return failures


def pair_report(records):
    by={r.applicant_id:r for r in records}
    exact=[]
    for a,b in EXACT_PAIRS:
        same_input = content(by[a]) == content(by[b]) and by[a].values['documented_cost'] == by[b].values['documented_cost']
        exact.append(dict(a=a,b=b,identical_content=same_input,
                          equal_amount=by[a].values['amount_granted']==by[b].values['amount_granted']))
    near=[]
    for a,b,expected in NEAR_PAIRS:
        diff=[k for k in MATCHING_FIELDS if by[a].values[k]!=by[b].values[k]]
        near.append(dict(a=a,b=b,expected_field=expected,differing_fields=diff,
                         difference_in_amount=by[b].values['amount_granted']-by[a].values['amount_granted']))
    return dict(exact=exact,near=near)


def summarize(records):
    rows=[]
    for purpose in sorted({r.values['purpose_of_assistance'] for r in records}):
        group=[r for r in records if r.values['purpose_of_assistance']==purpose]
        mean_amount=statistics.mean(r.values['amount_granted'] for r in group)
        direct=purpose in DIRECT
        mean_cost=None if direct else statistics.mean(r.values['documented_cost'] for r in group)
        rows.append(dict(purpose=purpose,n=len(group),mean_cost=mean_cost,mean_amount=mean_amount,
                         aggregate_share=None if direct else mean_amount/mean_cost,
                         rule_base=DIRECT[purpose][1] if direct else SHARES[purpose][1]))
    return rows


def build(output, base_path, judged_path):
    output=Path(output)
    if output.exists():
        raise ValueError('Output already exists; choose a new directory to preserve previous runs')
    sources={str(Path(p).resolve()):sha(p) for p in [base_path,judged_path]}
    base_raw=load_study_csv(base_path).records
    judged=load_study_csv(judged_path).records
    base,changes,unresolved=repair_wage_labels(base_raw)
    base,cost_report=assign_costs(base)
    calibration=calibrate(base)
    # Do not silently change the reviewed forty.
    _, judged_changes, judged_unresolved=repair_wage_labels(judged)
    if judged_changes:
        raise ValueError('Reviewed cases contain wage contradictions; review before changing them')
    generated={}
    checks={}
    for p in SETTINGS:
        tag=f'p{round(p*100):02d}'
        base_condition,base_diag=generate(base,p,calibration=calibration)
        judged_condition,judged_diag=generate(judged,p,calibration=calibration)
        pairs=pair_report(judged_condition)
        failures=validate_amounts(base_condition)+validate_amounts(judged_condition)
        if failures or not all(x['identical_content'] and x['equal_amount'] for x in pairs['exact']):
            raise ValueError(f'{tag}: amount or duplicate validation failed: {failures}')
        if any(x['differing_fields'] != [x['expected_field']] for x in pairs['near']):
            raise ValueError('Near pairs no longer differ in exactly their designated field')
        checks[tag]=dict(amount_violations=failures,pairs=pairs,
                         case_base_summary=summarize(base_condition),judged_summary=summarize(judged_condition))
        generated[tag]=(base_condition,judged_condition,base_diag,judged_diag)
    output.mkdir(parents=True)
    write_json(output/'calibration.json',calibration)
    write_json(output/'cost_checks.json',cost_report)
    write_json(output/'consistency_changes.json',dict(wage_label_repairs=changes,
               unverifiable_wage_labels=unresolved,judged_unverifiable_wage_labels=judged_unresolved))
    for tag,(base_condition,judged_condition,base_diag,judged_diag) in generated.items():
        for name,records in [('case_base',base_condition),('judged',judged_condition)]:
            path=output/f'{name}_{tag}.csv'
            write_csv(path,records)
            reread=load_study_csv(path).records
            if [r.values for r in reread] != [r.values for r in records]:
                raise AssertionError(f'{path}: round-trip changed normalized values')
        write_json(output/f'diagnostics_{tag}.json',dict(case_base=base_diag,judged=judged_diag))
    write_json(output/'validation.json',checks)
    for path,digest in sources.items():
        if sha(path)!=digest:
            raise AssertionError('Source unexpectedly changed')
    manifest=dict(version=VERSION,source_url=SOURCE_URL,source_hashes=sources,
        amount_seed=AMOUNT_SEED,cost_seed=COST_SEED,conditions=list(SETTINGS),
        primary_condition=.5,case_base_events=len(base),case_base_applicants=len({r.applicant_id for r in base}),
        judged_cases=len(judged),wage_label_repairs=len(changes),
        unverifiable_wage_labels=len(unresolved),
        income_bands={'case_base':dict(Counter(income_band(r.values['total_income_past_6_months'])[0] for r in base)),
                      'judged':dict(Counter(income_band(r.values['total_income_past_6_months'])[0] for r in judged))},
        missing_score_inputs={k:sum(r.values[k] is None for r in base) for k in MATCHING_FIELDS},
        cost_checks_pass=all(x['within_20_percent'] for x in cost_report['checks']),
        source_files_unchanged=True,amount_evaluation_run=False,
        policy_hashes={name:sha(Path(__file__).parent/name) for name in ['policy.py','amounts.py','build_dataset.py']},
        output_hashes={p.name:sha(p) for p in sorted(output.iterdir())})
    write_json(output/'manifest.json',manifest)
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    parser.add_argument('--case-base',default='backend/data/study_intake.csv')
    parser.add_argument('--judged',default='research/inputs/judged_cases_v11.csv')
    args=parser.parse_args()
    manifest=build(args.output,args.case_base,args.judged)
    print(json.dumps({k:manifest[k] for k in ['version','case_base_events','case_base_applicants',
          'judged_cases','wage_label_repairs','unverifiable_wage_labels','income_bands','cost_checks_pass']},indent=2))


if __name__=='__main__':
    main()
