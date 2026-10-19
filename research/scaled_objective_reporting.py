"""Decompose existing held-out errors; no fitting or generation."""
import json
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def diagnose():
    raw=json.loads((ROOT/'research/generated/completed-study-v1/weights/primary/results.json').read_text())['p50']
    out={}
    for method in ['equal','learned']:
        rows=[r for r in raw[method]['events'] if r['scaled_error'] is not None]
        counts=Counter(r['applicant_id'] for r in rows)
        totals=defaultdict(float)
        for r in rows:totals[r['assistance_type']]+=r['scaled_error']/counts[r['applicant_id']]/len(counts)
        assert abs(sum(totals.values())-raw[method]['objective'])<1e-12
        out[method]={'applicants':len(counts),'objective':raw[method]['objective'],'contributions':dict(totals),'shares':{k:100*v/raw[method]['objective'] for k,v in totals.items()}}
    return out

if __name__=='__main__':print(json.dumps(diagnose(),indent=2))

def add_scaled_diagnosis(md):
    if '### Scaled-error contribution and the observed trade-off' in md:return md
    appendix=md.split('## Appendix 4A',1)[1];lookup={}
    for line in appendix.splitlines():
        c=[x.strip() for x in line.strip().strip('|').split('|')]
        if len(c)==9 and c[0]=='p50' and c[7]!='N/A':lookup[(c[1],c[2])]=(int(c[3]),float(c[7].replace(',','')))
    types=['Medical','Food Assistance','Educational','Funeral','Cash Relief Assistance']
    denom=sum(lookup[('equal',t)][0]*lookup[('equal',t)][1] for t in types)
    exact=diagnose()
    rows=[];changes=[]
    for typ in types:
        n,equal=lookup[('equal',typ)];learned=lookup[('learned',typ)][1]
        rows.append(f'| {typ} | {n} | {equal:.6f} | {100*n*equal/denom:.1f} | {exact["equal"]["shares"][typ]:.2f} |')
        changes.append(f'| {typ} | {equal:.6f} | {learned:.6f} | {learned-equal:+.6f} |')
    block='''### Scaled-error contribution and the observed trade-off

The scaled results allow a more direct check of medical's contribution. Multiplying each type's mean scaled error by its applicant count gives the approximate proxy below. Applicants appearing in more than one type are counted in more than one row, so that proxy is not a partition of the actual applicant-averaged objective.

| Type | Applicants in type | Equal scaled error | Overlapping-row proxy share % | Exact held-out objective share % |
| --- | --- | --- | --- | --- |
'''+ '\n'.join(rows)+'''

The exact column is reconstructed from the saved p = .50 held-out event errors, with no retrieval or fitting rerun. For each applicant a, divide each non-transport event error by that applicant's count of non-transport events; then sum those fractions by type and divide by the 794 applicants with a defined scaled error. The contributions sum to the recorded equal-weight objective of 0.167927. Medical contributes 0.072774, or **43.34%**, the largest single block; the overlapping-row approximation is **41.4%**. These are the held-out errors under the fitted folds, not the training objective values evaluated inside each search. The same applicant-averaging convention underlies both, but the eligible reference pools differ.

| Type | Equal scaled error | Learned scaled error | Learned minus equal |
| --- | --- | --- | --- |
'''+ '\n'.join(changes)+'''

Medical has the largest decrease in per-type applicant-averaged scaled error, about 0.0501, roughly 3.1 times the next largest decrease (food, about 0.0163). Educational error instead rises by about 0.0166. The exact objective decomposition likewise assigns the largest reduction to medical: its contribution falls by 0.027421, while education's rises by 0.000915. The shared weights therefore produce an observed trade-off: substantially lower medical error accompanies higher educational error.

This is consistent with purpose being a lever used by the search and medical being where that lever paid off. It describes the outcome of the learned weights; it does not isolate the optimizer's internal reasons, prove that education was deliberately sacrificed, or establish that purpose was its only useful lever. Section 4.8's household-recovery conclusion remains unchanged.

'''
    old='Medical dominates the unscaled peso error under equal weights, but that alone does not establish its influence on the scaled optimization objective.'
    assert old in md
    md=md.replace(old,old+' The scaled-error breakdown below addresses that separate question using the saved errors.')
    return md.replace('## 4.7 Five-fold',block+'## 4.7 Five-fold')
