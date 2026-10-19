"""End-to-end API invariants on the synthetic study case base."""
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from backend import data_store, retrieval
from backend.catalog import SECTIONS, TYPES
from backend.main import app
from backend.models import CaseInput
from backend.study_adapter import to_display

@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client

@pytest.fixture
def intake(client):
    return client.get('/api/sample-cases').json()[0]['case']

def test_study_dataset(client):
    records = data_store.get_cases()
    assert len(records) == 1000
    assert len({r.applicant_id for r in records}) == 844
    assert {r.values['assistance_type_granted'] for r in records} == set(TYPES)
    assert all(r.values['amount_granted'] is not None for r in records)
    for record in records:
        CaseInput.model_validate(to_display(record))

def test_csv_loads_once(monkeypatch):
    old = data_store._cases
    data_store._cases = None
    calls = []
    actual = data_store.load_study_csv
    def load(path):
        calls.append(path)
        return actual(path)
    monkeypatch.setattr(data_store, 'load_study_csv', load)
    try:
        with TestClient(app) as client:
            for _ in range(3):
                sample = client.get('/api/sample-cases').json()[0]['case']
                assert client.post('/api/similar-cases', json=sample).status_code == 200
            data_store.load_cases()
        assert len(calls) == 1
    finally:
        data_store._cases = old

def test_all_six_types_retrieve_actual_cases(client):
    samples = client.get('/api/sample-cases').json()
    assert len(samples) == 6
    ids = []
    for sample in samples:
        query = sample['case']
        response = client.post('/api/similar-cases', json=query)
        assert response.status_code == 200
        assert response.headers['cache-control'] == 'no-store'
        records = response.json()
        assert len(records) == 5
        assert all(r['assistance_type'] == query['assistance_type'] for r in records)
        assert all(r['case_id'] != query['case_id'] for r in records)
        assert all(r['amount_granted'] is not None for r in records)
        if query['assistance_type'] not in ('Food Assistance','Cash Relief Assistance'):
            assert all(r['documented_cost'] is not None for r in records)
        ids.append({r['control_no'] for r in records})
    assert not ids[0] & ids[1]

def test_response_contract_no_scores(client, intake):
    cases = client.post('/api/similar-cases', json=intake).json()
    allowed = set(CaseInput.model_fields) | {'matched_fields','explanation_context','comparison'}
    for case in cases:
        assert set(case) == allowed
        assert '%' not in ' '.join(case['matched_fields'])
        assert 'generated research outcomes' in case['explanation_context']
        assert [s['id'] for s in case['comparison']] == [s['id'] for s in SECTIONS]

@pytest.mark.parametrize('field,value', [('monthly_expenses',True),('monthly_expenses',-1),('monthly_expenses','NaN'),('monthly_expenses','Infinity'),('assistance_type','unknown'),('employed_members',1.5),('target_sector',['unknown']),('target_sector',['SC','SC']),('savings','yes'),('date_received','bad')])
def test_invalid_inputs(client, intake, field, value):
    response = client.post('/api/similar-cases', json={**intake, field:value})
    assert response.status_code == 422
    assert all('input' not in e for e in response.json()['detail'])

def test_forbidden_fields(client,intake):
    for field in ['name','score','similarity','priority','recommended_amount','amount_requested']:
        assert client.post('/api/similar-cases', json={**intake,field:'unexpected'}).status_code == 422

def test_unknowns_empty_sets_and_zero(client,intake):
    query = {**intake, 'savings':None,'target_sector':[], 'monthly_expenses':0,'occupation':None}
    response = client.post('/api/similar-cases',json=query)
    assert response.status_code == 200
    rows = {r['key']:r for s in response.json()[0]['comparison'] for r in s['rows']}
    assert rows['savings']['status'] == 'not_recorded'
    assert rows['target_sector']['current'] == 'None / not applicable'
    assert rows['monthly_expenses']['current'] == '₱0.00'
    assert client.post('/api/similar-cases',json={'assistance_type':'Medical'}).json() == []

def test_comparison_and_outcome_independence(client,intake):
    original = client.post('/api/similar-cases',json=intake).json()
    query = {**intake,'combined_family_income':9876,'amount_granted':999999,'documented_cost':888888,'fund_source':'test'}
    changed = client.post('/api/similar-cases',json=query).json()
    assert [r['control_no'] for r in original] == [r['control_no'] for r in changed]
    rows = {r['key']:r for s in changed[0]['comparison'] for r in s['rows']}
    assert rows['combined_family_income']['current'] == '₱9,876.00'

def test_explanations_follow_query(client,intake):
    for value in [True,False,None]:
        query = {**intake, 'savings':value}
        cases = client.post('/api/similar-cases',json=query).json()
        for case in cases:
            for explanation in case['matched_fields']:
                if explanation.startswith('Savings:'):
                    assert value is not None and case['savings'] is value

def test_control_number_excludes_household(client,intake):
    query = {**intake,'case_id':None}
    cases = client.post('/api/similar-cases',json=query).json()
    assert all(r['case_id'] != intake['case_id'] for r in cases)

def test_no_mutation(client,intake):
    before = deepcopy(data_store.get_cases())
    original = deepcopy(intake)
    cases = retrieval.retrieve_similar_cases(intake)
    cases[0]['target_sector'].append('changed')
    assert data_store.get_cases() == before
    assert intake == original
    assert len(retrieval.retrieve_similar_cases(intake,3)) == 3
    assert retrieval.retrieve_similar_cases(intake,0) == []

def test_schema_matches_model(client):
    schema = client.get('/api/form-schema').json()
    assert set(schema['empty_case']) == set(CaseInput.model_fields)
    keys = [f['key'] for s in schema['sections'] for f in s['fields']]
    assert len(keys) == len(set(keys))

def test_missing_assistance_rejected(client):
    assert client.post('/api/similar-cases',json={}).status_code == 422
