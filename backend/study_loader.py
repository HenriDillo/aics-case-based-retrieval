"""Read-only v25 CSV normalization; no imputation or amount generation.

Run: python -m backend.study_loader PATH [PATH ...]
"""
import argparse
import csv
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

from .study_schema import (
    BOOLEAN_FIELDS, MATCHING_FIELDS, MULTI_FIELDS, NOT_APPLICABLE,
    NUMERIC_FIELDS, PRINTED_TO_CANONICAL, RESOURCE_FIELDS, SYNTHETIC_COLUMNS,
)


@dataclass
class StudyRecord:
    source: str
    row_number: int
    applicant_id: str
    event_id: str | None
    values: dict
    raw: dict[str, str]


@dataclass
class StudyDataset:
    records: list[StudyRecord]
    report: dict


def parse_value(field, raw):
    text = raw.strip()
    if text.lower() in ('', '(not recorded)', 'not recorded'):
        return None
    if text.lower() in ('not_applicable', 'not applicable'):
        return frozenset() if field in MULTI_FIELDS else NOT_APPLICABLE
    if field in BOOLEAN_FIELDS or field == 'no_income_recorded':
        if text.lower() not in ('yes', 'no'):
            raise ValueError('expected Yes or No')
        return text.lower() == 'yes'
    if field in MULTI_FIELDS:
        return frozenset(x.strip() for x in re.split(r'[|,]', text) if x.strip())
    if field == 'documented_cost':
        if text.lower() == 'none presented for this type of request':
            return NOT_APPLICABLE
        # The outstanding balance, not the gross hospital bill, sets the scale.
        balance = re.search(r'₱([\d,]+(?:\.\d+)?)\s*balance after PhilHealth', text, re.I)
        amounts = re.findall(r'₱([\d,]+(?:\.\d+)?)', text)
        if balance:
            text = balance.group(1)
        elif len(amounts) == 1:
            text = amounts[0]
        elif amounts:
            raise ValueError('ambiguous cost: multiple amounts without a recognized balance')
    if field in NUMERIC_FIELDS or field == 'documented_cost':
        value = float(text.replace('₱', '').replace(',', ''))
        if not math.isfinite(value) or value < 0:
            raise ValueError('expected a finite nonnegative number')
        if field in ('employed_members', 'seasonal_members') and not value.is_integer():
            raise ValueError('expected a whole member count')
        return int(value) if value.is_integer() else value
    return text


def load_study_csv(path: str | Path) -> StudyDataset:
    path = Path(path)
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)):
            raise ValueError('Duplicate CSV headers')
        if 'Purpose of assistance' in headers:
            schema = 'printed_v11'
            mapping = PRINTED_TO_CANONICAL
        elif 'purpose_of_assistance' in headers:
            schema = 'synthetic_v1'
            mapping = {key: key for key in SYNTHETIC_COLUMNS}
            if 'documented_cost' in headers:
                mapping['documented_cost'] = 'documented_cost'
        else:
            raise ValueError('Unrecognized study CSV schema')
        missing = sorted(set(mapping) - set(headers))
        if missing:
            raise ValueError(f'Missing required columns: {missing}')
        rows = list(reader)
    records, issues, identities = [], [], set()
    for number, raw in enumerate(rows, start=2):
        if None in raw or any(v is None for v in raw.values()):
            raise ValueError(f'CSV row {number}: wrong number of cells')
        values = {}
        for source, target in mapping.items():
            try:
                values[target] = parse_value(target, raw[source])
            except ValueError as error:
                raise ValueError(f'CSV row {number}, {source}: {error}') from error
        applicant = values['case_id']
        event = values.get('event_id')
        if not applicant or (schema == 'synthetic_v1' and not event):
            raise ValueError(f'CSV row {number}: missing identity')
        identity = (applicant, event)
        if identity in identities:
            raise ValueError(f'CSV row {number}: duplicate applicant/event identity {identity}')
        identities.add(identity)
        # Printed sheets have case IDs but no separate event or household linkage.
        # Keep event_id absent; do not invent identities or pair membership.
        resources = [values[k] for k in RESOURCE_FIELDS]
        if all(v is False for v in resources):
            issues.append({'row': number, 'case_id': applicant,
                           'issue': 'All resources are No; source has no separate Section V N/A flag. Unanswered versus explicit absence cannot be verified.'})
        records.append(StudyRecord(schema, number, applicant, event, values, dict(raw)))
    report = {
        'path': str(path.resolve()), 'schema': schema, 'records': len(records),
        'applicants': len({r.applicant_id for r in records}),
        'matching_fields': len(MATCHING_FIELDS),
        'unknown_matching_values': {k: sum(r.values[k] is None for r in records) for k in MATCHING_FIELDS},
        'unmapped_columns': sorted(set(headers) - set(mapping)),
        'documented_cost_column_present': 'documented_cost' in mapping.values(),
        'missing_amounts': sum(r.values['amount_granted'] is None for r in records),
        'separate_event_ids_present': schema == 'synthetic_v1',
        'issues': issues,
    }
    return StudyDataset(records, report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='+')
    args = parser.parse_args()
    for path in args.paths:
        print(json.dumps(load_study_csv(path).report, indent=2, ensure_ascii=True))


if __name__ == '__main__':
    main()
