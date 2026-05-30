"""Tests for PromptBuilder (Phase 3)."""

import json

from app.domain.models import UserBudget, UserPreferences
from app.domain.prompt import PromptBuilder, SYSTEM_PROMPT
from tests.conftest import sample_candidates


def test_prompt_build_structure(sample_candidates):
    prefs = UserPreferences(
        location="Bangalore",
        budget=UserBudget.MEDIUM,
        cuisine="Italian",
        min_rating=4.0,
        top_k=3,
        additional_preferences=["family-friendly"],
    )
    builder = PromptBuilder()
    messages = builder.build(sample_candidates, prefs)

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "ONLY" in SYSTEM_PROMPT or "only" in messages[0]["content"].lower()
    assert "restaurant_id" in messages[1]["content"]
    assert "abc111" in messages[1]["content"]
    assert "family-friendly" in messages[1]["content"]
    assert "top 3" in messages[1]["content"].lower()


def test_prompt_snapshot_stable(sample_candidates):
    """Snapshot-style assertion for stable prompt structure."""
    prefs = UserPreferences(
        location="Bangalore",
        budget=UserBudget.MEDIUM,
        cuisine="Italian",
        min_rating=4.0,
        top_k=2,
    )
    messages = PromptBuilder().build(sample_candidates, prefs)
    user = messages[1]["content"]

    assert user.startswith("User preferences:")
    assert '"location": "Bangalore"' in user
    assert '"budget": "medium"' in user
    assert '"cuisine": "Italian"' in user
    assert "Candidate restaurants (2)" in user

    # Candidate JSON is parseable
    start = user.index("[", user.index("Candidate restaurants"))
    end = user.index("]", start) + 1
    candidates = json.loads(user[start:end])
    assert len(candidates) == 2
    assert candidates[0]["restaurant_id"] == "abc111"


def test_prompt_repair_includes_invalid_response(sample_candidates):
    prefs = UserPreferences(location="Bangalore", budget=UserBudget.LOW, cuisine="Any")
    messages = PromptBuilder().build_repair(sample_candidates, prefs, "not json")
    assert messages[-1]["role"] == "user"
    assert "corrected json" in messages[-1]["content"].lower()
