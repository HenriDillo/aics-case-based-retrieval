import csv

import pytest

from backend.study_loader import load_study_csv, parse_value
from backend.study_schema import MATCHING_FIELDS, NOT_APPLICABLE, SYNTHETIC_COLUMNS, PRINTED_TO_CANONICAL


def write_rows(tmp_path, rows, headers=SYNTHETIC_COLUMNS):
    path = tmp_path / 'cases.csv'
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    return path


def record(event='1'):
    return dict.fromkeys(SYNTHETIC_COLUMNS, '') | {
        'case_id': 'C1', 'event_id': event, 'purpose_of_assistance': 'Medicines',
        'assistance_type_granted': 'Medical',
    }


def test_matching_boundary():
    assert len(MATCHING_FIELDS) == len(set(MATCHING_FIELDS)) == 39
    assert not set(MATCHING_FIELDS) & {
        'amount_granted', 'documented_cost', 'case_id', 'event_id',
        'combined_family_income', 'mode_of_assistance', 'fund_source',
        'assistance_type_granted', 'income_salaries_wages',
    }


def test_unknown_no_na_zero_are_distinct():
    assert parse_value('savings', '(not recorded)') is None
    assert parse_value('savings', 'No') is False
    assert parse_value('monthly_expenses', '0') == 0
    assert parse_value('disability_type', 'not applicable') == frozenset()
    assert parse_value('disability_type', '') is None
    assert parse_value('occupation', 'None') == 'None'
    assert parse_value('illness_duration', 'not applicable') == NOT_APPLICABLE


def test_sets_and_currency():
    assert parse_value('target_sector', 'SC|PWD') == parse_value('target_sector', 'SC, PWD')
    assert parse_value('total_income_past_6_months', '₱55,162') == 55162
    assert parse_value('documented_cost', '₱113,000 hospital billing statement, ₱40,500 balance after PhilHealth') == 40500
    assert parse_value('documented_cost', 'none presented for this type of request') == NOT_APPLICABLE


@pytest.mark.parametrize('field,value', [('savings', 'maybe'), ('monthly_expenses', 'NaN'), ('monthly_expenses', '-1'), ('employed_members', '1.5'), ('documented_cost', '₱100 and ₱200')])
def test_invalid_values_fail(field, value):
    with pytest.raises(ValueError):
        parse_value(field, value)


def test_repeat_applicants_and_read_only(tmp_path):
    path = write_rows(tmp_path, [record('1'), record('2')])
    before = path.read_bytes()
    data = load_study_csv(path)
    assert data.report['records'] == 2
    assert data.report['applicants'] == 1
    assert [r.event_id for r in data.records] == ['1', '2']
    assert data.records[0].raw['monthly_expenses'] == ''
    assert data.records[0].values['monthly_expenses'] is None
    assert path.read_bytes() == before


def test_bad_structure_and_duplicate_identity(tmp_path):
    with pytest.raises(ValueError, match='duplicate applicant/event'):
        load_study_csv(write_rows(tmp_path, [record(), record()]))
    with pytest.raises(ValueError, match='Missing required columns'):
        load_study_csv(write_rows(tmp_path, [], ['purpose_of_assistance']))


def test_report_resource_ambiguity_without_imputation(tmp_path):
    row = record()
    for key in row:
        if key.startswith('ext_'):
            row[key] = 'No'
    data = load_study_csv(write_rows(tmp_path, [row]))
    assert len(data.report['issues']) == 1
    assert data.records[0].values['ext_philhealth'] is False


def test_both_schemas_agree_on_matching_fields(tmp_path):
    source = record()
    source.update(target_sector='SC|PWD', total_income_past_6_months='55000', savings='No')
    synthetic = load_study_csv(write_rows(tmp_path, [source])).records[0]
    printed = {label: source.get(key, '') for label, key in PRINTED_TO_CANONICAL.items()}
    printed['Target Sector'] = 'SC, PWD'
    printed['Total income in the past 6 months'] = '₱55,000'
    printed['Seen at'] = '(not recorded)'
    judged = load_study_csv(write_rows(tmp_path, [printed], tuple(PRINTED_TO_CANONICAL))).records[0]
    assert {k: synthetic.values[k] for k in MATCHING_FIELDS} == {k: judged.values[k] for k in MATCHING_FIELDS}
    assert judged.event_id is None
    assert judged.raw['Target Sector'] == 'SC, PWD'
