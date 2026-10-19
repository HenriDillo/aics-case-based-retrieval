import csv
from pathlib import Path

import pytest

from backend.study_loader import load_study_csv
from research.sheets import inspect_packet, export_packet
from research.validate_intake import validate

ROOT = Path(__file__).resolve().parents[2]


def test_required_wage_rule_reports_instead_of_repairing():
    records = load_study_csv(ROOT/'backend/data/study_intake.csv').records
    before = [r.values.copy() for r in records]
    report = validate(records)
    assert len(report['violations']) == 244
    assert len(report['unverifiable']) == 10
    assert [r.values for r in records] == before


def test_reviewed_packet_preserves_funds_diagnoses_and_pairs(tmp_path):
    target = tmp_path/'export'
    result = export_packet(target)
    assert result['cases'] == 40
    assert result['populated_diagnoses'] == 22
    assert (target/'AICS_Case_Review_11.docx').read_bytes() == (ROOT/'research/inputs/AICS_Case_Review_11.docx').read_bytes()


@pytest.mark.parametrize('field,value', [('Funds available','₱100,000'),
                                        ('Diagnosis / cause of death','Diagnosis not on sheet')])
def test_packet_rejects_divergence_from_csv(tmp_path, field, value):
    with (ROOT/'research/inputs/judged_cases_v11.csv').open(encoding='utf-8-sig', newline='') as f:
        reader=csv.DictReader(f)
        rows=list(reader)
        headers=reader.fieldnames
    rows[0][field] = value
    path=tmp_path/'changed.csv'
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError):
        inspect_packet(path, ROOT/'research/inputs/AICS_Case_Review_11.docx')
