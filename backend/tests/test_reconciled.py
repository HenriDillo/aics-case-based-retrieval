import csv
import json
from pathlib import Path

from backend.study_loader import load_study_csv
from research.reconciled import amounts, build, printed, rule

SOURCE = Path('research/inputs/compatibility')


def test_all_160_supplied_amounts_match_source_calibration():
    records = load_study_csv('research/inputs/judged_cases_v11.csv').records
    calibration = json.loads((SOURCE/'calibration.json').read_text())
    for tag,p in [('p00',0),('p25',.25),('p50',.5),('p75',.75)]:
        expected = list(csv.DictReader((SOURCE/f'amounts_{tag}.csv').open(encoding='utf-8-sig')))
        actual,_ = amounts(records,p,calibration)
        assert [r.values['amount_granted'] for r in actual] == [int(r['amount_granted']) for r in expected]


def test_generated_fixture_has_no_wage_contradictions_and_repeats(tmp_path):
    from research.validate_intake import validate
    a=build(tmp_path/'a',41000,100)
    b=build(tmp_path/'b',41000,100)
    assert (a/'case_base_p50.csv').read_bytes() == (b/'case_base_p50.csv').read_bytes()
    records=load_study_csv(a/'case_base_p50.csv').records
    assert not validate(records)['violations']
    assert len(records)==100
    assert len({r.applicant_id for r in records})<100
