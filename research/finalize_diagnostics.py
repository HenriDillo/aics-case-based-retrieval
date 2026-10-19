"""Complete reporting diagnostics without refitting weights or changing outcomes.

The household score uses 28 matching fields; purpose also enters the amount rule
through its base share. The paper's reference therefore includes purpose. Preserve
the narrower household-only reference for traceability, and label both explicitly.
"""
import json
from pathlib import Path
import numpy as np
from backend.study_schema import ASYMMETRIC_FIELDS
from research.run_experiments import STUDY,GENERATED,TAGS,RULE_FIELDS,records,metric
from research.experiment_engine import blocks,FIELDS
from research.build_dataset import write_json
from research.evaluate import aggregate

ALL_RULE_FIELDS=RULE_FIELDS | {'purpose_of_assistance'}


def add_weighted_counts(rows,by,weight_for):
    for row in rows:
        query=by[(row['applicant_id'],row['event_id'])]
        weights=weight_for(row['applicant_id'])
        counts=[]
        for aid,eid in row['neighbors']:
            neighbor=by[(aid,eid)]
            counts.append(int(sum(weights[field]>0 and query.values[field] is not None and
                neighbor.values[field] is not None and not (field in ASYMMETRIC_FIELDS and
                query.values[field] is False and neighbor.values[field] is False)
                for field in row['active_fields'])))
        row['neighbor_positive_weight_compared_field_counts']=counts


def main():
    chosen=json.loads((STUDY/'selected-settings.json').read_text())
    vector=np.array([39/len(ALL_RULE_FIELDS) if f in ALL_RULE_FIELDS else 0 for f in FIELDS])
    for folder in sorted((STUDY/'weights').iterdir()):
        path=folder/'results.json'
        if not path.exists(): continue
        data_path=GENERATED/('reconciled-'+folder.name if folder.name.isdigit() else 'reconciled-primary')
        result=json.loads(path.read_text())
        assignment=json.loads((folder/'fold-assignment.json').read_text())
        base=records(data_path)
        bs=blocks(base,base,chosen['money'],chosen['duration'])
        by={(r.applicant_id,r.event_id):r for r in base}
        for tag in TAGS:
            item=result[tag]
            if 'household_only_reference' not in item: item['household_only_reference']=item['reference']
            item['reference']=metric(bs,records(data_path,tag),vector)
            item['reference']['summary']=aggregate(item['reference']['events'])
            item['reference_gap']=item['learned']['objective']-item['reference']['objective']
            for fold in item['folds']:
                weights=fold['weights']
                fold['household_rule_weight_fraction']=sum(weights[f] for f in RULE_FIELDS)/39
                fold['rule_weight_fraction']=sum(weights[f] for f in ALL_RULE_FIELDS)/39
                top=sorted(FIELDS,key=lambda f:-weights[f])[:10]
                fold['zero_rule_fields_in_top_ten']=[f for f in top if f not in ALL_RULE_FIELDS]
            weight_for=lambda aid: item['folds'][assignment[aid]]['weights']
            add_weighted_counts(item['learned']['events'],by,weight_for)
            add_weighted_counts(item['reference']['events'],by,lambda aid: dict(zip(FIELDS,vector)))
        write_json(path,result)
        print('Finalized reporting',folder.name,flush=True)
    sensitivity=json.loads((STUDY/'k-sensitivity.json').read_text())
    first=json.loads((STUDY/'weights/primary/results.json').read_text())
    assignment=json.loads((STUDY/'weights/primary/fold-assignment.json').read_text())
    base=records(GENERATED/'reconciled-primary');by={(r.applicant_id,r.event_id):r for r in base}
    for tag in TAGS:
        for item in sensitivity[tag].values():
            add_weighted_counts(item['learned']['events'],by,lambda aid:first[tag]['folds'][assignment[aid]]['weights'])
    write_json(STUDY/'k-sensitivity.json',sensitivity)
    write_json(STUDY/'reporting-definitions.json',dict(household_score_fields=sorted(RULE_FIELDS),
        all_amount_rule_matching_fields=sorted(ALL_RULE_FIELDS),reference_includes_purpose=True,
        zero_rule_top_count=10,available_counts='neighbor_compared_field_counts',
        positive_weight_counts='neighbor_positive_weight_compared_field_counts',
        scope='Reporting only; learned weights, predictions, objectives, hypothesis tests and main test unchanged'))


if __name__=='__main__': main()
