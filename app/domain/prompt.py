"""LLM prompt construction (Phase 3)."""

from __future__ import annotations

import json
from typing import Any

from app.domain.models import Restaurant, UserPreferences

SYSTEM_PROMPT = """You are a restaurant recommendation assistant for Zomato-style dining discovery.

Rules:
1. Recommend ONLY restaurants from the candidate list provided by the user message.
2. Do NOT invent restaurants, IDs, ratings, or prices.
3. Rank by fit: rating, budget match, cuisine match, then additional preferences.
4. Return ONLY valid JSON (no markdown) matching this schema:
{
  "summary": "One sentence overview of the picks",
  "recommendations": [
    {
      "restaurant_id": "<id from list>",
      "rank": 1,
      "explanation": "Why this fits the user's preferences"
    }
  ]
}
5. Include at most the requested top_k recommendations.
6. Each restaurant_id must exactly match an id from the candidate list."""


REPAIR_PROMPT = """The previous response was not valid JSON or did not match the schema.
Return ONLY corrected JSON with keys: summary, recommendations.
Each recommendation needs: restaurant_id, rank, explanation.
Use only restaurant IDs from the candidate list."""


class PromptBuilder:
    """Build chat messages for LLM recommendation requests."""

    def build(
        self,
        candidates: list[Restaurant],
        preferences: UserPreferences,
    ) -> list[dict[str, str]]:
        if not candidates:
            raise ValueError("Cannot build prompt with zero candidates")

        user_content = self._build_user_content(candidates, preferences)
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def build_repair(
        self,
        candidates: list[Restaurant],
        preferences: UserPreferences,
        invalid_response: str,
    ) -> list[dict[str, str]]:
        messages = self.build(candidates, preferences)
        messages.append(
            {
                "role": "assistant",
                "content": invalid_response[:2000],
            }
        )
        messages.append({"role": "user", "content": REPAIR_PROMPT})
        return messages

    def _build_user_content(
        self,
        candidates: list[Restaurant],
        preferences: UserPreferences,
    ) -> str:
        prefs_payload: dict[str, Any] = {
            "location": preferences.location,
            "budget": preferences.budget.value,
            "cuisine": preferences.cuisine,
            "min_rating": preferences.min_rating,
            "additional_preferences": preferences.additional_preferences,
            "top_k": preferences.top_k,
        }

        compact_candidates = [self._compact_restaurant(r) for r in candidates]

        return (
            "User preferences:\n"
            f"{json.dumps(prefs_payload, indent=2)}\n\n"
            f"Candidate restaurants ({len(compact_candidates)}). "
            "Recommend only from this list:\n"
            f"{json.dumps(compact_candidates, indent=2)}\n\n"
            f"Return the top {preferences.top_k} recommendations as JSON."
        )

    @staticmethod
    def _compact_restaurant(restaurant: Restaurant) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "restaurant_id": restaurant.id,
            "name": restaurant.name[:200],
            "location": restaurant.location,
            "cuisine": restaurant.cuisine[:200],
            "rating": restaurant.rating,
            "estimated_cost": restaurant.estimated_cost,
            "budget_tier": restaurant.budget_tier.value,
        }
        if restaurant.metadata.get("area"):
            payload["area"] = str(restaurant.metadata["area"])[:100]
        if restaurant.metadata.get("rest_type"):
            payload["rest_type"] = str(restaurant.metadata["rest_type"])[:100]
        return payload
