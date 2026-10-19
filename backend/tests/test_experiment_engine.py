from copy import deepcopy
from pathlib import Path
import numpy as np
import pytest

from backend.study_loader import load_study_csv
from backend.study_retrieval import retrieve
from research.experiment_engine import blocks, membership, Outcomes, fit, paired_test
from research.evaluate import evaluate_case

@pytest.fixture(scope='module')
def base_path(tmp_path_factory):
    from research.reconciled import build
    return build(tmp_path_factory.mktemp('experiment-inputs')/'primary')


def test_vectorized_engine_matches_scalar_baseline_and_pair_counts(base_path):
    base=load_study_csv(base_path/'case_base_p50.csv').records
    judged=load_study_csv(base_path/'judged_p50.csv').records
    for queries,review in [(base[:35],False),(judged,True)]:
        bs=blocks(queries,base,reviewed=review)
        output=Outcomes(bs,base+judged)
        rows=output.evaluate([b.sums(np.ones(39)) for b in bs],details=True)[2]
        by={(r['applicant_id'],r['event_id']):r for r in rows}
        for q in queries:
            expected=evaluate_case(q,base,reviewed=review)
            actual=by[q.applicant_id,q.event_id]
            assert actual['prediction']==pytest.approx(expected['prediction'])
            assert actual['neighbors']==[list(n) for n in expected['neighbors']]
            assert actual['neighbor_compared_field_counts']==expected['neighbor_compared_field_counts']
            assert actual['numeric_ranges']==expected['numeric_ranges']


def test_fuzzy_shapes_ties_and_rank():
    np.testing.assert_allclose(membership(np.array([0,25,50,75,100]),[25,50,75]),
                               [[1,0,0],[1,0,0],[0,1,0],[0,0,1],[0,0,1]])
    np.testing.assert_allclose(membership(37.5,[25,50,75]),[.5,.5,0])
    assert paired_test([1,1],[1,1])['p']==1
    # No ties: n=3, positive rank sum=6, mean=3, variance=3.5.
    assert paired_test([1,2,3],[0,0,0])['z']==pytest.approx(3/(3.5**.5))
    assert paired_test([1,2,3],[0,0,0])['p']==pytest.approx(paired_test([0,0,0],[1,2,3])['p'])


def test_outcomes_cannot_change_distance_and_heldout_values_cannot_fit_ranges(base_path):
    base=load_study_csv(base_path/'case_base_p50.csv').records
    training=base[:100]
    query=deepcopy(training[0]); query.values['monthly_expenses']=1e12
    b=blocks([query],training)[0]
    expected=retrieve(query,training)
    assert b.metadata[0]['numeric_ranges']==expected.numeric_ranges
    changed=deepcopy(training)
    for r in changed: r.values['amount_granted']=99999999
    other=blocks([query],changed)[0]
    np.testing.assert_array_equal(b.scores,other.scores)


def test_fit_is_reproducible_and_constrained(base_path):
    base=load_study_csv(base_path/'case_base_p50.csv').records[:120]
    bs=blocks(base,base)
    outcomes=Outcomes(bs,base)
    a,trace=fit(bs,outcomes,17,20)
    b,_=fit(bs,outcomes,17,20)
    np.testing.assert_array_equal(a,b)
    assert a.min()>=0 and a.sum()==pytest.approx(39)
    assert len(trace)==20
    assert all(x['incumbent']>=y['incumbent'] for x,y in zip(trace,trace[1:]))
