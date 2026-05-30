"""Shared pytest fixtures."""

from pathlib import Path

import pytest

from app.domain.models import BudgetTier, Restaurant, UserBudget, UserPreferences

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_candidates() -> list[Restaurant]:
    return [
        Restaurant(
            id="abc111",
            name="Trattoria",
            location="Bangalore",
            cuisine="Italian, Pizza",
            rating=4.5,
            cost_for_two=800.0,
            budget_tier=BudgetTier.MEDIUM,
        ),
        Restaurant(
            id="abc222",
            name="Pasta House",
            location="Bangalore",
            cuisine="Italian",
            rating=4.2,
            cost_for_two=600.0,
            budget_tier=BudgetTier.MEDIUM,
        ),
    ]


@pytest.fixture
def sample_preferences() -> UserPreferences:
    return UserPreferences(
        location="Bangalore",
        budget=UserBudget.MEDIUM,
        cuisine="Italian",
        min_rating=4.0,
        top_k=2,
    )


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR
