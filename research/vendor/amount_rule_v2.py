# -*- coding: utf-8 -*-
"""
AICS amount generating rule, version 3, 18 October 2026.

amount = base_share(purpose) x adjustment(household) x noise  x documented_cost

Base shares are DSWD's own published Region XI figures (Process Evaluation of the
AICS, DSWD PDPB 2022). The household adjustment and the noise are the researchers'
choice and are declared as such.

Reproducible: fixed seed, no hidden state.

WHAT CHANGED FROM VERSION 1 (three bugs, all found in external review 18 October)
---------------------------------------------------------------------------------
1. The household score used to be standardised over whatever rows were passed in.
   Running the forty test cases alone and the thousand-row case base alone therefore
   put them on two different scales, and the same case got two different amounts.
   The scale (mu and sd) is now computed once from the case base and carried, and
   it is written to a small JSON file so the same scale is reused every time.
   See calibrate() and generate(..., calib=).

2. The noise seed used every column except case_id and amount_granted. The thousand
   row file also carries event_id, control_no and date_received, which differ between
   two otherwise identical cases, so the duplicate pairs would have received different
   noise there even though they match on every real field. The seed now skips every
   identifier and date column, by an explicit list plus a pattern.
   See SEED_EXCLUDE and seed_payload().

3. Cash relief assistance had no maximum in the code, although the published Region XI
   average for it (P4,400) sits below its P10,000 schedule cap, which is the rule the
   spec states for when a ceiling applies. It now has one.
   See CEILING.

WHAT CHANGED IN VERSION 3
-------------------------
A fourth issue was raised in the same review: the rule used no money field at all, so
the money scaling comparison in Section 3.2.2 of the manuscript had nothing it could
find. Settled, and implemented here. The rule now also adds points for a lower total
income in the past six months, in BANDS rather than as a straight line or a logarithm.

Bands, not a line and not a log, on purpose. Whatever shape goes into the rule, the
scaling option matching that shape wins, so a linear term would hand the result to plain
range scaling and a log term would hand it to log scaling. A band matches none of the
three exactly. Fuzzy membership is closest in kind, which the manuscript states openly
along with how far the fuzzy break points sit from the band edges.

The band edges are published, not ours: see INCOME_BANDS below.
"""
import csv, hashlib, json, math, random, re, statistics, sys

SEED = 20261014
TOTAL_LOG_SD = 0.25          # total spread of log(share), held fixed across conditions
ROUND_TO = 50                # pesos

# ---------------------------------------------------------------- base shares
# received / cost, Region XI rows.  Tables 29, 31, 32, 33 (pp. 41-42).
BASE_SHARE = {
    'Hospital bill':                      (0.2075, 'Table 29 p.41 hospitalization 30,574.07/147,375.00'),
    'Medicines':                          (0.8046, 'Table 29 p.41 medicine 6,301.63/7,831.71'),
    'Assistive device':                   (0.3556, 'BORROWED from Table 29 dialysis/chemo 8,228.57/23,142.86; '
                                                   'Table 30 prints no cost column and no Region XI row'),
    'Funeral expenses':                   (0.2903, 'Table 31 p.41 13,129.63/45,230.74'),
    'Cadaver transfer':                   (0.2903, 'Table 31 p.41, same row as funeral expenses'),
    'Allowance':                          (0.6105, 'Table 32 p.42 7,142.86/11,700.00 against tuition'),
    'School fees':                        (0.6105, 'Table 32 p.42'),
    'School supplies':                    (0.6105, 'Table 32 p.42'),
    'Transportation to home province':    (1.0000, 'ASSUMPTION. Table 2 p.16 sets transportation at actual '
                                                   'ticket cost. Table 34 has no Region XI row.'),
    'Transportation for medical treatment':(1.0000,'ASSUMPTION, as above'),
}
# types with no documented cost: the amount is generated directly
BASE_AMOUNT = {
    'Food subsidy': (3857.14, 'Table 33 p.42 Region XI food assistance received'),
    'Other needs':  (4400.00, 'Table 33 p.42 Region XI cash assistance received'),
}
# transportation carries no household adjustment: the guideline is the actual cost,
# so there is nothing for the household to move and nothing for retrieval to find.
NO_ADJUSTMENT = {'Transportation to home province', 'Transportation for medical treatment'}

# ------------------------------------------------- household adjustment weights
# Chosen to match DSWD's own recommendation (p.70): the amount should reflect needs,
# vulnerability, the money situation, and health / income / spending shocks.
# Positive raises the share, negative lowers it.  These are OURS, not published.
W = {
    'no_emergency_fund':        +1.0,
    'no_savings':               +0.8,
    'no_insurance':             +0.8,
    'per_support_system':       -0.35,   # x count of supports available (0 to 5)
    'vuln_special_care':        +0.7,
    'vuln_incapacitated':       +0.7,
    'vuln_unstable_employment': +0.6,
    'per_crisis_flag':          +0.30,   # x count of the six crisis flags set
    'sub_no_regular_income':    +0.8,
    'sub_4ps':                  +0.5,
    'nobody_employed':          +0.6,
    'philhealth':               -0.6,
    'health_card':              -0.5,
    'guarantee_letter_other':   -0.7,
    'per_discount':             -0.30,   # x count of MSS / senior citizen / PWD
    'sought_income':            -0.4,
    'reached_agencies':         -0.4,
    # The income band term. Band 3, at or above the poverty threshold, adds nothing.
    'income_below_food':        +1.0,
    'income_food_to_poverty':   +0.5,
}

# ------------------------------------------------------------- income bands
# PUBLISHED, not ours. Philippine Statistics Authority Regional Statistical Services
# Office XI (2024), 2023 Poverty Statistics of Davao Region, Special Release No.
# SR-24RSSO11-0030, released 25 October 2024.
#   Poverty threshold, family of five: P157,607 a year (printed; NOT 13,134 x 12).
#   Food threshold,    family of five: P110,323 a year.
# The intake sheet records income over six months, so each annual figure is halved.
# Halving the printed annual figure avoids carrying the rounding in the monthly one.
#
# Four assumptions, all stated in Section 3.2.1 of the manuscript:
#   1. No household size field on the sheet, so PSA's family of five is assumed.
#   2. Six months of income is compared with half the published annual threshold.
#   3. 2023 thresholds are applied to records dated August 2025 to August 2026.
#   4. The thresholds cover Davao Region as a whole, not Davao City.
POVERTY_6M = 157607 / 2      # 78,803.50
FOOD_6M    = 110323 / 2      # 55,161.50
INCOME_FIELD = 'Total income in the past 6 months'
# Deliberately given NO weight, so the weight-learning experiment has something to find.
# If learned weights beat equal weights, it should be because they down-weighted these.
DECOYS = ['client_type', 'referral_type', 'service_setting', 'disability_type', 'occupation']

# ---------------------------------------------------------------------------
# WHICH MONEY FIELDS THE RULE USES, and why.
#
# Used:     total income in the past six months, in bands. Table 3.1 marks it as a
#           compared field, so the distance can see the pattern the rule plants.
# Not used: combined family income and the seven income source lines, because
#           Table 3.1 keeps them as context and the distance never sees them.
# Not used: the documented cost, same reason. It multiplies the share at the end,
#           but it is not part of the household score.
# Not used: monthly family expenses, although it IS a compared field. High expenses
#           can mean a struggling household or a comfortable one, so the direction
#           is not defensible. It therefore stays a decoy the weight search should
#           learn to ignore, alongside the five in DECOYS.
# ---------------------------------------------------------------------------

# ------------------------------------------------------------------- schedule
FLOOR   = {'Funeral': 5000, 'Cash Relief Assistance': 1000, 'Food Assistance': 1000,
           'Educational': 500, 'Medical': 1000}
# Ceilings are applied only where DSWD's own Region XI average sits below the cap.
# Educational (7,142.86 vs 5,000) and Food (3,857.14 vs 3,000) exceed their own maxima
# in the published data, so clipping there would contradict the evidence.
# Cash relief (4,400 vs 10,000) sits below its cap, so the cap applies. [fix 3]
CEILING = {'Funeral': 25000,
           'Cash Relief Assistance': 10000,
           'Medical:Hospital bill': 150000,
           'Medical:Medicines': 10000,
           'Medical:Assistive device': 150000}

# ------------------------------------------------------------ noise seed fields
# Columns that must never reach the noise seed. Two cases that are identical on every
# real field still differ on these, and if they reached the seed the duplicate pairs
# would get different amounts. [fix 2]
SEED_EXCLUDE = {
    'case_id', 'amount_granted', 'event_id', 'control_no', 'client_id', 'record_id',
    'row_id', 'row', 'index', 'seq', 'sequence', 'date_received', 'date', 'month',
    'year', 'month_year', 'date_of_assistance', 'created_at', 'updated_at',
}
SEED_EXCLUDE_PATTERN = re.compile(r'(^|_)(id|uuid|no|num)$|date|timestamp', re.I)


def seed_fields(fieldnames):
    """The columns the noise seed is allowed to read, in a fixed order.
    Everything excluded is printed by main() so the exclusion is never silent."""
    keep, drop = [], []
    for k in sorted(fieldnames):
        name = (k or '').strip()
        low = name.lower().replace(' ', '_').replace('/', '_')
        if low in SEED_EXCLUDE or SEED_EXCLUDE_PATTERN.search(low):
            drop.append(name)
        else:
            keep.append(name)
    return keep, drop


def seed_payload(r, keep):
    return '|'.join(f'{k}={r.get(k, "")}' for k in keep)


def yes(v): return str(v).strip().lower() == 'yes'


def num(v):
    try: return int(str(v).replace('₱', '').replace(',', '').strip())
    except Exception: return 0


def num_strict(v):
    """Returns None when the value is missing or unreadable, instead of 0.
    Income needs this: a recorded income of zero is real and must not be confused
    with a blank, since the two would land in different bands."""
    s = str(v if v is not None else '').replace('₱', '').replace(',', '').strip()
    if s == '' or s.lower() in ('(not recorded)', 'not recorded', 'n/a', 'na', 'none'):
        return None
    try: return int(float(s))
    except Exception: return None


def income_band_points(r):
    """Points from the income band. Band 3, at or above the poverty threshold, adds
    nothing. A missing income adds nothing either, and is counted by main()."""
    if INCOME_FIELD not in r:
        raise KeyError(f'{INCOME_FIELD!r} is not a column in this file. The rule needs '
                       'it. Add it to the generator before running.')
    inc = num_strict(r[INCOME_FIELD])
    if inc is None:               return 0.0, 'missing'
    if inc < FOOD_6M:             return W['income_below_food'], 'band1'
    if inc < POVERTY_6M:          return W['income_food_to_poverty'], 'band2'
    return 0.0, 'band3'


def peso(s):
    m = re.search(r'₱([\d,]+)', s or '')
    return int(m.group(1).replace(',', '')) if m else None


def documented_cost(row):
    """The balance the client still owes, as the sheet prints it."""
    dc = row.get('Documented cost', '') or ''
    if dc.startswith('none'): return None
    m = re.search(r'₱([\d,]+)\s*balance after PhilHealth', dc)
    if m:                                       # the balance owing, not the gross bill
        return int(m.group(1).replace(',', ''))
    return peso(dc)


def raw_score(r):
    s  = 0.0
    s += W['no_emergency_fund']        * (0 if yes(r['Availability of emergency fund']) else 1)
    s += W['no_savings']               * (0 if yes(r['Savings']) else 1)
    s += W['no_insurance']             * (0 if yes(r['Insurance coverage']) else 1)
    sup = sum(yes(r[k]) for k in ('Family', 'Relatives', 'Friend/s', 'Employer',
                                  'Church / Community Organization'))
    s += W['per_support_system']       * sup
    s += W['vuln_special_care']        * yes(r['There are elderly / child in need / PWD / pregnant in the household'])
    s += W['vuln_incapacitated']       * yes(r['A member is physically or mentally incapacitated to work'])
    s += W['vuln_unstable_employment'] * yes(r['Inability to secure stable employment'])
    cr = sum(yes(r[k]) for k in ('Hospitalization', 'Death of a family member', 'Catastrophic event',
                                 'Disablement', 'Loss of livelihood', 'Others'))
    s += W['per_crisis_flag']          * cr
    sub = (r.get('Specify Sub-Category') or '')
    s += W['sub_no_regular_income']    * ('No Regular Income' in sub)
    s += W['sub_4ps']                  * ('4Ps' in sub)
    s += W['nobody_employed']          * (num(r['Employed\n number of members working']
                                              if 'Employed\n number of members working' in r
                                              else r.get('Employed, number of members working', 0)) == 0)
    s += W['philhealth']               * yes(r['Philhealth'])
    s += W['health_card']              * yes(r['Health Card'])
    s += W['guarantee_letter_other']   * yes(r['Guarantee Letter from other agencies'])
    dis = sum(yes(r[k]) for k in ('MSS Discount', 'Senior Citizen Discount', 'PWD Discount'))
    s += W['per_discount']             * dis
    s += W['sought_income']            * yes(r['Successfully sought employment opportunities or explored additional income sources'])
    s += W['reached_agencies']         * yes(r['Successfully reached out to relevant organizations or agencies for financial assistance or support'])
    s += income_band_points(r)[0]
    return s


# ------------------------------------------------------------------ the scale
def calibrate(rows):
    """Compute the household score scale ONCE, from the case base. [fix 1]

    Both the thousand-row case base and the forty test cases must be generated using
    this same mu and sd, or the same household lands on a different z and gets a
    different amount depending on which file it was run in."""
    vals = [raw_score(r) for r in rows]
    return {'mu': statistics.mean(vals),
            'sd': statistics.pstdev(vals) or 1.0,
            'n': len(vals)}


def generate(rows, p_explained, seed=SEED, calib=None, seed_keep=None):
    """p_explained: share of the spread in log(share) owed to the household.
       p = 0 is the null control: the amounts carry no household signal at all.
       calib: the {'mu','sd'} from calibrate() on the CASE BASE. Required in real use.
              If omitted, it is computed from these rows and a warning is printed,
              which is only safe when these rows are the whole case base."""
    if calib is None:
        calib = calibrate(rows)
        print('WARNING: no calibration passed, scale taken from these rows only. '
              'Amounts will not match a run over the full case base.', file=sys.stderr)
    mu, sd = calib['mu'], calib['sd']

    if seed_keep is None:
        seed_keep, _ = seed_fields(rows[0].keys())

    raw = {r['case_id']: raw_score(r) for r in rows}

    def case_rng(r):
        """Noise seeded from the case's own field values, never from row order, and
        never from an identifier or a date. Two identical case pages therefore get
        identical noise, which is what the duplicate-pair design requires."""
        h = hashlib.sha256(
            f'{seed}|{p_explained}|{seed_payload(r, seed_keep)}'.encode('utf-8')).hexdigest()
        return random.Random(int(h[:16], 16))

    a     = TOTAL_LOG_SD * math.sqrt(p_explained)
    sigma = TOTAL_LOG_SD * math.sqrt(1 - p_explained)

    out = []
    for r in rows:
        purpose, atype = r['Purpose of assistance'], r['Type']
        z = (raw[r['case_id']] - mu) / sd
        shift = 0.0 if purpose in NO_ADJUSTMENT else a * z
        eps   = 0.0 if purpose in NO_ADJUSTMENT else case_rng(r).gauss(0, sigma)
        factor = math.exp(shift + eps)

        cost = documented_cost(r)
        if purpose in BASE_AMOUNT:
            base, src = BASE_AMOUNT[purpose]
            amount, share = base * factor, None
        else:
            base, src = BASE_SHARE[purpose]
            share  = min(base * factor, 1.0)     # cannot cover more than the documented cost
            amount = share * cost

        key = f"{atype}:{purpose}"
        cap   = CEILING.get(key, CEILING.get(atype))
        floor = FLOOR.get(atype)
        pre = amount
        if floor and amount < floor: amount = floor
        if cap   and amount > cap:   amount = cap
        amount = int(round(amount / ROUND_TO) * ROUND_TO)

        out.append({'case_id': r['case_id'], 'type': atype, 'purpose': purpose,
                    'documented_cost': cost, 'household_z': round(z, 3),
                    'share': round(share, 4) if share is not None else '',
                    'amount_granted': amount,
                    'floor_bound': bool(floor and pre < floor),
                    'cap_bound':   bool(cap and pre > cap),
                    'base_source': src})
    return out


# ------------------------------------------------------------------- the check
PAIRS = [('J01', 'J22'), ('J28', 'J13'), ('J11', 'J30'), ('J20', 'J35')]


def check_pairs(res, pairs=PAIRS):
    """Duplicate pairs must receive identical amounts. Run this every time."""
    by = {x['case_id']: x['amount_granted'] for x in res}
    bad = [(a, b, by[a], by[b]) for a, b in pairs
           if a in by and b in by and by[a] != by[b]]
    return bad


if __name__ == '__main__':
    rows = list(csv.DictReader(open(sys.argv[1], encoding='utf-8-sig')))
    base = rows
    if len(sys.argv) > 2:                    # optional: the case base to calibrate on
        base = list(csv.DictReader(open(sys.argv[2], encoding='utf-8-sig')))
    calib = calibrate(base)
    json.dump(calib, open('calibration.json', 'w'), indent=2)

    keep, drop = seed_fields(rows[0].keys())
    print(f"scale from {calib['n']} rows: mu={calib['mu']:.4f} sd={calib['sd']:.4f}")
    print(f"noise seed reads {len(keep)} columns, skips {len(drop)}: {drop}")

    bands = {}
    for r in rows:
        b = income_band_points(r)[1]
        bands[b] = bands.get(b, 0) + 1
    print(f"income bands (edges {FOOD_6M:,.2f} and {POVERTY_6M:,.2f}): "
          + '  '.join(f'{k}={v}' for k, v in sorted(bands.items())))
    if bands.get('missing'):
        print(f"  NOTE: {bands['missing']} rows have no readable income and score zero "
              "for this term. Report this figure if it is not zero.")

    for p in (0.00, 0.25, 0.50, 0.75):
        res = generate(rows, p, calib=calib, seed_keep=keep)
        with open(f'amounts_p{int(p*100):02d}.csv', 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=list(res[0].keys())); w.writeheader(); w.writerows(res)
        amts = [x['amount_granted'] for x in res]
        bad = check_pairs(res)
        print(f"p={p:.2f}  n={len(res)}  min={min(amts):>7,}  median={int(statistics.median(amts)):>7,}  "
              f"max={max(amts):>8,}  floor_bound={sum(x['floor_bound'] for x in res)}  "
              f"cap_bound={sum(x['cap_bound'] for x in res)}  "
              f"pairs={'OK' if not bad else 'BROKEN ' + str(bad)}")
