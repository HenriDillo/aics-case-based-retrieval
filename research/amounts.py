"""Content-seeded synthetic costs and amounts; no retrieval dependency."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
import random
import statistics

from backend.study_schema import MATCHING_FIELDS, NOT_APPLICABLE
from .policy import (AMOUNT_SEED, COST_SEED, COST_RANGES, DIRECT, FLOORS,
                     LOG_SD, ROUND_TO, SETTINGS, SHARES, VERSION)


def content(record):
    """One canonical payload for both source schemas; no IDs/dates/outcomes."""
    payload = {k: record.values[k] for k in MATCHING_FIELDS}
    payload['assistance_type'] = record.values['assistance_type_granted']
    return {k: sorted(v) if isinstance(v, frozenset) else v for k, v in payload.items()}


def rng_for(record, seed, domain, cost=None, p=None):
    payload = dict(seed=seed, domain=domain, fields=content(record), cost=cost, p=p)
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'),
                                       allow_nan=False).encode()).digest()
    return random.Random(int.from_bytes(digest, 'big'))


def income_band(value):
    if value is None:
        return 'missing', 0.
    if value < 55161.5:
        return 'below_food', 1.
    if value < 78803.5:
        return 'food_to_poverty', .5
    return 'at_or_above_poverty', 0.


def household_score(record):
    v = record.values
    # Unknown does not assert poverty, absence or employment. Explicit No only.
    score = sum(weight for key, weight in [('emergency_fund',1.),('savings',.8),
                                          ('insurance_coverage',.8)] if v[key] is False)
    score += sum(weight for key, weight in [
        ('vuln_elderly_child_pwd_pregnant',.7),('vuln_member_incapacitated',.7),
        ('vuln_unstable_employment',.6),('ext_philhealth',-.6),('ext_health_card',-.5),
        ('ext_guarantee_letter_other_agency',-.7),('selfhelp_sought_income',-.4),
        ('selfhelp_reached_agencies',-.4)] if v[key] is True)
    for prefix, weight in [('support_',-.35),('crisis_',.30)]:
        score += weight * sum(value is True for key, value in v.items()
                              if key.startswith(prefix) and key != 'crisis_last_3_months')
    score -= .3 * sum(v[k] is True for k in
                     ['ext_mss_discount','ext_senior_citizen_discount','ext_pwd_discount'])
    categories = v['sub_category'] or frozenset()
    score += .8 * ('No Regular Income' in categories) + .5 * ('4Ps Beneficiary' in categories)
    score += .6 * (v['employed_members'] == 0)
    return score + income_band(v['total_income_past_6_months'])[1]


def calibrate(records):
    if not records:
        raise ValueError('Calibration requires a nonempty case base')
    scores = [household_score(r) for r in records]
    return dict(mu=statistics.mean(scores), sd=statistics.pstdev(scores) or 1.,
                n=len(records), weighting='one score per event', version=VERSION)


def repair_wage_labels(records):
    """Conservative consistency repair: never invent employment or change income."""
    prepared, changes, unresolved = deepcopy(records), [], []
    for r in prepared:
        v = r.values
        labels = v['sub_category']
        if not labels or not any('Wage Earner' in x for x in labels):
            continue
        employed, seasonal = v['employed_members'], v['seasonal_members']
        if employed == 0 and seasonal == 0:
            new = frozenset(x for x in labels if 'Wage Earner' not in x)
            changes.append(dict(case_id=r.applicant_id,event_id=r.event_id,
                                before=sorted(labels),after=sorted(new)))
            v['sub_category'] = new
        elif (employed is None and not seasonal) or (seasonal is None and not employed):
            unresolved.append(dict(case_id=r.applicant_id,event_id=r.event_id,
                                   reason='Wage label cannot be verified with missing worker count'))
    return prepared, changes, unresolved


def validate_purpose(record):
    p, t = record.values['purpose_of_assistance'], record.values['assistance_type_granted']
    spec = SHARES.get(p) or DIRECT.get(p)
    if spec is None or spec[0] != t:
        raise ValueError(f'Unsupported assistance type/purpose: {t}/{p}')


def assign_costs(records, seed=COST_SEED):
    """One allowed correction of published-mean cost ranges, before amounts."""
    output = deepcopy(records)
    ranges = dict(COST_RANGES)
    adjustments = []
    def cost(r):
        purpose = r.values['purpose_of_assistance']
        low, high = ranges[purpose]
        return int(round(rng_for(r,seed,'cost').uniform(low,high) / ROUND_TO) * ROUND_TO)
    for r in output:
        validate_purpose(r)
        r.values['documented_cost'] = (NOT_APPLICABLE if r.values['purpose_of_assistance'] in DIRECT else cost(r))
    # Medical benchmarks per purpose; funeral and educational checked per type.
    groups = {}
    for r in output:
        purpose, atype = r.values['purpose_of_assistance'], r.values['assistance_type_granted']
        if purpose not in SHARES or SHARES[purpose][2] is None:
            continue
        key = purpose if atype == 'Medical' else atype
        groups.setdefault(key, []).append(r)
    checks = []
    for key, group in groups.items():
        target = SHARES[group[0].values['purpose_of_assistance']][2]
        before = statistics.mean(r.values['documented_cost'] for r in group)
        if abs(before-target)/target > .20:
            factor = target/before
            purposes = {r.values['purpose_of_assistance'] for r in group}
            for purpose in sorted(purposes):
                old = ranges[purpose]
                ranges[purpose] = tuple(x*factor for x in old)
                adjustments.append(dict(purpose=purpose,old=list(old),new=list(ranges[purpose])))
            for r in group:
                r.values['documented_cost'] = cost(r)
        after = statistics.mean(r.values['documented_cost'] for r in group)
        checks.append(dict(group=key,n=len(group),published_mean_cost=target,
                           initial_mean=before,final_mean=after,
                           relative_difference=(after-target)/target,
                           within_20_percent=abs(after-target)/target <= .20))
    return output, dict(checks=checks,range_adjustments=adjustments,
                        final_ranges={k:list(v) for k,v in ranges.items()})


def generate(records, p, *, calibration, seed=AMOUNT_SEED):
    if p not in SETTINGS:
        raise ValueError('Unsupported amount condition')
    mu, sd = calibration['mu'], calibration['sd']
    if not all(math.isfinite(x) for x in (mu, sd)) or sd <= 0:
        raise ValueError('Invalid calibration')
    output, diagnostics = deepcopy(records), []
    for r in output:
        validate_purpose(r)
        purpose, atype = r.values['purpose_of_assistance'], r.values['assistance_type_granted']
        cost = r.values.get('documented_cost')
        direct = purpose in DIRECT
        if not direct and (isinstance(cost,bool) or not isinstance(cost,(int,float)) or
                           not math.isfinite(cost) or cost <= 0):
            raise ValueError('A cost-based event requires a finite positive cost')
        floor = FLOORS.get(atype,0)
        if not direct and cost < floor:
            raise ValueError('Documented cost below floor: constraints cannot both hold')
        z = (household_score(r)-mu)/sd  # per event, never indexed by applicant alone
        if atype == 'Transportation':
            if cost % ROUND_TO:
                raise ValueError('Ticket cost must be a multiple of 50 to satisfy exact-cost and rounding rules')
            raw, amount, cap = cost, cost, None
        else:
            eps = rng_for(r,seed,'amount',None if direct else cost,p).gauss(0,LOG_SD*math.sqrt(1-p))
            factor = math.exp(LOG_SD*math.sqrt(p)*z+eps)
            if direct:
                _, base, cap = DIRECT[purpose]
                raw = base*factor
            else:
                _, base, _, cap = SHARES[purpose]
                raw = min(base*factor,1.)*cost
            upper = min([x for x in [cap,None if direct else cost] if x is not None], default=math.inf)
            lower_grid = math.ceil(floor/ROUND_TO)*ROUND_TO
            upper_grid = math.floor(upper/ROUND_TO)*ROUND_TO if math.isfinite(upper) else math.inf
            if lower_grid > upper_grid:
                raise ValueError('No rounded amount can satisfy floor and cost/ceiling')
            amount = min(upper_grid,max(lower_grid,round(raw/ROUND_TO)*ROUND_TO))
        r.values['amount_granted'] = int(amount)
        diagnostics.append(dict(case_id=r.applicant_id,event_id=r.event_id,
            household_score=household_score(r),household_z=z,unrounded_amount=raw,
            realized_share=None if direct else amount/cost,
            floor_bound=raw<floor,ceiling_bound=cap is not None and raw>cap))
    return output, diagnostics
