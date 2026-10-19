from copy import deepcopy

import pytest

from backend.study_loader import StudyRecord
from backend.study_schema import MATCHING_FIELDS
from research.evaluate import aggregate, evaluate_case, pass_threshold, predict


def case(identity, income=1, purpose='Hospital bill', amount=100, cost=1000, event='1'):
    values = dict.fromkeys(MATCHING_FIELDS)
    values.update(assistance_type_granted='Medical', purpose_of_assistance=purpose,
                  total_income_past_6_months=income, amount_granted=amount, documented_cost=cost)
    return StudyRecord('test', 2, identity, event, values, {})


def test_actual_share_median_and_query_cost():
    refs = [case(str(i), amount=a, cost=c) for i, (a, c) in enumerate(
        [(100, 1000), (400, 2000), (900, 3000), (1600, 4000), (2500, 5000)])]
    query = case('Q', cost=2000)
    assert predict(query, refs) == 600
    query.values['assistance_type_granted'] = 'Food Assistance'
    for r in refs:
        r.values['assistance_type_granted'] = 'Food Assistance'
        r.values['documented_cost'] = None
    assert predict(query, refs) == 900


def test_same_purpose_baseline_and_all_applicant_partner_exclusions():
    query = case('J01', income=3, cost=2000)
    refs = [case(str(i), income=i, amount=100*i) for i in range(1, 7)]
    refs += [case('other-purpose', income=3, purpose='Medicines', amount=10000)]
    refs += [case('J01', income=99999, amount=99999, event='2'),
             case('J22', income=88888, amount=88888)]
    row = evaluate_case(query, refs, reviewed=True)
    assert row['baseline_prediction'] == 700
    assert row['numeric_ranges']['total_income_past_6_months'] == 5
    assert row['eligible_count'] == 7
    assert row['neighbor_compared_field_counts'] == [2] * 5
    assert {x[0] for x in row['baseline_references']} == set(map(str, range(1, 7)))
    assert not ({'J01', 'J22'} & {x[0] for x in row['neighbors']})
    changed = deepcopy(query)
    changed.values['amount_granted'] = 999999
    again = evaluate_case(changed, refs, reviewed=True)
    for key in ('neighbors', 'prediction', 'baseline_prediction', 'numeric_ranges'):
        assert again[key] == row[key]
    changed.values['documented_cost'] = 4000
    again = evaluate_case(changed, refs, reviewed=True)
    assert again['neighbors'] == row['neighbors']
    assert again['prediction'] == 2 * row['prediction']


def test_saved_counts_exclude_pair_specific_missing_and_shared_absences():
    query = case('Q', income=3)
    query.values.update(savings=True, crisis_hospitalization=False)
    refs = [case(str(i), income=i) for i in range(1, 7)]
    refs[0].values.update(savings=True, crisis_hospitalization=False)
    refs[1].values.update(savings=False, crisis_hospitalization=True)
    row = evaluate_case(query, refs)
    # Purpose is constant and removed. Other fields differ in pairwise availability.
    counts = dict(zip((x[0] for x in row['neighbors']), row['neighbor_compared_field_counts']))
    assert counts['1'] == 2
    assert all(counts[str(i)] == 1 for i in (3, 4, 5))


def test_reject_missing_cost_empty_pool_and_insufficient_neighbors():
    with pytest.raises(ValueError):
        predict(case('Q', cost=0), [case('A')])
    with pytest.raises(ValueError):
        predict(case('Q'), [])
    with pytest.raises(ValueError, match='five'):
        evaluate_case(case('Q'), [case('A'), case('B', income=2)])


def test_applicant_average_and_threshold_boundary():
    rows = [dict(applicant_id='A', assistance_type='Medical', error=x,
                 baseline_error=100, scaled_error=x/10000, baseline_scaled_error=.01)
            for x in (20, 60)]
    assert aggregate(rows)['applicants']['A']['mae'] == 40
    assert pass_threshold(dict(mae=80, baseline_mae=100))
    assert not pass_threshold(dict(mae=80.01, baseline_mae=100))
    assert not pass_threshold(dict(mae=0, baseline_mae=0))
