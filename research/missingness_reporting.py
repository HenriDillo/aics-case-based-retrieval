"""Count unknowns in existing records only; never generate amounts or records."""
import json,math
from collections import Counter
from pathlib import Path
from backend.study_loader import load_study_csv
from backend.study_schema import MATCHING_FIELDS

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('C:/Users/henri/Downloads/aics-v25-for-henri/aics-v25')
HOUSEHOLD_FIELDS=set(['emergency_fund','savings','insurance_coverage','sub_category','employed_members','total_income_past_6_months','selfhelp_sought_income','selfhelp_reached_agencies']) | {k for k in MATCHING_FIELDS if k.startswith(('support_','ext_','vuln_')) or (k.startswith('crisis_') and k!='crisis_last_3_months')}
assert len(HOUSEHOLD_FIELDS)==28

def summarize(records,fields):
    n=len(records);counts={f:sum(r.values[f] is None for r in records) for f in sorted(fields)}
    distribution=Counter(sum(r.values[f] is None for f in fields) for r in records)
    return {'events':n,'fields':len(fields),'unknown_cells':sum(counts.values()),'fields_with_unknowns':sum(v>0 for v in counts.values()),'complete_events':distribution[0],'incomplete_events':n-distribution[0],'complete_percent':100*distribution[0]/n,'unknown_counts':counts,'unknown_fields_per_event':dict(sorted(distribution.items())),'independence_expected_complete_events':n*math.prod(1-v/n for v in counts.values())}

def measure():
    paths={'primary':ROOT/'research/generated/reconciled-primary/case_base_p50.csv','frozen_reviewed':SOURCE/'data/judged/judged_cases_as_printed_v11.csv'}
    out={}
    for name,path in paths.items():
        records=load_study_csv(path).records
        rawcounts={f:sum(r.raw[f].strip().lower() in ('','(not recorded)','not recorded') for r in records) for f in records[0].raw}
        intake_fields=[f for f in rawcounts if f!='amount_granted']
        out[name]={'matching':summarize(records,MATCHING_FIELDS),'household_rule':summarize(records,HOUSEHOLD_FIELDS),'raw_source_scope':{'columns':len(rawcounts),'unknown_cells':sum(rawcounts.values()),'fields_with_unknowns':sum(v>0 for v in rawcounts.values()),'events_with_any_unknown':sum(any(x.strip().lower() in ('','(not recorded)','not recorded') for x in r.raw.values()) for r in records),'nonzero_counts':{k:v for k,v in rawcounts.items() if v}},'source_non_outcome_scope':{'columns':len(intake_fields),'unknown_cells':sum(rawcounts[f] for f in intake_fields),'fields_with_unknowns':sum(rawcounts[f]>0 for f in intake_fields),'events_with_any_unknown':sum(any(r.raw[f].strip().lower() in ('','(not recorded)','not recorded') for f in intake_fields) for r in records)},'source_path':str(path)}
    return out

def add_missingness(md,data=None):
    if '### Exact record-level completeness' in md:return md
    data=measure() if data is None else data
    rows=[]
    for dataset,label in [('primary','Primary case base'),('frozen_reviewed','Frozen reviewed cases')]:
        for scope,name in [('matching','39 matching fields'),('household_rule','28 household-rule fields')]:
            r=data[dataset][scope]
            rows.append(f'| {label} | {name} | {r["events"]} | {r["unknown_cells"]} | {r["complete_events"]} | {r["incomplete_events"]} |')
    block='''### Exact record-level completeness

Counting the existing CSV records directly gives the following completeness figures. Unknown means an empty or explicitly unrecorded value under the existing loader; explicit No, numeric zero and recorded not-applicable values are not counted as unknown. These are event counts, not counts of distinct applicants.

| Dataset | Field scope | Events | Unknown cells | Complete events | Incomplete events |
| --- | --- | --- | --- | --- | --- |
'''+ '\n'.join(rows)+'''

For the 39 matching fields, 463 of 1,000 events (46.3%) are complete. The 772 unknown cells give a mean cell-level rate of 1.98%; multiplying the per-field observed proportions under an independence assumption would predict approximately 457.6 complete events, but the actual joint count is 463. For the correction to the household score, the relevant direct count is narrower: 455 events (45.5%) have an unknown in at least one of its 28 fields, containing 606 unknown cells. The other 545 events have complete household-rule inputs. Missingness is therefore material, even though the typical per-field rate is small.

Across the frozen 40-case source file, excluding the blank outcome column, there are 287 unknown cells in 21 columns and every case has at least one. That broader scope includes context and income-source fields not used in matching or the household score. Within the 39 matching fields, only 18 cases have unknowns (21 cells); within the 28 household-rule fields, 13 have unknowns (14 cells). The statement that all 40 source cases contain an unrecorded entry must not be read as saying all 40 household scores are incomplete.

The reviewed inputs remain frozen, and removing unknowns from the case-base generator would alter the data design rather than address the observed missingness. Any approved correction must handle existing unknowns explicitly. The proposed shifted score preserves a complete record's raw score, but recalibration can change standardized scores and generated amounts for complete records as well. It does not follow that every amount must change, because rounding and bounds may preserve some. A corrected-data run would be a new, prospectively approved version with these reasons disclosed, while every prior run remains retained. No such run is included here.

'''
    marker='## 4.5 Separate-set'
    assert md.count(marker)==1
    return md.replace(marker,block+marker)

if __name__=='__main__':
    data=measure()
    print(json.dumps({k:{scope:{x:val for x,val in v.items() if x not in ('unknown_counts','unknown_fields_per_event','nonzero_counts')} for scope,v in item.items() if isinstance(v,dict)} for k,item in data.items()},indent=2))
