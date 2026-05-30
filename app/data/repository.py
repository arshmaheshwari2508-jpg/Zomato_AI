"""In-memory restaurant data access."""

from __future__ import annotations

import logging
from pathlib import Path

from app.data.loader import load_raw_dataset
from app.domain.models import BudgetTier, Restaurant
from config.settings import settings

logger = logging.getLogger(__name__)


class RestaurantRepository:
    """Read-only in-memory store of normalized restaurants."""

    def __init__(self, restaurants: list[Restaurant] | None = None) -> None:
        self._restaurants: list[Restaurant] = restaurants or []
        self._by_id: dict[str, Restaurant] = {r.id: r for r in self._restaurants}

    @classmethod
    def from_cache_or_dataset(
        cls,
        cache_path: Path | None = None,
        force_refresh: bool | None = None,
    ) -> "RestaurantRepository":
        """Build repository by loading HF dataset (or cache) and preprocessing."""
        from app.data.preprocessor import preprocess_dataset
        path = cache_path or settings.data_cache_path
        refresh = force_refresh if force_refresh is not None else settings.force_refresh_dataset
        df = load_raw_dataset(cache_path=path, force_refresh=refresh)
        restaurants = preprocess_dataset(df)
        return cls(restaurants)

    def load(self, restaurants: list[Restaurant]) -> None:
        self._restaurants = restaurants
        self._by_id = {r.id: r for r in restaurants}

    @property
    def count(self) -> int:
        return len(self._restaurants)

    def get_all(self) -> list[Restaurant]:
        return list(self._restaurants)

    def get_by_id(self, restaurant_id: str) -> Restaurant | None:
        return self._by_id.get(restaurant_id)

    def get_by_city(self, city: str) -> list[Restaurant]:
        normalized = city.strip().title()
        return [r for r in self._restaurants if r.location.lower() == normalized.lower()]

    def get_cities(self) -> list[str]:
        return sorted({r.location for r in self._restaurants})

    def get_areas(self) -> list[str]:
        areas = set()
        for r in self._restaurants:
            area = r.metadata.get("area")
            if area:
                areas.add(area)
            listed_area = r.metadata.get("listed_area")
            if listed_area:
                areas.add(listed_area)
        return sorted(areas)

    def get_location_options(self) -> list[str]:
        """
        Return list of combined location options like 'Area, City' and also city names alone.
        For example: 'Indiranagar, Bangalore', 'BTM, Bangalore', 'Bangalore'.
        """
        options = set()
        for r in self._restaurants:
            city = r.location
            # Add city itself
            options.add(city)
            
            # Add specific areas combined with city
            area = r.metadata.get("area")
            if area:
                options.add(f"{area}, {city}")
            listed_area = r.metadata.get("listed_area")
            if listed_area:
                options.add(f"{listed_area}, {city}")
        return sorted(options)

    def get_cuisines(self) -> list[str]:
        tokens: set[str] = set()
        for r in self._restaurants:
            for part in r.cuisine.split(","):
                token = part.strip()
                if token and token.lower() != "unknown":
                    tokens.add(token)
        return sorted(tokens)

    def get_by_budget_tier(self, tier: BudgetTier) -> list[Restaurant]:
        return [r for r in self._restaurants if r.budget_tier == tier]
