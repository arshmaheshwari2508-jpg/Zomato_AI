"""Tests for LLM client (Phase 3)."""

import json

from app.domain.models import UserBudget, UserPreferences
from app.domain.prompt import PromptBuilder
from app.llm.client import MockLLMClient
from app.llm.parser import LLMResponseParser
from tests.conftest import sample_candidates


def test_mock_client_returns_valid_json(sample_candidates):
    prefs = UserPreferences(
        location="Bangalore",
        budget=UserBudget.MEDIUM,
        cuisine="Italian",
        top_k=2,
    )
    messages = PromptBuilder().build(sample_candidates, prefs)
    raw = MockLLMClient().complete(messages)
    data = json.loads(raw)
    assert "recommendations" in data
    assert len(data["recommendations"]) >= 1


def test_mock_client_integration_with_parser(sample_candidates):
    prefs = UserPreferences(
        location="Bangalore",
        budget=UserBudget.MEDIUM,
        cuisine="Italian",
        top_k=2,
    )
    messages = PromptBuilder().build(sample_candidates, prefs)
    raw = MockLLMClient().complete(messages)
    result = LLMResponseParser().parse(raw, sample_candidates, prefs)
    assert result.success
    assert len(result.recommendations) >= 1
