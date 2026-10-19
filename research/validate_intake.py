"""Read-only intake checks. Report contradictions; never repair source records.

python -m research.validate_intake PATH
"""
import argparse
import json
from collections import Counter
from backend.study_loader import load_study_csv


def validate(records):
    violations, unverifiable = [], []
    for r in records:
        v = r.values
        labels = v.get('sub_category')
        if labels and any('Wage Earner' in label for label in labels):
            employed, seasonal = v['employed_members'], v['seasonal_members']
            if (employed or 0) + (seasonal or 0) >= 1:
                continue
            item = dict(applicant_id=r.applicant_id, event_id=r.event_id,
                        rule='Wage Earner requires employed + seasonal >= 1')
            if employed is None or seasonal is None:
                unverifiable.append(item)
            else:
                violations.append(item)
    return dict(records=len(records), applicants=len({r.applicant_id for r in records}),
                type_counts=dict(Counter(r.values['assistance_type_granted'] for r in records)),
                violations=violations, unverifiable=unverifiable,
                policy='Read-only; missing counts do not establish a contradiction.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    args = parser.parse_args()
    report = validate(load_study_csv(args.input).records)
    print(json.dumps(report, indent=2))
    raise SystemExit(1 if report['violations'] else 0)
