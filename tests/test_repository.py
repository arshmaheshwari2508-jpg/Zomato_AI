"""Unit tests for RestaurantRepository (Phase 1)."""

from app.data.repository import RestaurantRepository
from app.domain.models import BudgetTier, Restaurant


def _sample_restaurants() -> list[Restaurant]:
    return [
        Restaurant(
            id="1",
            name="Italian Place",
            location="Bangalore",
            cuisine="Italian, Pizza",
            rating=4.5,
            cost_for_two=800.0,
            budget_tier=BudgetTier.MEDIUM,
        ),
        Restaurant(
            id="2",
            name="Budget Bites",
            location="Bangalore",
            cuisine="Chinese",
            rating=3.8,
            cost_for_two=200.0,
            budget_tier=BudgetTier.LOW,
        ),
        Restaurant(
            id="3",
            name="Delhi Diner",
            location="New Delhi",
            cuisine="North Indian",
            rating=4.2,
            cost_for_two=1200.0,
            budget_tier=BudgetTier.HIGH,
        ),
    ]


def test_get_all_and_by_id():
    repo = RestaurantRepository(_sample_restaurants())
    assert repo.count == 3
    assert repo.get_by_id("2").name == "Budget Bites"
    assert repo.get_by_id("missing") is None


def test_get_by_city_case_insensitive():
    repo = RestaurantRepository(_sample_restaurants())
    assert len(repo.get_by_city("bangalore")) == 2


def test_get_cities_and_cuisines():
    repo = RestaurantRepository(_sample_restaurants())
    assert "Bangalore" in repo.get_cities()
    assert "Italian" in repo.get_cuisines()
    assert "Pizza" in repo.get_cuisines()


def test_get_by_budget_tier():
    repo = RestaurantRepository(_sample_restaurants())
    assert len(repo.get_by_budget_tier(BudgetTier.LOW)) == 1
