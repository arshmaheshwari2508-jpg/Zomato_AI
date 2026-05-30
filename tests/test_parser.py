"""Tests for LLM response parser (Phase 3)."""

import json

import pytest

from app.llm.parser import LLMResponseParser, extract_json
from tests.conftest import FIXTURES_DIR, sample_candidates, sample_preferences


def test_extract_json_plain(fixtures_dir):
    raw = (fixtures_dir / "llm_valid_response.json").read_text()
    data = extract_json(raw)
    assert "recommendations" in data
    assert len(data["recommendations"]) == 2


def test_extract_json_fenced(fixtures_dir):
    raw = (fixtures_dir / "llm_fenced_response.txt").read_text()
    data = extract_json(raw)
    assert data["recommendations"][0]["restaurant_id"] == "abc111"


def test_extract_json_raises_on_garbage():
    with pytest.raises((json.JSONDecodeError, ValueError)):
        extract_json("Sorry, I cannot help with that.")


def test_parse_valid_response(sample_candidates, sample_preferences, fixtures_dir):
    raw = (fixtures_dir / "llm_valid_response.json").read_text()
    result = LLMResponseParser().parse(raw, sample_candidates, sample_preferences)

    assert result.success
    assert not result.used_fallback
    assert len(result.recommendations) == 2
    assert result.recommendations[0].restaurant_id == "abc111"
    assert result.recommendations[0].name == "Trattoria"
    assert result.recommendations[0].rating == 4.5
    assert result.recommendations[0].estimated_cost == "₹800 for two"
    assert "rating" in result.recommendations[0].explanation.lower()


def test_parse_drops_hallucinated_ids(sample_candidates, sample_preferences, fixtures_dir):
    raw = (fixtures_dir / "llm_with_hallucination.json").read_text()
    prefs = sample_preferences.model_copy(update={"top_k": 2})
    result = LLMResponseParser().parse(raw, sample_candidates, prefs)

    assert result.success
    assert "fake999" in result.dropped_ids
    ids = {r.restaurant_id for r in result.recommendations}
    assert "fake999" not in ids
    assert all(rid in {"abc111", "abc222"} for rid in ids)


def test_parse_malformed_uses_fallback(sample_candidates, sample_preferences):
    result = LLMResponseParser().parse("not valid json", sample_candidates, sample_preferences)

    assert not result.success
    assert result.used_fallback
    assert len(result.recommendations) == 2
    assert result.recommendations[0].name == "Trattoria"
    assert result.error is not None


def test_parse_backfills_when_llm_returns_one(sample_candidates, sample_preferences):
    raw = json.dumps(
        {
            "summary": "One pick",
            "recommendations": [
                {"restaurant_id": "abc222", "rank": 1, "explanation": "Good pasta."}
            ],
        }
    )
    result = LLMResponseParser().parse(raw, sample_candidates, sample_preferences)
    assert len(result.recommendations) == 2
    assert {r.restaurant_id for r in result.recommendations} == {"abc222", "abc111"}


def test_all_output_ids_exist_in_candidates(sample_candidates, sample_preferences, fixtures_dir):
    raw = (fixtures_dir / "llm_valid_response.json").read_text()
    result = LLMResponseParser().parse(raw, sample_candidates, sample_preferences)
    valid = {c.id for c in sample_candidates}
    for rec in result.recommendations:
        assert rec.restaurant_id in valid
