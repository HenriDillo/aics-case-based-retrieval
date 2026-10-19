from copy import deepcopy

import pytest

from backend.study_loader import StudyRecord,load_study_csv
from backend.study_schema import MATCHING_FIELDS,NOT_APPLICABLE
from research.amounts import (assign_costs,calibrate,generate,household_score,
                             income_band,repair_wage_labels)
from research.build_dataset import build,sha,validate_amounts
from research.policy import SETTINGS


def row(identity='C1',event='1',purpose='Medicines',typ='Medical',cost=5000,**fields):
    values=dict.fromkeys(MATCHING_FIELDS)
    values.update(purpose_of_assistance=purpose,assistance_type_granted=typ,
                  documented_cost=cost,**fields)
    return StudyRecord('test',2,identity,event,values,{})


@pytest.mark.parametrize('value,points',[(None,0),(0,1),(55161,1),(55162,.5),(78803,.5),(78804,0)])
def test_income_edges(value,points):
    assert income_band(value)[1]==points


def test_unknowns_do_not_assert_absence_or_zero_employment():
    assert household_score(row())==0
    assert household_score(row(emergency_fund=False,savings=False,insurance_coverage=False,
                               employed_members=0))==pytest.approx(3.2)


def test_repeat_applicant_scores_are_event_specific():
    a=row(savings=False)
    b=row(event='2',savings=True)
    _,diagnostics=generate([a,b],.5,calibration=calibrate([a,b]))
    assert diagnostics[0]['household_score']==.8
    assert diagnostics[1]['household_score']==0


def test_content_seed_is_identifier_and_order_independent():
    a=row(savings=False)
    b=deepcopy(a);b.applicant_id='OTHER';b.event_id='2';b.values['case_id']='OTHER';b.values['date_received']='2099-01-01'
    calib=calibrate([a,b])
    for p in SETTINGS:
        out,_=generate([a,b],p,calibration=calib)
        assert out[0].values['amount_granted']==out[1].values['amount_granted']
        reordered,_=generate([b,a],p,calibration=calib)
        assert [r.values['amount_granted'] for r in reordered]==[r.values['amount_granted'] for r in out]
    costs,_=assign_costs([a,b])
    assert costs[0].values['documented_cost']==costs[1].values['documented_cost']


def test_p00_ignores_household_calibration():
    records=[row(savings=False)]
    a,_=generate(records,0,calibration={'mu':0,'sd':1})
    b,_=generate(records,0,calibration={'mu':999,'sd':2})
    assert a[0].values['amount_granted']==b[0].values['amount_granted']


def test_rounding_and_cost_constraints():
    records=[row(cost=1001),row('C2',cost=1049)]
    out,_=generate(records,.75,calibration={'mu':-100,'sd':1})
    assert [r.values['amount_granted'] for r in out]==[1000,1000]
    assert validate_amounts(out)==[]
    with pytest.raises(ValueError,match='below floor'):
        generate([row(cost=999)],.5,calibration={'mu':0,'sd':1})


def test_transportation_exact_and_direct_types_no_cost():
    transport=row(purpose='Transportation to home province',typ='Transportation',cost=2450)
    food=row('C2',purpose='Food subsidy',typ='Food Assistance',cost=NOT_APPLICABLE)
    for p in SETTINGS:
        output,_=generate([transport,food],p,calibration=calibrate([transport,food]))
        assert output[0].values['amount_granted']==2450
        assert validate_amounts(output)==[]
    with pytest.raises(ValueError,match='multiple of 50'):
        transport.values['documented_cost']=2451
        generate([transport],.5,calibration={'mu':0,'sd':1})


def test_conservative_wage_repair_is_logged_and_preserves_income():
    original=row(sub_category=frozenset({'Below Minimum Wage Earner','Solo Parent'}),
                 employed_members=0,seasonal_members=0,total_income_past_6_months=50000)
    out,changes,unresolved=repair_wage_labels([original])
    assert out[0].values['sub_category']==frozenset({'Solo Parent'})
    assert len(changes)==1 and not unresolved
    assert out[0].values['total_income_past_6_months']==50000
    assert 'Below Minimum Wage Earner' in original.values['sub_category']


def test_cost_range_can_adjust_only_once(monkeypatch):
    import research.amounts as amounts
    monkeypatch.setitem(amounts.COST_RANGES,'Medicines',(2000,2000))
    records,report=assign_costs([row(),row('C2')])
    assert len(report['range_adjustments'])==1
    assert report['checks'][0]['within_20_percent']


def test_full_pipeline_and_reproducibility(tmp_path):
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]
    base=root/'backend/data/study_intake.csv'
    judged=root/'research/inputs/judged_cases_v11.csv'
    source_hashes=[sha(base),sha(judged)]
    a=build(tmp_path/'first',base,judged)
    b=build(tmp_path/'second',base,judged)
    assert a['output_hashes']==b['output_hashes']
    assert a['case_base_events']==1000 and a['judged_cases']==40
    assert a['wage_label_repairs']==244
    assert a['cost_checks_pass']
    assert a['income_bands']['judged']=={'below_food':26,'food_to_poverty':7,'at_or_above_poverty':7}
    assert [sha(base),sha(judged)]==source_hashes
    assert len(load_study_csv(tmp_path/'first/case_base_p50.csv').records)==1000
    with pytest.raises(ValueError,match='already exists'):
        build(tmp_path/'first',base,judged)
