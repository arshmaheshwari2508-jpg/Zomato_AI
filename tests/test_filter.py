"""Unit tests for FilterService (Phase 2)."""

import pytest
from pydantic import ValidationError

from app.data.repository import RestaurantRepository
from app.domain.filter import FilterService
from app.domain.models import BudgetTier, Restaurant, UserBudget, UserPreferences


def _build_repo() -> RestaurantRepository:
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
                metadata={"rest_type": "Casual Dining", "area": "Indiranagar"},
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
            Restaurant(
                id="4",
                name="Fine Italiano",
                location="Bangalore",
                cuisine="Italian",
                rating=4.8,
                cost_for_two=2000.0,
                budget_tier=BudgetTier.HIGH,
            ),
            Restaurant(
                id="5",
                name="Delhi Dhaba",
                location="New Delhi",
                cuisine="North Indian",
                rating=4.2,
                cost_for_two=500.0,
                budget_tier=BudgetTier.MEDIUM,
                metadata={"area": "Rohini"},
            ),
            Restaurant(
                id="6",
                name="Spice Hub",
                location="Bangalore",
                cuisine="North Indian",
                rating=4.1,
                cost_for_two=600.0,
                budget_tier=BudgetTier.MEDIUM,
                metadata={"area": "BTM Layout"},
            ),
            Restaurant(
                id="7",
                name="Urban Bites",
                location="Bangalore",
                cuisine="Continental",
                rating=4.3,
                cost_for_two=700.0,
                budget_tier=BudgetTier.MEDIUM,
            ),
        ]
    )


@pytest.fixture
def filter_service() -> FilterService:
    return FilterService(_build_repo(), max_candidates=3)


def test_user_preferences_validation():
    prefs = UserPreferences(
        location="Bangalore",
        budget=UserBudget.MEDIUM,
        cuisine="Italian",
        min_rating=4.0,
    )
    assert prefs.top_k == 5
    assert prefs.cuisine_filter_active is True


def test_user_preferences_rejects_empty_location():
    with pytest.raises(ValidationError):
        UserPreferences(location="  ", budget=UserBudget.LOW)


def test_user_preferences_clamps_top_k():
    prefs = UserPreferences(location="Bangalore", budget=UserBudget.LOW, top_k=25)
    assert prefs.top_k == 10


def test_bangalore_italian_medium_min_rating():
    service = FilterService(_build_repo(), max_candidates=30)
    prefs = UserPreferences(
        location="Bangalore",
        budget=UserBudget.MEDIUM,
        cuisine="Italian",
        min_rating=4.0,
    )
    result = service.apply(prefs)

    assert not result.is_empty
    assert result.should_call_llm
    assert result.resolved_location == "Bangalore"
    assert len(result.candidates) == 1
    assert result.candidates[0].name == "Trattoria"
    assert all(r.rating >= 4.0 for r in result.candidates)
    assert all(r.budget_tier == BudgetTier.MEDIUM for r in result.candidates)


def test_partial_cuisine_match():
    service = FilterService(_build_repo(), max_candidates=30)
    prefs = UserPreferences(
        location="Bangalore",
        budget=UserBudget.HIGH,
        cuisine="Ital",
        min_rating=0.0,
    )
    result = service.apply(prefs)
    names = {r.name for r in result.candidates}
    assert "Fine Italiano" in names


def test_cuisine_any_skips_cuisine_filter():
    service = FilterService(_build_repo(), max_candidates=30)
    prefs = UserPreferences(
        location="Bangalore",
        budget=UserBudget.LOW,
        cuisine="Any",
        min_rating=0.0,
    )
    result = service.apply(prefs)
    assert len(result.candidates) == 1
    assert result.candidates[0].name == "Budget Dosa"


def test_no_match_returns_empty_state():
    service = FilterService(_build_repo(), max_candidates=30)
    prefs = UserPreferences(
        location="Bangalore",
        budget=UserBudget.LOW,
        cuisine="Mexican",
        min_rating=0.0,
    )
    result = service.apply(prefs)

    assert result.is_empty
    assert not result.should_call_llm
    assert result.candidates == []
    assert result.message is not None
    assert len(result.suggestions) >= 1


def test_unknown_location_returns_suggestions():
    service = FilterService(_build_repo(), max_candidates=30)
    prefs = UserPreferences(
        location="Tokyo",
        budget=UserBudget.MEDIUM,
        cuisine="Italian",
    )
    result = service.apply(prefs)

    assert result.is_empty
    assert "Tokyo" in result.message
    assert "Bangalore" in result.suggestions[0] or any("Bangalore" in s for s in result.suggestions)


def test_location_typo_fuzzy_match():
    service = FilterService(_build_repo(), max_candidates=30)
    prefs = UserPreferences(
        location="Banglore",
        budget=UserBudget.MEDIUM,
        cuisine="Chinese",
    )
    result = service.apply(prefs)
    assert result.resolved_location == "Bangalore"
    assert result.candidates[0].name == "China Wok"


def test_boundary_rating_excludes_below_threshold():
    service = FilterService(_build_repo(), max_candidates=30)
    prefs = UserPreferences(
        location="Bangalore",
        budget=UserBudget.LOW,
        cuisine="Any",
        min_rating=3.6,
    )
    result = service.apply(prefs)
    assert result.is_empty


def test_max_candidates_cap():
    service = FilterService(_build_repo(), max_candidates=2)
    prefs = UserPreferences(
        location="Bangalore",
        budget=UserBudget.MEDIUM,
        cuisine="Any",
        min_rating=0.0,
    )
    result = service.apply(prefs)
    assert len(result.candidates) == 2
    assert result.capped is True
    assert result.total_matched == 4


def test_case_insensitive_location():
    service = FilterService(_build_repo(), max_candidates=30)
    prefs = UserPreferences(
        location="bangalore",
        budget=UserBudget.MEDIUM,
        cuisine="Chinese",
    )
    result = service.apply(prefs)
    assert result.resolved_location == "Bangalore"


def test_get_dataset_hints():
    service = FilterService(_build_repo())
    hints = service.get_dataset_hints()
    assert "Bangalore" in hints.cities
    assert "Italian" in hints.cuisines
    assert "Indiranagar, Bangalore" in hints.location_options


def test_area_and_city_filtering():
    service = FilterService(_build_repo(), max_candidates=30)
    
    # 1. Search in Indiranagar, Bangalore
    prefs = UserPreferences(
        location="Indiranagar, Bangalore",
        budget=UserBudget.MEDIUM,
        cuisine="Any",
    )
    result = service.apply(prefs)
    assert not result.is_empty
    assert result.resolved_location == "Indiranagar, Bangalore"
    assert len(result.candidates) == 1
    assert result.candidates[0].name == "Trattoria"

    # 2. Search in Rohini, New Delhi
    prefs2 = UserPreferences(
        location="Rohini, New Delhi",
        budget=UserBudget.MEDIUM,
        cuisine="Any",
    )
    result2 = service.apply(prefs2)
    assert not result2.is_empty
    assert result2.resolved_location == "Rohini, New Delhi"
    assert len(result2.candidates) == 1
    assert result2.candidates[0].name == "Delhi Dhaba"

    # 3. Typo in Area, resolved fuzzy
    prefs3 = UserPreferences(
        location="Indirnagar, Bangalore",
        budget=UserBudget.MEDIUM,
        cuisine="Any",
    )
    result3 = service.apply(prefs3)
    assert not result3.is_empty
    assert result3.resolved_location == "Indiranagar, Bangalore"
    assert len(result3.candidates) == 1
