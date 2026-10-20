"""Input-only eligibility audit; never reads an amount into a calculation."""
from collections import Counter
import random
from backend.study_loader import load_study_csv
from research.reconciled import derived

def audit(data_dir,names=None):
    rows=[]
    for name in names or ['primary']+[str(n) for n in range(51001,51031)]:
        seed=51000 if name=='primary' else int(name)
        records=load_study_csv(data_dir/name/'case_base_p50.csv').records
        ids=sorted({r.applicant_id for r in records})
        random.Random(derived(seed,'fold')).shuffle(ids)
        assignment={a:i%5 for i,a in enumerate(ids)}
        for fold in range(5):
            training=[r for r in records if assignment[r.applicant_id]!=fold]
            sizes=Counter((r.values['assistance_type_granted'],r.values['purpose_of_assistance']) for r in training)
            own=Counter((r.applicant_id,r.values['assistance_type_granted'],r.values['purpose_of_assistance']) for r in training)
            minimum=min(sizes[(r.values['assistance_type_granted'],r.values['purpose_of_assistance'])]-own[(r.applicant_id,r.values['assistance_type_granted'],r.values['purpose_of_assistance'])] for r in training)
            rows.append(dict(dataset=name,fold=fold,minimum_training_purpose_references=minimum))
    failures=[r for r in rows if r['minimum_training_purpose_references']<5]
    return dict(passed=not failures,minimum=min(r['minimum_training_purpose_references'] for r in rows),failures=failures,checks=rows)
