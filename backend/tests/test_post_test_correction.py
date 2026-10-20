from copy import deepcopy
from pathlib import Path
import numpy as np
import pytest
from backend.study_loader import load_study_csv
from research.corrected_amounts_20261020 import BOUNDS, FIELDS, LOWER, TOTAL_RANGE, score_details, LEGACY_SCORE, printed, check_pairs
from research.experiment_engine import blocks

ROOT = Path(__file__).resolve().parents[2]

@pytest.fixture(scope='module')
def base_path(tmp_path_factory):
    from research.reconciled import build
    return build(tmp_path_factory.mktemp('post-test')/'original')

def records(base_path,kind='case_base'):
    return load_study_csv(base_path/f'{kind}_p50.csv').records

def test_signed_available_score_preserves_complete_and_observed_no(base_path):
    base=records(base_path)
    for r in base:
        if all(r.values[f] is not None for f in FIELDS):
            assert score_details(r.values)['score']==pytest.approx(LEGACY_SCORE(printed(r)),abs=1e-12)
    v={f:None for f in FIELDS}
    with pytest.raises(ValueError):score_details(v)
    v['support_family']=False
    assert score_details(v)['observed_fields']==1
    assert score_details(v)['score']==pytest.approx(LOWER+TOTAL_RANGE)
    v['support_family']=True
    assert score_details(v)['score']==pytest.approx(LOWER)
    v['support_family']=None;v['sub_category']=frozenset()
    assert score_details(v)['observed_fields']==1
    assert score_details(v)['score']==pytest.approx(LOWER)

def test_corrected_twins_have_same_unknown_masks_and_amounts(base_path):
    from research.corrected_amounts_20261020 import correct_dataset
    corrected=correct_dataset(base_path,base_path.parent/'corrected')
    fixed=load_study_csv(corrected/'judged_p50.csv').records
    report=check_pairs(fixed)
    assert len(report['exact'])==4
    assert all(x['unknown_rule_fields_a']==x['unknown_rule_fields_b'] for x in report['exact'])

def test_purpose_pool_fits_only_eligible_references_and_never_uses_outcomes(base_path):
    base=records(base_path);q=next(r for r in base if r.values['purpose_of_assistance']=='Medicines')
    bs=blocks([q],base,pool='purpose');b=bs[0]
    assert all(r.values['purpose_of_assistance']=='Medicines' for r in b.references)
    assert 'purpose_of_assistance' not in b.metadata[0]['active_fields']
    assert all(not b.eligible[0,i] for i,r in enumerate(b.references) if r.applicant_id==q.applicant_id)
    changed=deepcopy(base)
    for r in changed:r.values['amount_granted']=1e9
    other=blocks([q],changed,pool='purpose')[0]
    np.testing.assert_array_equal(b.scores,other.scores)
    ix,_,_=b.neighbors(*b.sums(np.ones(39)),5)
    assert ix.shape==(1,5)
    from backend.study_retrieval import retrieve
    expected=retrieve(q,[r for r in base if r.values['purpose_of_assistance']=='Medicines'])
    assert b.metadata[0]['numeric_ranges']==expected.numeric_ranges
    assert {(b.references[i].applicant_id,b.references[i].event_id) for i in ix[0]}=={(m.record.applicant_id,m.record.event_id) for m in expected.matches}

def test_fixed_replication_feasibility_detects_the_whole_infeasible_fold(tmp_path):
    from research.post_test_feasibility_20261020 import audit
    from research.reconciled import build
    build(tmp_path/'51024',51024)
    result=audit(tmp_path,['51024'])
    assert result['failures']==[dict(dataset='51024',fold=0,minimum_training_purpose_references=4)]
    assert len(result['checks'])==5
