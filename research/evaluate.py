"""Offline, fixed equal-weight evaluation. Never imports the amount generator.

Run python -m research.evaluate --input research/generated/v26 --output PATH.
Outputs contain synthetic case identifiers and are research artifacts only.
"""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median

from backend.study_loader import load_study_csv
from backend.study_retrieval import retrieve

PAIRS = (('J01', 'J22'), ('J28', 'J13'), ('J11', 'J30'), ('J20', 'J35'),
         ('J14', 'J37'), ('J04', 'J24'), ('J27', 'J03'), ('J17', 'J33'))
PARTNERS = {a: b for pair in PAIRS for a, b in (pair, pair[::-1])}
DIRECT = {'Food Assistance', 'Cash Relief Assistance'}
PROTOCOL = {
    'version': 'equal-weight-evaluation-1', 'k': 5,
    'distance': 'equal-weight Gower; plain range; categorical duration',
    'holdout': 'all events of applicant; reviewed pair partner also excluded',
    'baseline': 'same type and intake purpose, same applicant exclusions',
    'prediction': 'median recorded share times query cost; direct median for food/cash',
    'main_test': 'p50, 36 reviewed non-transport events, pooled peso MAE reduction >=20%',
    'missing_or_insufficient': 'fail explicitly; no fallback or dropped queries',
    'inference': 'one generated dataset; descriptive; no challenger significance claim',
}


def number(record, field, positive=False):
    value = record.values.get(field)
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0 or (positive and value == 0)):
        raise ValueError(f'{record.applicant_id}: invalid {field}')
    return value


def predict(query, references):
    if not references:
        raise ValueError('Empty reference pool')
    if any(r.values['assistance_type_granted'] != query.values['assistance_type_granted']
           for r in references):
        raise ValueError('Mixed assistance types')
    amounts = [number(r, 'amount_granted') for r in references]
    if query.values['assistance_type_granted'] in DIRECT:
        return median(amounts)
    shares = [a / number(r, 'documented_cost', positive=True)
              for a, r in zip(amounts, references)]
    return median(shares) * number(query, 'documented_cost', positive=True)


def width(query):
    assistance = query.values['assistance_type_granted']
    if assistance == 'Transportation':
        return None
    if assistance == 'Medical':
        return 10000 if query.values['purpose_of_assistance'] in {'Medicines', 'Laboratory'} else 149000
    return {'Funeral': 20000, 'Educational': 4500,
            'Food Assistance': 2000, 'Cash Relief Assistance': 9000}[assistance]


def evaluate_case(query, case_base, reviewed=False):
    excluded = {query.applicant_id}
    if reviewed and query.applicant_id in PARTNERS:
        excluded.add(PARTNERS[query.applicant_id])
    result = retrieve(query, case_base, k=5, exclude_applicant_ids=excluded)
    if len(result.matches) != 5:
        raise ValueError(f'{query.applicant_id}: requires five defined neighbors')
    baseline_pool = [r for r in case_base if r.applicant_id not in excluded
                     and r.values['assistance_type_granted'] == query.values['assistance_type_granted']
                     and r.values['purpose_of_assistance'] == query.values['purpose_of_assistance']]
    predicted = predict(query, [m.record for m in result.matches])
    baseline = predict(query, baseline_pool)
    actual = number(query, 'amount_granted')
    scale = width(query)
    return dict(applicant_id=query.applicant_id, event_id=query.event_id,
                assistance_type=query.values['assistance_type_granted'],
                purpose=query.values['purpose_of_assistance'], actual=actual,
                prediction=predicted, baseline_prediction=baseline,
                error=abs(predicted-actual), baseline_error=abs(baseline-actual),
                scaled_error=abs(predicted-actual)/scale if scale else None,
                baseline_scaled_error=abs(baseline-actual)/scale if scale else None,
                excluded_applicants=sorted(excluded), eligible_count=result.eligible_count,
                undefined_pairs=result.undefined_pairs, numeric_ranges=result.numeric_ranges,
                active_fields=result.active_fields,
                neighbor_compared_field_counts=[len(m.field_scores) for m in result.matches],
                baseline_references=[(r.applicant_id, r.event_id) for r in baseline_pool],
                neighbors=[(m.record.applicant_id, m.record.event_id) for m in result.matches])


def summarize(rows):
    baseline = mean(r['baseline_error'] for r in rows)
    error = mean(r['error'] for r in rows)
    scaled = [r for r in rows if r['scaled_error'] is not None]
    return dict(n=len(rows), mae=error, baseline_mae=baseline,
                reduction_percent=100*(baseline-error)/baseline if baseline else None,
                scaled_mae=mean(r['scaled_error'] for r in scaled) if scaled else None,
                baseline_scaled_mae=mean(r['baseline_scaled_error'] for r in scaled) if scaled else None)


def pass_threshold(summary):
    # A zero-error baseline cannot be improved by twenty percent.
    return summary['baseline_mae'] > 0 and summary['mae'] <= .8 * summary['baseline_mae']


def aggregate(rows):
    groups = defaultdict(list)
    applicants = defaultdict(list)
    for r in rows:
        groups[r['assistance_type']].append(r)
        applicants[r['applicant_id']].append(r)
    return dict(by_type={k: summarize(v) for k, v in sorted(groups.items())},
                non_transport=summarize([r for r in rows if r['assistance_type'] != 'Transportation']),
                applicants={k: summarize(v) for k, v in sorted(applicants.items())})


def run(input_dir, output_dir):
    output_dir.mkdir(parents=True, exist_ok=False)
    def save(name, value):
        (output_dir/name).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    save('protocol.json', PROTOCOL)
    summaries, hashes = {}, {}
    for condition in ('p00', 'p25', 'p50', 'p75'):
        paths = [input_dir/f'{kind}_{condition}.csv' for kind in ('case_base', 'judged')]
        for path in paths:
            hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        base, judged = [load_study_csv(p).records for p in paths]
        if len(base) != 1000 or len(judged) != 40:
            raise ValueError('Expected 1000 case-base events and 40 reviewed cases')
        summaries[condition] = {}
        for name, queries in (('leave_one_applicant_out', base), ('reviewed', judged)):
            rows = [evaluate_case(q, base, reviewed=name == 'reviewed') for q in queries]
            save(f'{condition}_{name}_events.json', rows)
            summary = aggregate(rows)
            save(f'{condition}_{name}_applicants.json', summary.pop('applicants'))
            summaries[condition][name] = summary
        print(f'{condition} complete', flush=True)
    main = summaries['p50']['reviewed']['non_transport']
    if main['n'] != 36:
        raise ValueError('Main test must contain 36 non-transport cases')
    save('summary.json', dict(conditions=summaries, main_test_pass=pass_threshold(main),
                              input_sha256=hashes,
                              evaluator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    return summaries


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.input, args.output)
