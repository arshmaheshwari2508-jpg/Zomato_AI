"""Recommendation engine: filter → prompt → LLM → parse (Phase 3)."""

from __future__ import annotations

import logging
from typing import Optional

from app.domain.filter import FilterService
from app.domain.models import ParseResult, UserPreferences
from app.domain.prompt import PromptBuilder
from app.llm.client import LLMClient, LLMError, get_llm_client
from app.llm.parser import LLMResponseParser

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """End-to-end recommendation without HTTP layer (Phase 3)."""

    def __init__(
        self,
        filter_service: FilterService,
        llm_client: Optional[LLMClient] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        parser: Optional[LLMResponseParser] = None,
    ) -> None:
        self._filter = filter_service
        self._llm = llm_client or get_llm_client()
        self._prompt = prompt_builder or PromptBuilder()
        self._parser = parser or LLMResponseParser()

    def recommend(self, preferences: UserPreferences) -> ParseResult:
        filter_result = self._filter.apply(preferences)

        if not filter_result.should_call_llm:
            return ParseResult(
                success=True,
                recommendations=[],
                summary=filter_result.message,
                error=None,
            )

        candidates = filter_result.candidates
        messages = self._prompt.build(candidates, preferences)

        try:
            raw = self._llm.complete(messages)
        except LLMError as exc:
            logger.error("LLM call failed: %s", exc)
            return self._parser.fallback(candidates, preferences, error=str(exc))

        result = self._parser.parse(raw, candidates, preferences)

        if not result.success:
            repair_messages = self._prompt.build_repair(candidates, preferences, raw)
            try:
                repaired = self._llm.complete(repair_messages)
                result = self._parser.parse(repaired, candidates, preferences)
            except LLMError:
                pass

        return result
