"""CLI demo: python -m app.domain.filter"""

from __future__ import annotations

import json
import logging

from app.data.repository import RestaurantRepository
from app.domain.filter import FilterService
from app.domain.models import UserBudget, UserPreferences

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main() -> None:
    repo = RestaurantRepository.from_cache_or_dataset()
    service = FilterService(repo)

    print("\n=== Dataset hints ===")
    hints = service.get_dataset_hints()
    print(f"Cities: {', '.join(hints.cities[:5])}")
    print(f"Cuisines (sample): {', '.join(hints.cuisines[:8])}")

    prefs = UserPreferences(
        location="Bangalore",
        budget=UserBudget.MEDIUM,
        cuisine="Italian",
        min_rating=4.0,
        top_k=5,
    )
    print(f"\n=== Filter: {prefs.location} | {prefs.cuisine} | {prefs.budget.value} | rating>={prefs.min_rating} ===")
    result = service.apply(prefs)

    if result.is_empty:
        print(f"Empty: {result.message}")
        for s in result.suggestions:
            print(f"  - {s}")
        return

    print(f"Matched: {result.total_matched} | Returned: {len(result.candidates)} | Capped: {result.capped}")
    if result.message:
        print(result.message)
    for r in result.candidates[:5]:
        print(f"  - {r.name} | {r.cuisine} | {r.rating} | {r.budget_tier.value}")


if __name__ == "__main__":
    main()
