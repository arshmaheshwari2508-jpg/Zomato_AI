"""Integration tests for the FastAPI API endpoints (Phase 4)."""

import pytest
from fastapi.testclient import TestClient

from app.data.repository import RestaurantRepository
from app.domain.models import BudgetTier, Restaurant, UserBudget
from app.llm.client import MockLLMClient, LLMError
from app.main import create_app


def _build_test_repo() -> RestaurantRepository:
    return RestaurantRepository(
        [
            Restaurant(
                id="1",
                name="Trattoria",
                location="Bangalore",
                cuisine="Italian, Pizza",
                rating=4.5,
                cost_for_two=800.0,
                budget_tier=BudgetTier.MEDIUM,
            ),
            Restaurant(
                id="2",
                name="China Wok",
                location="Bangalore",
                cuisine="Chinese",
                rating=4.0,
                cost_for_two=400.0,
                budget_tier=BudgetTier.MEDIUM,
            ),
            Restaurant(
                id="3",
                name="Budget Dosa",
                location="Bangalore",
                cuisine="South Indian",
                rating=3.5,
                cost_for_two=150.0,
                budget_tier=BudgetTier.LOW,
            ),
        ]
    )


@pytest.fixture
def api_client() -> TestClient:
    app = create_app()
    # Inject test repository and mock LLM client
    app.state.repository = _build_test_repo()
    app.state.llm_client = MockLLMClient()
    return TestClient(app)


def test_health_endpoint(api_client):
    response = api_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["dataset_loaded"] is True
    assert data["total_restaurants"] == 3


def test_health_endpoint_not_loaded():
    app = create_app()
    app.state.repository = None
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["dataset_loaded"] is False
    assert data["total_restaurants"] == 0


def test_stats_endpoint(api_client):
    response = api_client.get("/dataset/stats")
    assert response.status_code == 200
    data = response.json()
    assert "cities" in data
    assert "location_options" in data
    assert "cuisines" in data
    assert "budget_tiers" in data
    assert "Bangalore" in data["cities"]
    assert "Bangalore" in data["location_options"]
    assert "Italian" in data["cuisines"]
    assert "low" in data["budget_tiers"]


def test_stats_endpoint_service_unavailable():
    app = create_app()
    app.state.repository = None
    client = TestClient(app)
    response = client.get("/dataset/stats")
    assert response.status_code == 503
    assert "not yet initialized" in response.json()["detail"]


def test_recommendations_endpoint_success(api_client):
    payload = {
        "location": "Bangalore",
        "budget": "medium",
        "cuisine": "Italian",
        "min_rating": 4.0,
        "top_k": 2,
    }
    response = api_client.post("/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["recommendations"]) > 0
    first_rec = data["recommendations"][0]
    assert first_rec["name"] == "Trattoria"
    assert first_rec["cuisine"] == "Italian, Pizza"
    assert first_rec["rating"] == 4.5
    assert first_rec["rank"] == 1


def test_recommendations_endpoint_empty_filter(api_client):
    # No Mexican restaurant in our test repository
    payload = {
        "location": "Bangalore",
        "budget": "medium",
        "cuisine": "Mexican",
        "min_rating": 4.0,
        "top_k": 2,
    }
    response = api_client.post("/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["recommendations"]) == 0
    assert "No restaurants match" in data["summary"]


def test_recommendations_endpoint_fallback(api_client):
    # Inject a failing LLM client to force the engine into fallback mode
    class FailingLLMClient(MockLLMClient):
        def complete(self, messages, temperature=None, max_tokens=None):
            raise LLMError("Rate limit exceeded")

    api_client.app.state.llm_client = FailingLLMClient()
    payload = {
        "location": "Bangalore",
        "budget": "medium",
        "cuisine": "Any",
        "min_rating": 4.0,
        "top_k": 2,
    }
    response = api_client.post("/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["used_fallback"] is True
    # Fallback sorts candidates by rating: Trattoria (4.5) then China Wok (4.0)
    assert len(data["recommendations"]) == 2
    assert data["recommendations"][0]["name"] == "Trattoria"
    assert data["recommendations"][1]["name"] == "China Wok"
    assert "Rate limit exceeded" in data["error"]
