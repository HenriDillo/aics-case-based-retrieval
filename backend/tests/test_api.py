"""Contract and thesis-invariant checks, using synthetic data only."""

from copy import deepcopy
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from backend import data_store, retrieval
from backend.catalog import SECTIONS, TYPES
from backend.main import app
from backend.models import CaseInput


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def intake(client):
    return client.get("/api/sample-cases").json()[0]["case"]


def test_dataset_has_30_complete_varied_closed_cases(client):
    frame = data_store.get_cases()
    assert len(frame) == 30
    assert set(frame.assistance_type) == set(TYPES)
    assert frame.control_number.is_unique
    for kind in TYPES:
        group = frame[frame.assistance_type == kind]
        assert len(group) == 5
        assert group.amount_granted.nunique() == 5
        assert group.intake_month.nunique() == 5
    assert (frame.amount_requested >= 100_000).sum() >= 3
    for record in frame.to_dict(orient="records"):
        assert CaseInput.model_validate(record).amount_granted is not None


def test_csv_read_once_per_process(monkeypatch):
    original = data_store._cases
    data_store._cases = None
    reads = []
    actual_read = pd.read_csv

    def tracked_read(*args, **kwargs):
        reads.append(args)
        return actual_read(*args, **kwargs)

    monkeypatch.setattr(pd, "read_csv", tracked_read)
    try:
        with TestClient(app) as client:
            for _ in range(3):
                sample = client.get("/api/sample-cases").json()[0]["case"]
                assert client.post("/api/similar-cases", json=sample).status_code == 200
            data_store.load_cases()
        assert len(reads) == 1
    finally:
        data_store._cases = original


def test_all_samples_work_and_have_no_outcome(client):
    samples = client.get("/api/sample-cases").json()
    assert len(samples) == 6
    for sample in samples:
        assert sample["case"]["amount_granted"] is None
        assert client.post("/api/similar-cases", json=sample["case"]).status_code == 200


def test_fixed_retrieval_has_only_documented_fields(client, intake):
    first = client.post("/api/similar-cases", json=intake)
    second_intake = client.get("/api/sample-cases").json()[1]["case"]
    second = client.post("/api/similar-cases", json=second_intake).json()
    assert first.status_code == 200
    assert first.headers["cache-control"] == "no-store"
    cases = first.json()
    assert len(cases) == 8
    assert [r["control_number"] for r in cases] == [r["control_number"] for r in second]
    allowed = set(CaseInput.model_fields) | {"matched_fields", "explanation_context", "comparison"}
    for case in cases:
        assert set(case) == allowed
        assert all(isinstance(text, str) and "%" not in text for text in case["matched_fields"])
        assert "fixed cases" in case["explanation_context"]
        assert [s["id"] for s in case["comparison"]] == [s["id"] for s in SECTIONS]
        assert all(set(row) == {"key", "label", "current", "past", "status"} for section in case["comparison"] for row in section["rows"])


def test_high_requested_amount_has_no_policy_ceiling(client, intake):
    intake["amount_requested"] = 9_000_000_000
    response = client.post("/api/similar-cases", json=intake)
    assert response.status_code == 200
    row = next(r for r in response.json()[0]["comparison"][0]["rows"] if r["key"] == "amount_requested")
    assert row["current"] == "₱9,000,000,000.00"


@pytest.mark.parametrize("field,value", [("amount_requested", -1), ("amount_requested", "NaN"), ("amount_requested", "Infinity"), ("assistance_type", "unknown"), ("family_members_employed", 1.5), ("crises", ["unknown"]), ("target_sector", "unknown")])
def test_invalid_intakes_are_rejected_without_echoing_data(client, intake, field, value):
    intake[field] = value
    response = client.post("/api/similar-cases", json=intake)
    assert response.status_code == 422
    assert all("input" not in error for error in response.json()["detail"])


def test_new_intake_cannot_include_name_or_score(client, intake):
    for forbidden in ["name", "score", "similarity", "priority", "recommended_amount"]:
        invalid = {**intake, forbidden: "unexpected"}
        assert client.post("/api/similar-cases", json=invalid).status_code == 422


def test_comparison_uses_actual_input_and_handles_unordered_checkboxes(client, intake):
    intake["crises"].reverse()
    intake["combined_family_income"] = 9876
    case = client.post("/api/similar-cases", json=intake).json()[0]
    rows = {r["key"]: r for s in case["comparison"] for r in s["rows"]}
    assert rows["crises"]["status"] == "same"
    assert rows["combined_family_income"]["status"] == "different"
    assert rows["combined_family_income"]["current"] == "₱9,876.00"
    assert rows["amount_granted"]["current"] == "Not recorded"
    assert rows["amount_granted"]["status"] == "not_recorded"


def test_conflicting_responses_and_partial_outcomes_rejected(client, intake):
    for updates in [
        {"external_resources": ["not applicable", "PhilHealth"]},
        {"recent_crisis": False},
        {"crises": []},
        {"amount_granted": 1000},
    ]:
        assert client.post("/api/similar-cases", json={**intake, **updates}).status_code == 422


def test_retrieval_does_not_mutate_dataframe_or_input(client, intake):
    before = deepcopy(data_store.get_cases().to_dict(orient="records"))
    original_intake = deepcopy(intake)
    cases = retrieval.retrieve_similar_cases(intake)
    cases[0]["support_systems"].append("changed")
    assert data_store.get_cases().to_dict(orient="records") == before
    assert intake == original_intake
    assert len(retrieval.retrieve_similar_cases(intake, 3)) == 3
    assert retrieval.retrieve_similar_cases(intake, 0) == []


def test_replacing_only_retrieval_function_preserves_api(client, intake, monkeypatch):
    def replacement(new_case: dict, k: int = 8) -> list[dict]:
        record = deepcopy(data_store.get_cases().iloc[-1].to_dict())
        return [{**record, "matched_fields": ["Replacement retrieval explanation"], "explanation_context": "Explanations for the submitted intake."}]

    monkeypatch.setattr(retrieval, "retrieve_similar_cases", replacement)
    response = client.post("/api/similar-cases", json=intake)
    assert response.status_code == 200
    assert response.json()[0]["matched_fields"] == ["Replacement retrieval explanation"]
    assert response.json()[0]["comparison"]


def test_empty_retrieval_is_supported(client, intake, monkeypatch):
    monkeypatch.setattr(retrieval, "retrieve_similar_cases", lambda new_case, k=8: [])
    assert client.post("/api/similar-cases", json=intake).json() == []


def test_schema_matches_intake_contract(client):
    schema = client.get("/api/form-schema").json()
    assert set(schema["empty_case"]) == set(CaseInput.model_fields)
