"""Independent equal-weight Gower retrieval for normalized v25 study records.

Distances and field scores are research diagnostics, never application responses.
Plain range scaling and categorical illness duration are the fixed baseline here.
Run: python -m backend.study_retrieval CASE_BASE QUERY_FILE QUERY_ID
"""
import argparse
from copy import deepcopy
from dataclasses import dataclass
import json
import math
from typing import Iterable

from .study_loader import StudyRecord, load_study_csv
from .study_schema import (
    ASYMMETRIC_FIELDS, BOOLEAN_FIELDS, MATCHING_FIELDS, MULTI_FIELDS,
    NUMERIC_FIELDS,
)

NUMERIC_MATCHING = frozenset(MATCHING_FIELDS) & NUMERIC_FIELDS
ASSISTANCE_TYPES = frozenset({
    'Medical', 'Funeral', 'Educational', 'Food Assistance',
    'Cash Relief Assistance', 'Transportation',
})


@dataclass(frozen=True)
class Match:
    record: StudyRecord
    distance: float
    field_scores: dict[str, float]


@dataclass(frozen=True)
class RetrievalResult:
    matches: tuple[Match, ...]
    eligible_count: int
    undefined_pairs: int
    active_fields: tuple[str, ...]
    numeric_ranges: dict[str, float]
    requested_count: int


def validate_record(record: StudyRecord):
    """Fail on malformed canonical inputs instead of silently inventing matches."""
    if not record.applicant_id:
        raise ValueError('An applicant/case ID is required')
    if record.values.get('assistance_type_granted') not in ASSISTANCE_TYPES:
        raise ValueError('A recognized assistance type is required')
    missing = set(MATCHING_FIELDS) - record.values.keys()
    if missing:
        raise ValueError(f'Missing matching fields: {sorted(missing)}')
    for field in MATCHING_FIELDS:
        value = record.values[field]
        if value is None:
            continue
        if field in NUMERIC_MATCHING:
            valid = (not isinstance(value, bool) and isinstance(value, (int, float))
                     and math.isfinite(value) and value >= 0)
        elif field in BOOLEAN_FIELDS:
            valid = isinstance(value, bool)
        elif field in MULTI_FIELDS:
            valid = isinstance(value, frozenset) and all(isinstance(v, str) and v for v in value)
        else:
            valid = isinstance(value, str) and bool(value)
        if not valid:
            raise ValueError(f'{record.applicant_id}: invalid normalized {field}')


def field_similarity(field: str, left, right, numeric_range: float | None = None):
    """None means excluded, not zero similarity. Called only for active fields."""
    if field not in MATCHING_FIELDS:
        raise ValueError('Only matching fields can enter similarity')
    if left is None or right is None:
        return None
    if field in ASYMMETRIC_FIELDS and left is False and right is False:
        return None
    if field in MULTI_FIELDS:
        union = left | right
        return len(left & right) / len(union) if union else 1.0
    if field in NUMERIC_MATCHING:
        if numeric_range is None or not math.isfinite(numeric_range) or numeric_range <= 0:
            raise ValueError('Numeric comparison requires a positive reference range')
        return max(0.0, 1.0 - abs(left - right) / numeric_range)
    # Includes explicit not-applicable illness duration and symmetric No answers.
    return float(left == right)


def retrieve(query: StudyRecord, case_base: Iterable[StudyRecord], k: int = 5,
             *, exclude_applicant_ids: Iterable[str] = ()) -> RetrievalResult:
    """Return up to k events of the same type, holding out the whole applicant.

    Extra exclusions support pair partners and training-fold isolation. They apply
    before fitting ranges AND before retrieval. Callers must supply pair partners;
    neither household linkage nor judged-case pairing is inferred from fields.
    A fold-fitting caller passes its training records only (or excludes the fold).
    Ties use applicant/event IDs, never row order or outcomes.
    """
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError('k must be a positive integer')
    validate_record(query)
    excluded = set(exclude_applicant_ids) | {query.applicant_id}
    eligible = []
    identities = set()
    for record in case_base:
        if record.applicant_id in excluded:
            continue
        if record.values.get('assistance_type_granted') != query.values['assistance_type_granted']:
            continue
        validate_record(record)
        identity = (record.applicant_id, record.event_id)
        if identity in identities:
            raise ValueError(f'Duplicate candidate identity: {identity}')
        identities.add(identity)
        eligible.append(record)
    active, ranges = [], {}
    for field in MATCHING_FIELDS:
        known = {r.values[field] for r in eligible if r.values[field] is not None}
        # Unknown is not a category. One observed value cannot distinguish cases.
        if len(known) < 2:
            continue
        active.append(field)
        if field in NUMERIC_MATCHING:
            ranges[field] = max(known) - min(known)
    matches, undefined = [], 0
    for record in eligible:
        scores = {}
        for field in active:
            score = field_similarity(field, query.values[field], record.values[field], ranges.get(field))
            if score is not None:
                scores[field] = score
        if not scores:
            undefined += 1
            continue
        distance = max(0.0, min(1.0, 1.0 - sum(scores.values()) / len(scores)))
        matches.append(Match(record, distance, scores))
    matches.sort(key=lambda m: (m.distance, m.record.applicant_id, m.record.event_id or ''))
    # Return owned copies so downstream display code cannot mutate the case base.
    return RetrievalResult(tuple(deepcopy(matches[:k])), len(eligible), undefined,
                           tuple(active), ranges, k)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case_base')
    parser.add_argument('query_file')
    parser.add_argument('query_id')
    parser.add_argument('--event-id')
    parser.add_argument('--exclude-applicant', action='append', default=[])
    parser.add_argument('-k', type=int, default=5)
    args = parser.parse_args()
    base = load_study_csv(args.case_base)
    queries = load_study_csv(args.query_file)
    selected = [r for r in queries.records if r.applicant_id == args.query_id
                and (args.event_id is None or r.event_id == args.event_id)]
    if len(selected) != 1:
        parser.error('Select exactly one query; use --event-id for repeat applicants')
    result = retrieve(selected[0], base.records, args.k,
                      exclude_applicant_ids=args.exclude_applicant)
    print(json.dumps({
        'query_id': args.query_id, 'eligible_count': result.eligible_count,
        'undefined_pairs': result.undefined_pairs, 'active_fields': result.active_fields,
        'numeric_ranges': result.numeric_ranges,
        'matches': [{'case_id': m.record.applicant_id, 'event_id': m.record.event_id,
                     'assistance_type': m.record.values['assistance_type_granted'],
                     'purpose': m.record.values['purpose_of_assistance'],
                     'amount_granted': m.record.values.get('amount_granted'),
                     'documented_cost': m.record.values.get('documented_cost'),
                     'compared_fields': len(m.field_scores)} for m in result.matches],
    }, indent=2))


if __name__ == '__main__':
    main()
