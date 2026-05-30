"""Deterministic restaurant filtering (Phase 2)."""

from __future__ import annotations

import logging
from difflib import get_close_matches

from app.data.repository import RestaurantRepository
from app.domain.models import (
    ANY_CUISINE_VALUES,
    BudgetTier,
    DatasetHints,
    FilterResult,
    Restaurant,
    UserBudget,
    UserPreferences,
)
from config.settings import settings

logger = logging.getLogger(__name__)

_BUDGET_ADJACENT: dict[UserBudget, list[str]] = {
    UserBudget.LOW: ["medium"],
    UserBudget.MEDIUM: ["low", "high"],
    UserBudget.HIGH: ["medium"],
}


class FilterService:
    """Apply structured filters over the restaurant repository."""

    def __init__(
        self,
        repository: RestaurantRepository,
        max_candidates: int | None = None,
    ) -> None:
        self._repository = repository
        self._max_candidates = max_candidates or settings.max_candidates

    def get_dataset_hints(self) -> DatasetHints:
        return DatasetHints(
            cities=self._repository.get_cities(),
            location_options=self._repository.get_location_options(),
            cuisines=self._repository.get_cuisines(),
            budget_tiers=[UserBudget.LOW.value, UserBudget.MEDIUM.value, UserBudget.HIGH.value],
        )

    def get_areas_for_city(self, city: str) -> list[str]:
        areas = set()
        for r in self._repository.get_all():
            if r.location.lower() == city.lower():
                area = r.metadata.get("area")
                if area:
                    areas.add(area)
                listed_area = r.metadata.get("listed_area")
                if listed_area:
                    areas.add(listed_area)
        return sorted(areas)

    def resolve_location(self, location: str) -> tuple[str | None, str | None, list[str]]:
        """
        Resolve user location to a canonical city and optional area/neighborhood.

        Returns (resolved_city, resolved_area, suggestions).
        """
        cities = self._repository.get_cities()
        if not cities:
            return None, None, []

        query = location.strip()
        
        # 1. Check if there is a comma separating area and city (e.g. "Indiranagar, Bangalore")
        if "," in query:
            parts = [p.strip() for p in query.split(",")]
            if len(parts) >= 2:
                area_part = parts[0]
                city_part = parts[1]
                
                # Resolve city
                resolved_city = None
                for city in cities:
                    if city.lower() == city_part.lower():
                        resolved_city = city
                        break
                
                if resolved_city:
                    # Resolve area within that city
                    areas = self.get_areas_for_city(resolved_city)
                    resolved_area = None
                    for area in areas:
                        if area.lower() == area_part.lower():
                            resolved_area = area
                            break
                    if resolved_area:
                        return resolved_city, resolved_area, []
                    
                    # Fuzzy match area
                    close_areas = get_close_matches(area_part, areas, n=3, cutoff=0.75)
                    if close_areas:
                        return resolved_city, close_areas[0], [f"{a}, {resolved_city}" for a in close_areas]
                    
                    return resolved_city, None, [f"{a}, {resolved_city}" for a in areas[:8]]

        # 2. Check if query matches a city name directly (e.g. "Bangalore")
        for city in cities:
            if city.lower() == query.lower():
                return city, None, []

        # 3. Check if query matches a known area directly
        for city in cities:
            areas = self.get_areas_for_city(city)
            for area in areas:
                if area.lower() == query.lower():
                    return city, area, []

        # 4. Try fuzzy matching city directly
        close_cities = get_close_matches(query, cities, n=3, cutoff=0.75)
        if close_cities:
            return close_cities[0], None, close_cities

        # 5. Try fuzzy matching combined "Area, City" options
        options = self._repository.get_location_options()
        close_options = get_close_matches(query, options, n=3, cutoff=0.6)
        if close_options:
            opt = close_options[0]
            if "," in opt:
                parts = opt.split(",")
                return parts[1].strip(), parts[0].strip(), close_options
            return opt, None, close_options

        return None, None, options[:8]

    def apply(self, preferences: UserPreferences) -> FilterResult:
        """Filter restaurants matching user preferences."""
        resolved_city, resolved_area, location_hints = self.resolve_location(preferences.location)

        if resolved_city is None:
            return FilterResult(
                candidates=[],
                total_matched=0,
                is_empty=True,
                message=(
                    f"No restaurants found in {preferences.location}. "
                    f"Try: {', '.join(location_hints[:5])}."
                ),
                suggestions=[
                    f"Choose a listed location: {', '.join(location_hints[:5])}",
                ],
                location_suggestions=location_hints,
                preferences=preferences,
            )

        pool = self._repository.get_by_city(resolved_city)
        
        # Area filter
        if resolved_area:
            pool = [
                r for r in pool
                if (r.metadata.get("area") and r.metadata.get("area").lower() == resolved_area.lower())
                or (r.metadata.get("listed_area") and r.metadata.get("listed_area").lower() == resolved_area.lower())
            ]

        pool = self._filter_by_rating(pool, preferences.min_rating)
        pool = self._filter_by_cuisine(pool, preferences.cuisine)
        pool = self._filter_by_budget(pool, preferences.to_budget_tier())

        total_matched = len(pool)
        pool = self._sort_by_rating(pool)
        capped = total_matched > self._max_candidates
        candidates = pool[: self._max_candidates]

        resolved_name = f"{resolved_area}, {resolved_city}" if resolved_area else resolved_city

        if not candidates:
            return FilterResult(
                candidates=[],
                total_matched=0,
                is_empty=True,
                message=self._empty_message(resolved_name, preferences),
                suggestions=self._empty_suggestions(resolved_name, preferences),
                resolved_location=resolved_name,
                preferences=preferences,
            )

        message = None
        if total_matched < preferences.top_k:
            message = f"Showing all {total_matched} matches."

        logger.info(
            "Filter applied: location=%s matched=%d returned=%d capped=%s",
            resolved_name,
            total_matched,
            len(candidates),
            capped,
        )

        return FilterResult(
            candidates=candidates,
            total_matched=total_matched,
            capped=capped,
            is_empty=False,
            message=message,
            resolved_location=resolved_name,
            location_suggestions=location_hints if location_hints and location_hints[0] != resolved_name else [],
            preferences=preferences,
        )

    @staticmethod
    def _filter_by_rating(restaurants: list[Restaurant], min_rating: float) -> list[Restaurant]:
        return [r for r in restaurants if r.rating >= min_rating]

    @staticmethod
    def _filter_by_cuisine(restaurants: list[Restaurant], cuisine: str) -> list[Restaurant]:
        query = cuisine.strip().lower()
        if query in ANY_CUISINE_VALUES:
            return restaurants
        return [r for r in restaurants if FilterService._cuisine_matches(r.cuisine, query)]

    @staticmethod
    def _cuisine_matches(restaurant_cuisine: str, query: str) -> bool:
        cuisine_lower = restaurant_cuisine.lower()
        if query in cuisine_lower:
            return True
        for token in restaurant_cuisine.split(","):
            token = token.strip().lower()
            if token == query:
                return True
            if len(query) >= 3 and token.startswith(query):
                return True
        return False

    @staticmethod
    def _filter_by_budget(restaurants: list[Restaurant], tier: BudgetTier) -> list[Restaurant]:
        return [
            r
            for r in restaurants
            if r.budget_tier == tier or r.budget_tier == BudgetTier.UNKNOWN
        ]

    @staticmethod
    def _sort_by_rating(restaurants: list[Restaurant]) -> list[Restaurant]:
        return sorted(restaurants, key=lambda r: (-r.rating, r.name.lower()))

    def _empty_message(self, city: str, preferences: UserPreferences) -> str:
        parts = [f"No restaurants match your criteria in {city}."]
        if preferences.cuisine_filter_active:
            parts.append(f"No {preferences.cuisine} options found with the current filters.")
        return " ".join(parts)

    def _empty_suggestions(self, city: str, preferences: UserPreferences) -> list[str]:
        suggestions: list[str] = []

        if preferences.min_rating > 0:
            suggestions.append(
                f"Lower minimum rating to {max(0.0, preferences.min_rating - 0.5):.1f}"
            )

        if preferences.cuisine_filter_active:
            city_cuisines = self._repository.get_cuisines()
            suggestions.append(
                f"Try another cuisine available in {city}, e.g. {', '.join(city_cuisines[:4])}"
            )
        else:
            suggestions.append("Specify a cuisine or use 'Any' to broaden results")

        for alt in _BUDGET_ADJACENT.get(preferences.budget, []):
            suggestions.append(f"Try budget tier: {alt}")

        suggestions.append("Relax one filter at a time for more results")
        return suggestions
