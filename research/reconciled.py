"""Versioned source-compatible generation. Never overwrites an existing run."""
import argparse
from copy import deepcopy
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import sys

from backend.study_loader import load_study_csv
from backend.study_schema import PRINTED_TO_CANONICAL, NOT_APPLICABLE
from research.amounts import assign_costs, repair_wage_labels
from research.build_dataset import write_csv, write_json, pair_report, validate_amounts, summarize
from research.policy import SHARES, DIRECT, SETTINGS, FLOORS
from research.validate_intake import validate

ROOT = Path(__file__).resolve().parents[1]
VENDOR = Path(__file__).parent/'vendor'


def module(name):
    spec = importlib.util.spec_from_file_location(name, VENDOR/f'{name}.py')
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


rule = module('amount_rule_v2')
for purpose in ('Laboratory', 'Dialysis', 'Chemotherapy'):
    rule.BASE_SHARE[purpose] = (SHARES[purpose][1], 'Published Table 29; shared dialysis/chemo proxy declared')
    rule.CEILING[f'Medical:{purpose}'] = SHARES[purpose][3]


def derived(master, domain, index=0):
    return int(hashlib.sha256(f'aics-v25-review-1|{master}|{domain}|{index}'.encode()).hexdigest()[:16], 16)


def printed(record):
    if record.source == 'printed_v11':
        return dict(record.raw)
    row = {}
    for label, key in PRINTED_TO_CANONICAL.items():
        value = record.values.get(key)
        if key == 'case_id': value = record.applicant_id
        if key == 'funds_available': value = 250000
        if key == 'amount_granted': value = None
        if key == 'no_income_recorded': value = record.values.get('total_income_past_6_months') == 0
        if value is None: text = ''
        elif isinstance(value, bool): text = 'Yes' if value else 'No'
        elif isinstance(value, frozenset): text = ', '.join(sorted(value)) or 'not_applicable'
        elif key == 'documented_cost':
            text = 'none presented for this type of request' if value == NOT_APPLICABLE else f'₱{value:,.0f}'
        elif isinstance(value, (int,float)): text = str(int(value))
        else: text = str(value)
        row[label] = text
    return row


def amounts(records, p, calibration, seed=20261014):
    result = deepcopy(records)
    diagnostics = []
    for record in result:
        # One record at a time fixes the source's applicant-keyed score overwrite.
        generated = rule.generate([printed(record)], float(p), seed=seed, calib=calibration)[0]
        v = record.values
        typ, purpose = v['assistance_type_granted'], v['purpose_of_assistance']
        floor = FLOORS.get(typ, 0)
        cap = DIRECT[purpose][2] if purpose in DIRECT else SHARES[purpose][3]
        cost = None if purpose in DIRECT else v['documented_cost']
        upper = min([n for n in (cost,cap) if n is not None], default=math.inf)
        low_grid = math.ceil(floor/50)*50
        high_grid = math.floor(upper/50)*50 if math.isfinite(upper) else upper
        if low_grid > high_grid: raise ValueError('Infeasible floor/cost constraint')
        v['amount_granted'] = int(min(high_grid, max(low_grid, generated['amount_granted'])))
        if typ == 'Transportation' and v['amount_granted'] != cost:
            raise ValueError('Ticket cost must be exactly representable')
        diagnostics.append(generated)
    assert not validate_amounts(result)
    return result, diagnostics


def intake(output, seed, count=1000):
    """Retain supplied generator distributions; prevent wage contradictions before blanks."""
    figures = module('dswd_figures')
    generator = module('generate_intake')
    figures.RANDOM_SEED = seed
    if count != 1000:
        if count < 100: raise ValueError('Smoke fixture requires at least 100 events')
        sizes = {k: int(v*count/1000) for k,v in figures.TYPE_COUNTS.items()}
        sizes['Medical'] += count-sum(sizes.values())
        figures.TYPE_COUNTS = sizes
    original = generator.build
    fixes = []
    def build(*args, **kwargs):
        row = original(*args, **kwargs)
        if int(row['employed_members']) + int(row['seasonal_members']) == 0:
            labels = row['sub_category'].split('|')
            new = [s for s in labels if 'Wage Earner' not in s]
            if new != labels:
                fixes.append([row['case_id'], row['event_id']])
                row['sub_category'] = '|'.join(new) or NOT_APPLICABLE
        return row
    generator.build = build
    generator.OUT_DIR = Path(output)
    generator.main()
    records = load_study_csv(Path(output)/'v1_intake.csv').records
    checked = validate(records)
    assert not checked['violations']
    write_json(Path(output)/'wage-generation-check.json', dict(corrected_before_missingness=fixes, validation=checked))
    return records


def build(output, master=None, count=1000):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    if master is None:
        raw = load_study_csv(ROOT/'backend/data/study_intake.csv').records
        base, fixes, unknown = repair_wage_labels(raw)
        cost_seed, amount_seed = 20261019, 20261014
    else:
        base = intake(output/'intake', derived(master,'intake'), count)
        fixes, unknown = [], validate(base)['unverifiable']
        cost_seed, amount_seed = derived(master,'cost'), derived(master,'amount')
    base, costs = assign_costs(base, seed=cost_seed)
    calibration = rule.calibrate([printed(r) for r in base])
    judged = load_study_csv(ROOT/'research/inputs/judged_cases_v11.csv').records
    checks = {}
    for p in SETTINGS:
        tag = f'p{round(p*100):02d}'
        b, bd = amounts(base,p,calibration,amount_seed)
        j, jd = amounts(judged,p,calibration,amount_seed)
        pairs = pair_report(j)
        assert all(x['identical_content'] and x['equal_amount'] for x in pairs['exact'])
        assert all(x['differing_fields'] == [x['expected_field']] for x in pairs['near'])
        for name, records in [('case_base',b),('judged',j)]:
            write_csv(output/f'{name}_{tag}.csv',records)
            assert [r.values for r in load_study_csv(output/f'{name}_{tag}.csv').records] == [r.values for r in records]
        checks[tag] = dict(pairs=pairs,case_base_summary=summarize(b),judged_summary=summarize(j))
    write_json(output/'calibration.json',calibration)
    write_json(output/'cost_checks.json',costs)
    write_json(output/'validation.json',checks)
    write_json(output/'manifest.json',dict(version='v25-reconciled-1',master_seed=master,
        cost_seed=cost_seed,amount_seed=amount_seed,events=len(base),applicants=len({r.applicant_id for r in base}),
        existing_wage_repairs=fixes,unverifiable_wage=unknown,
        missingness=load_study_csv(output/'case_base_p50.csv').report,
        hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob('*.csv')},
        contract_sha256=hashlib.sha256((ROOT/'research/RECONCILIATION.md').read_bytes()).hexdigest()))
    return output


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--master',type=int)
    parser.add_argument('--count',type=int,default=1000)
    args=parser.parse_args()
    print(build(args.output,args.master,args.count))
