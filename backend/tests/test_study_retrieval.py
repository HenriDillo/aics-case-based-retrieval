from copy import deepcopy

import pytest

from backend.study_loader import StudyRecord
from backend.study_retrieval import field_similarity, retrieve
from backend.study_schema import MATCHING_FIELDS


def case(identity, event='1', assistance='Medical', **fields):
    values = dict.fromkeys(MATCHING_FIELDS)
    values.update(fields)
    values['assistance_type_granted'] = assistance
    return StudyRecord('test', 2, identity, event, values, {})


def test_hand_calculated_equal_weight_average():
    query = case('Q', savings=False, employed_members=0, target_sector=frozenset({'SC'}))
    a = case('A', savings=False, employed_members=5, target_sector=frozenset({'SC', 'PWD'}))
    b = case('B', savings=True, employed_members=10, target_sector=frozenset({'PWD'}))
    result = retrieve(query, [a, b])
    # Training range is 10-5=5; A's scores are 1, 0 and 1/2.
    assert result.matches[0].record.applicant_id == 'A'
    assert result.matches[0].distance == pytest.approx(0.5)
    assert result.matches[1].distance == 1


def test_shared_absences_differ_by_section():
    assert field_similarity('crisis_hospitalization', False, False) is None
    assert field_similarity('vuln_member_incapacitated', False, False) is None
    for field in ['support_family', 'ext_philhealth', 'savings', 'crisis_last_3_months']:
        assert field_similarity(field, False, False) == 1
    assert field_similarity('ext_philhealth', None, False) is None


def test_multiselect_and_categorical_duration():
    assert field_similarity('target_sector', frozenset(), frozenset()) == 1
    assert field_similarity('target_sector', frozenset(), frozenset({'SC'})) == 0
    assert field_similarity('illness_duration', 'not_applicable', 'not_applicable') == 1
    assert field_similarity('illness_duration', 'not_applicable', 'Chronic, lifelong') == 0
    assert field_similarity('illness_duration', 'Three months to a year', 'Chronic, lifelong') == 0


def test_clamp_outside_reference_range():
    assert field_similarity('monthly_expenses', 1000, 1, 10) == 0
    assert field_similarity('monthly_expenses', 1, 1, 10) == 1


def test_applicant_type_and_extra_exclusions_precede_ranges():
    query = case('Q', employed_members=999)
    records = [case('Q', event='2', employed_members=10000),
               case('OTHER', assistance='Funeral', employed_members=99999),
               case('PAIR', employed_members=88888),
               case('FOLD', employed_members=77777),
               case('A', employed_members=2), case('B', employed_members=4)]
    result = retrieve(query, records, exclude_applicant_ids=['PAIR', 'FOLD'])
    assert result.numeric_ranges == {'employed_members': 2}
    assert result.eligible_count == 2
    assert {m.record.applicant_id for m in result.matches} == {'A', 'B'}


def test_constants_and_undefined_pairs():
    query = case('Q', savings=True)
    result = retrieve(query, [case('A', savings=True), case('B', savings=True)])
    assert result.active_fields == ()
    assert result.matches == ()
    assert result.undefined_pairs == 2
    # Reference varies but query has no comparable data.
    result = retrieve(case('Q'), [case('A', savings=True), case('B', savings=False)])
    assert result.undefined_pairs == 2


def test_missing_is_removed_from_denominator():
    query = case('Q', savings=False, employed_members=0)
    result = retrieve(query, [case('A', savings=False),
                             case('B', savings=True, employed_members=0),
                             case('C', savings=True, employed_members=2)])
    assert result.matches[0].record.applicant_id == 'A'
    assert result.matches[0].distance == 0
    assert result.matches[0].field_scores == {'savings': 1.0}


def test_no_outcome_influence_and_stable_ties():
    query = case('Q', savings=False)
    records = [case('B', savings=False), case('A', savings=False), case('C', savings=True)]
    before = retrieve(query, records)
    for row in [query, *records]:
        row.values.update(amount_granted=999999, documented_cost=1,
                          fund_source='changed', household_z=999)
    after = retrieve(query, reversed(records))
    signature = lambda result: [(m.record.applicant_id, m.distance) for m in result.matches]
    assert signature(before) == signature(after) == [('A', 0), ('B', 0), ('C', 1)]


def test_default_five_and_no_mutation():
    query = case('Q', employed_members=0)
    records = [case(str(i), employed_members=i) for i in range(8)]
    snapshot = deepcopy(records)
    result = retrieve(query, records)
    assert len(result.matches) == 5
    assert records == snapshot
    result.matches[0].record.values['employed_members'] = 999
    assert records == snapshot
    assert retrieve(query, []).matches == ()


@pytest.mark.parametrize('k', [0, -1, 1.5, True])
def test_invalid_k(k):
    with pytest.raises(ValueError):
        retrieve(case('Q'), [], k)


def test_invalid_normalized_data_and_duplicate_identity():
    with pytest.raises(ValueError, match='invalid normalized'):
        retrieve(case('Q', employed_members='not_applicable'), [])
    with pytest.raises(ValueError, match='Duplicate candidate'):
        retrieve(case('Q'), [case('A'), case('A')])
    with pytest.raises(ValueError, match='Only matching'):
        field_similarity('amount_granted', 1, 1)
