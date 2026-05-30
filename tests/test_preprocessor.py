"""Unit tests for data preprocessor (Phase 1)."""

import pandas as pd
import pytest

from app.data.preprocessor import (
    COL_ADDRESS,
    COL_COST,
    COL_CUISINES,
    COL_NAME,
    COL_RATE,
    assign_budget_tiers,
    preprocess_dataframe,
    _parse_cost,
    _parse_rating,
    _normalize_city,
    _city_from_address,
)
from app.domain.models import BudgetTier


def test_parse_rating_from_fraction():
    assert _parse_rating("4.1/5") == pytest.approx(4.1)
    assert _parse_rating("NEW") == 0.0
    assert _parse_rating(None) == 0.0


def test_parse_cost_formats():
    assert _parse_cost("800") == 800.0
    assert _parse_cost("₹1,200") == 1200.0
    assert _parse_cost("300-500") == 400.0
    assert _parse_cost(None) is None
    assert _parse_cost("-") is None


def test_normalize_city_aliases():
    assert _normalize_city("bengaluru") == "Bangalore"
    assert _normalize_city("Bangalore") == "Bangalore"
    assert _normalize_city("") is None


def test_city_from_address():
    assert _city_from_address("942, 21st Main Road, Banashankari, Bangalore") == "Bangalore"
    assert _city_from_address("Some place, New Delhi") == "New Delhi"


def test_assign_budget_tiers_percentiles():
    costs = pd.Series([100, 200, 300, 400, 500, 600])
    tiers = assign_budget_tiers(costs)
    assert set(tiers.unique()) <= {BudgetTier.LOW.value, BudgetTier.MEDIUM.value, BudgetTier.HIGH.value}
    assert tiers.iloc[costs.idxmin()] == BudgetTier.LOW.value
    assert tiers.iloc[costs.idxmax()] == BudgetTier.HIGH.value


def test_preprocess_drops_missing_name_and_city():
    df = pd.DataFrame(
        [
            {COL_NAME: "A", COL_ADDRESS: "1 Road, Bangalore", COL_CUISINES: "Italian", COL_RATE: "4.0/5", COL_COST: "500"},
            {COL_NAME: None, COL_ADDRESS: "2 Road, Bangalore", COL_CUISINES: "Chinese", COL_RATE: "3.5/5", COL_COST: "300"},
            {COL_NAME: "B", COL_ADDRESS: "Invalid address only", COL_CUISINES: "Chinese", COL_RATE: "4.5/5", COL_COST: "600"},
        ]
    )
    restaurants, stats = preprocess_dataframe(df)
    assert len(restaurants) == 1
    assert restaurants[0].name == "A"
    assert stats["dropped_missing_name"] == 1
    assert stats["dropped_missing_city"] == 1


def test_preprocess_all_budget_tiers_valid():
    df = pd.DataFrame(
        [
            {COL_NAME: f"R{i}", COL_ADDRESS: "Street, Bangalore", COL_CUISINES: "North Indian", COL_RATE: "4.0/5", COL_COST: str(c)}
            for i, c in enumerate([100, 400, 800])
        ]
    )
    restaurants, _ = preprocess_dataframe(df)
    tiers = {r.budget_tier for r in restaurants}
    assert tiers <= {BudgetTier.LOW, BudgetTier.MEDIUM, BudgetTier.HIGH}


def test_preprocess_missing_cost_defaults_to_medium():
    df = pd.DataFrame(
        [{COL_NAME: "NoCost", COL_ADDRESS: "Connaught Place, New Delhi", COL_CUISINES: "Cafe", COL_RATE: "3.8/5", COL_COST: None}]
    )
    restaurants, _ = preprocess_dataframe(df)
    assert len(restaurants) == 1
    assert restaurants[0].budget_tier == BudgetTier.MEDIUM
    assert restaurants[0].cost_for_two is None


def test_preprocess_generates_stable_ids():
    df = pd.DataFrame(
        [
            {COL_NAME: "Jalsa", COL_ADDRESS: "Banashankari, Bangalore", COL_CUISINES: "North Indian", COL_RATE: "4.1/5", COL_COST: "800"},
            {COL_NAME: "Jalsa", COL_ADDRESS: "Banashankari, Bangalore", COL_CUISINES: "North Indian", COL_RATE: "4.1/5", COL_COST: "800"},
        ]
    )
    restaurants, stats = preprocess_dataframe(df)
    assert len(restaurants) == 1
    assert stats["dropped_duplicates"] == 1


def test_preprocess_clamps_rating():
    df = pd.DataFrame(
        [{COL_NAME: "High", COL_ADDRESS: "Bandra, Mumbai", COL_CUISINES: "Thai", COL_RATE: "9.5", COL_COST: "500"}]
    )
    restaurants, _ = preprocess_dataframe(df)
    assert restaurants[0].rating <= 5.0
