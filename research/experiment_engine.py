"""Offline vectorized Gower experiments. No amount-rule inputs enter distances."""
from dataclasses import dataclass
import math
import random
import numpy as np

from backend.study_schema import MATCHING_FIELDS, NUMERIC_FIELDS, MULTI_FIELDS, ASYMMETRIC_FIELDS
from research.evaluate import width, PARTNERS

FIELDS = tuple(MATCHING_FIELDS)
MONEY = {'monthly_expenses','total_income_past_6_months'}
RANK = {'Recently diagnosed (3 months and below)':0., 'Three months to a year':.5, 'Chronic, lifelong':1.}


def membership(x, q):
    q1,q2,q3 = q
    low=np.clip((q2-x)/(q2-q1),0,1)
    high=np.clip((x-q2)/(q3-q2),0,1)
    return np.stack([low,1-low-high,high],axis=-1)


def paired_test(base, challenger):
    """Two-sided asymptotic Wilcoxon, zero removal, midranks, tie-corrected variance."""
    d=np.asarray(base)-np.asarray(challenger)
    d=d[d!=0]
    if not len(d): return dict(p=1.,n=0,z=0.,positive_rank_sum=0.)
    _,inv,counts=np.unique(abs(d),return_inverse=True,return_counts=True)
    ends=np.cumsum(counts)
    ranks=(ends-(counts-1)/2)[inv]
    plus=float(ranks[d>0].sum())
    n=len(d)
    variance=(n*(n+1)*(2*n+1)-float(sum(counts**3-counts))/2)/24
    z=(plus-n*(n+1)/4)/math.sqrt(variance)
    return dict(p=math.erfc(abs(z)/math.sqrt(2)),n=n,z=z,positive_rank_sum=plus)


@dataclass
class Block:
    queries: list
    references: list
    scores: np.ndarray
    masks: np.ndarray
    eligible: np.ndarray
    metadata: list

    def sums(self, weights):
        return (np.einsum('f,fqr->qr',weights,self.scores,optimize=False),
                np.einsum('f,fqr->qr',weights,self.masks,optimize=False))

    def neighbors(self, num, den, k):
        distance=np.full(num.shape,np.inf)
        np.divide(num,den,out=distance,where=den>0)
        distance=np.where((den>0)&self.eligible,np.clip(1-distance,0,1),np.inf)
        if np.any(np.isfinite(distance).sum(axis=1)<k): raise ValueError('Insufficient defined neighbors')
        threshold=np.partition(distance,k-1,axis=1)[:,k-1,None]
        less=distance<threshold
        tied=distance==threshold
        chosen=less | (tied & (np.cumsum(tied,axis=1) <= k-less.sum(axis=1)[:,None]))
        indices=np.nonzero(chosen)[1].reshape(len(self.queries),k)
        return indices, distance, ((den<=0)&self.eligible).sum(axis=1)


def blocks(queries, references, money='plain', duration='categorical', reviewed=False):
    result=[]
    for typ in sorted({r.values['assistance_type_granted'] for r in queries}):
        qs=[q for q in queries if q.values['assistance_type_granted']==typ]
        rs=sorted([r for r in references if r.values['assistance_type_granted']==typ],
                  key=lambda r:(r.applicant_id,r.event_id or ''))
        eligible=np.array([[r.applicant_id!=q.applicant_id and
            (not reviewed or r.applicant_id!=PARTNERS.get(q.applicant_id)) for r in rs] for q in qs])
        shape=(len(FIELDS),len(qs),len(rs))
        scores=np.zeros(shape,dtype=np.float64)
        masks=np.zeros(shape,dtype=np.float64)
        metadata=[dict(active_fields=[],numeric_ranges={},quartiles={},fallbacks=[]) for _ in qs]
        for f,field in enumerate(FIELDS):
            qvals=[q.values[field] for q in qs]
            rvals=[r.values[field] for r in rs]
            known=np.array([v is not None for v in rvals])
            unique={v:i for i,v in enumerate(dict.fromkeys(v for v in rvals if v is not None))}
            codes=np.array([unique.get(v,-1) for v in rvals])
            allowed=eligible & known[None,:]
            mins=np.where(allowed,codes,np.inf).min(axis=1)
            maxs=np.where(allowed,codes,-np.inf).max(axis=1)
            active=maxs>mins
            valid=allowed & np.array([v is not None for v in qvals])[:,None] & active[:,None]
            if field in ASYMMETRIC_FIELDS:
                valid &= ~(np.array([v is False for v in qvals])[:,None] & np.array([v is False for v in rvals])[None,:])
            for i in np.flatnonzero(active): metadata[i]['active_fields'].append(field)
            if field in NUMERIC_FIELDS:
                qx=np.array([np.nan if v is None else float(v) for v in qvals])
                rx=np.array([np.nan if v is None else float(v) for v in rvals])
                observed=np.where(allowed,rx[None,:],np.nan)
                transformed=np.log1p(observed) if field in MONEY and money=='log' else observed
                # Each row fits scales on its own eligible reference pool.
                for i in range(len(qs)):
                    if not active[i]: continue
                    rng=float(np.nanmax(transformed[i])-np.nanmin(transformed[i]))
                    metadata[i]['numeric_ranges'][field]=rng
                    left=np.log1p(qx[i]) if field in MONEY and money=='log' else qx[i]
                    right=np.log1p(rx) if field in MONEY and money=='log' else rx
                    sim=np.clip(1-abs(left-right)/rng,0,1)
                    if field in MONEY and money=='fuzzy':
                        quartiles=np.nanquantile(observed[i],[.25,.5,.75],method='linear')
                        metadata[i]['quartiles'][field]=quartiles.tolist()
                        if np.all(np.diff(quartiles)>0):
                            sim=1-.5*np.abs(membership(qx[i],quartiles)-membership(rx,quartiles)).sum(axis=-1)
                        else: metadata[i]['fallbacks'].append(field)
                    scores[f,i]=np.nan_to_num(sim)
            elif field in MULTI_FIELDS:
                universe=sorted(set().union(*(v for v in qvals+rvals if v is not None)))
                mapping={v:1<<i for i,v in enumerate(universe)}
                qbits=np.array([sum(mapping[x] for x in (v or [])) for v in qvals],dtype=np.uint64)
                rbits=np.array([sum(mapping[x] for x in (v or [])) for v in rvals],dtype=np.uint64)
                union=np.bitwise_count(qbits[:,None]|rbits[None,:])
                intersection=np.bitwise_count(qbits[:,None]&rbits[None,:])
                scores[f]=np.divide(intersection,union,out=np.ones(union.shape),where=union>0)
            else:
                scores[f]=np.array([[a==b for b in rvals] for a in qvals],dtype=float)
                if field=='illness_duration' and duration=='rank':
                    for i,a in enumerate(qvals):
                        for j,b in enumerate(rvals):
                            if a in RANK and b in RANK: scores[f,i,j]=1-abs(RANK[a]-RANK[b])
            masks[f]=valid
            scores[f]*=valid
        result.append(Block(qs,rs,scores,masks,eligible,metadata))
    return result


class Outcomes:
    def __init__(self, block_list, records):
        self.blocks=block_list
        by={(r.applicant_id,r.event_id):r for r in records}
        self.data=[]
        self.applicants=[]
        for block in block_list:
            qs=[by[(q.applicant_id,q.event_id)] for q in block.queries]
            rs=[by[(r.applicant_id,r.event_id)] for r in block.references]
            direct=qs[0].values['assistance_type_granted'] in {'Food Assistance','Cash Relief Assistance'}
            rcost=np.ones(len(rs)) if direct else np.array([r.values['documented_cost'] for r in rs])
            qcost=np.ones(len(qs)) if direct else np.array([r.values['documented_cost'] for r in qs])
            actual=np.array([q.values['amount_granted'] for q in qs])
            shares=np.array([r.values['amount_granted'] for r in rs])/rcost
            widths=np.array([width(q) or np.nan for q in qs])
            baseline=[]
            for i,q in enumerate(qs):
                same=block.eligible[i]&np.array([r.values['purpose_of_assistance']==q.values['purpose_of_assistance'] for r in rs])
                baseline.append(float(np.median(shares[same])*qcost[i]) if same.any() else np.nan)
            baseline=np.array(baseline)
            self.data.append((shares,qcost,actual,widths,baseline))
            self.applicants.extend(q.applicant_id for q in qs if width(q) is not None)
        self.ids=sorted(set(self.applicants))
        index={a:i for i,a in enumerate(self.ids)}
        self.inverse=np.array([index[a] for a in self.applicants])
        self.counts=np.bincount(self.inverse,minlength=len(self.ids))

    def evaluate(self, sums, k=5, details=False):
        scaled=[]
        rows=[]
        for block,(num,den),(shares,cost,actual,widths,baseline) in zip(self.blocks,sums,self.data):
            ix,dist,undefined=block.neighbors(num,den,k)
            predicted=np.median(shares[ix],axis=1)*cost
            errors=abs(predicted-actual)
            scaled.extend((errors/widths)[np.isfinite(widths)])
            if details:
                if not np.isfinite(baseline).all(): raise ValueError('No eligible same-purpose baseline')
                for i,q in enumerate(block.queries):
                    neighbors=sorted(ix[i],key=lambda j:dist[i,j])
                    rows.append(dict(applicant_id=q.applicant_id,event_id=q.event_id,
                        assistance_type=q.values['assistance_type_granted'],purpose=q.values['purpose_of_assistance'],
                        actual=float(actual[i]),prediction=float(predicted[i]),error=float(errors[i]),
                        scaled_error=float(errors[i]/widths[i]) if np.isfinite(widths[i]) else None,
                        baseline_prediction=float(baseline[i]),baseline_error=float(abs(baseline[i]-actual[i])),
                        baseline_scaled_error=float(abs(baseline[i]-actual[i])/widths[i]) if np.isfinite(widths[i]) else None,
                        neighbors=[[block.references[j].applicant_id,block.references[j].event_id] for j in neighbors],
                        neighbor_compared_field_counts=[int(block.masks[:,i,j].sum()) for j in neighbors],
                        undefined_pairs=int(undefined[i]),eligible_count=int(block.eligible[i].sum()),
                        **block.metadata[i]))
        app=np.bincount(self.inverse,weights=scaled,minlength=len(self.ids))/self.counts
        return float(app.mean()),app,rows


def fit(block_list,outcomes,seed,budget=200):
    rng=random.Random(seed)
    weights=np.ones(len(FIELDS))
    sums=[b.sums(weights) for b in block_list]
    best=outcomes.evaluate(sums)[0]
    trace=[dict(evaluation=0,candidate=best,incumbent=best,weights=weights.tolist(),accepted=True)]
    for iteration in range(1,budget):
        donor,recipient=rng.sample(range(len(FIELDS)),2)
        if weights[donor]==0:
            donor=rng.choice(np.flatnonzero(weights>0).tolist())
            if recipient==donor: recipient=rng.choice([j for j in range(len(FIELDS)) if j!=donor])
        delta=weights[donor]*(.25,.5,1.)[(iteration-1)%3]
        trial=weights.copy();trial[donor]-=delta;trial[recipient]+=delta
        proposed=[(num+delta*(b.scores[recipient]-b.scores[donor]),
                   den+delta*(b.masks[recipient]-b.masks[donor])) for b,(num,den) in zip(block_list,sums)]
        try: objective=outcomes.evaluate(proposed)[0]
        except ValueError: objective=math.inf
        accept=objective<best-1e-12
        if accept: weights,sums,best=trial,proposed,objective
        trace.append(dict(evaluation=iteration,candidate=objective if math.isfinite(objective) else None,
                          incumbent=best,weights=trial.tolist(),accepted=accept))
    return weights,trace
