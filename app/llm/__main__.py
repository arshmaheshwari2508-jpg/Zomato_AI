"""CLI smoke test: python -m app.llm"""

from __future__ import annotations

import argparse
import logging

from app.data.repository import RestaurantRepository
from app.domain.filter import FilterService
from app.domain.models import UserBudget, UserPreferences
from app.llm.client import get_llm_client
from app.llm.engine import RecommendationEngine
from config.settings import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 3 LLM recommendation smoke test")
    parser.add_argument("--mock", action="store_true", help="Use mock LLM (no API key)")
    parser.add_argument("--location", default="Bangalore")
    parser.add_argument("--cuisine", default="Italian")
    parser.add_argument("--budget", default="medium", choices=["low", "medium", "high"])
    parser.add_argument("--min-rating", type=float, default=4.0)
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    api_key = (settings.llm_api_key or settings.groq_api_key).strip()
    # Real Groq keys are ~50+ chars; placeholders like gsk_...9qux are ~11
    use_mock = args.mock or not api_key or len(api_key) < 20

    repo = RestaurantRepository.from_cache_or_dataset()
    engine = RecommendationEngine(
        filter_service=FilterService(repo),
        llm_client=get_llm_client(use_mock=use_mock),
    )

    prefs = UserPreferences(
        location=args.location,
        budget=UserBudget(args.budget),
        cuisine=args.cuisine,
        min_rating=args.min_rating,
        top_k=args.top_k,
    )

    print(f"\nMode: {'mock' if use_mock else 'groq'}")
    print(f"Preferences: {prefs.location} | {prefs.cuisine} | {prefs.budget.value} | rating>={prefs.min_rating}\n")

    result = engine.recommend(prefs)

    if result.summary:
        print(f"Summary: {result.summary}\n")

    if not result.recommendations:
        print("No recommendations.")
        if result.error:
            print(f"Error: {result.error}")
        return

    for rec in result.recommendations:
        print(f"#{rec.rank} {rec.name}")
        print(f"   {rec.cuisine} | {rec.rating} | {rec.estimated_cost}")
        print(f"   {rec.explanation}\n")

    if result.used_fallback:
        print("(Used rating fallback)")
    if result.dropped_ids:
        print(f"Dropped hallucinated IDs: {result.dropped_ids}")


if __name__ == "__main__":
    main()
