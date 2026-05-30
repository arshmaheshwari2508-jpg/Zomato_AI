"""Parse and validate LLM recommendation responses (Phase 3)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from pydantic import ValidationError

from app.domain.models import (
    LLMResponseSchema,
    ParseResult,
    Recommendation,
    Restaurant,
    UserPreferences,
)

logger = logging.getLogger(__name__)

DEFAULT_EXPLANATION = "Matches your preferences based on rating, cuisine, and budget."


class LLMResponseParser:
    """Extract JSON from LLM output, validate IDs, merge with dataset records."""

    def parse(
        self,
        raw_response: str,
        candidates: list[Restaurant],
        preferences: UserPreferences,
    ) -> ParseResult:
        try:
            payload = extract_json(raw_response)
            schema = LLMResponseSchema.model_validate(payload)
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            logger.warning("LLM parse failed: %s", exc)
            return self.fallback(candidates, preferences, error=str(exc))

        candidate_map = {r.id: r for r in candidates}
        valid_ids = set(candidate_map.keys())

        recommendations: list[Recommendation] = []
        dropped_ids: list[str] = []
        seen_ids: set[str] = set()

        sorted_items = sorted(schema.recommendations, key=lambda x: x.rank)
        for item in sorted_items:
            if item.restaurant_id not in valid_ids:
                dropped_ids.append(item.restaurant_id)
                logger.warning("Dropped hallucinated restaurant_id: %s", item.restaurant_id)
                continue
            if item.restaurant_id in seen_ids:
                continue
            seen_ids.add(item.restaurant_id)
            restaurant = candidate_map[item.restaurant_id]
            explanation = item.explanation.strip() or DEFAULT_EXPLANATION
            recommendations.append(self._merge(restaurant, item.rank, explanation))

        # Re-number ranks sequentially
        for idx, rec in enumerate(recommendations, start=1):
            recommendations[idx - 1] = rec.model_copy(update={"rank": idx})

        # Backfill if fewer than top_k
        if len(recommendations) < preferences.top_k:
            recommendations = self._backfill(
                recommendations,
                candidates,
                preferences.top_k,
                seen_ids,
            )

        recommendations = recommendations[: preferences.top_k]

        if not recommendations:
            return self.fallback(
                candidates,
                preferences,
                error="No valid recommendations after ID validation",
                dropped_ids=dropped_ids,
            )

        return ParseResult(
            success=True,
            recommendations=recommendations,
            summary=schema.summary,
            dropped_ids=dropped_ids,
        )

    def _merge(self, restaurant: Restaurant, rank: int, explanation: str) -> Recommendation:
        return Recommendation(
            restaurant_id=restaurant.id,
            name=restaurant.name,
            cuisine=restaurant.cuisine,
            rating=restaurant.rating,
            estimated_cost=restaurant.estimated_cost,
            location=restaurant.location,
            rank=rank,
            explanation=explanation,
            budget_tier=restaurant.budget_tier,
            metadata=restaurant.metadata,
        )


    def _backfill(
        self,
        current: list[Recommendation],
        candidates: list[Restaurant],
        top_k: int,
        seen_ids: set[str],
    ) -> list[Recommendation]:
        result = list(current)
        ranked_candidates = sorted(candidates, key=lambda r: (-r.rating, r.name.lower()))
        next_rank = len(result) + 1
        for restaurant in ranked_candidates:
            if restaurant.id in seen_ids:
                continue
            result.append(
                self._merge(
                    restaurant,
                    next_rank,
                    DEFAULT_EXPLANATION,
                )
            )
            seen_ids.add(restaurant.id)
            next_rank += 1
            if len(result) >= top_k:
                break
        return result

    def fallback(
        self,
        candidates: list[Restaurant],
        preferences: UserPreferences,
        error: str,
        dropped_ids: Optional[list[str]] = None,
    ) -> ParseResult:
        sorted_candidates = sorted(candidates, key=lambda r: (-r.rating, r.name.lower()))
        recommendations = [
            self._merge(r, rank, DEFAULT_EXPLANATION)
            for rank, r in enumerate(sorted_candidates[: preferences.top_k], start=1)
        ]
        return ParseResult(
            success=False,
            recommendations=recommendations,
            summary="Showing top-rated matches (AI response could not be parsed).",
            dropped_ids=dropped_ids or [],
            error=error,
            used_fallback=True,
        )


def extract_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from raw LLM text (plain, fenced, or embedded)."""
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Empty LLM response")

    # Direct parse
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # Markdown code fence
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned, re.IGNORECASE)
    if fence_match:
        return _parse_json_object(fence_match.group(1).strip())

    # First { ... } block
    brace_start = cleaned.find("{")
    brace_end = cleaned.rfind("}")
    if brace_start >= 0 and brace_end > brace_start:
        return _parse_json_object(cleaned[brace_start : brace_end + 1])

    raise json.JSONDecodeError("No JSON object found", cleaned, 0)


def _parse_json_object(fragment: str) -> dict[str, Any]:
    data = json.loads(fragment)
    if not isinstance(data, dict):
        raise ValueError("Expected JSON object")
    return data
