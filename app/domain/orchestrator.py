"""Orchestrator for restaurant recommendation flow (Phase 4)."""

from __future__ import annotations

import logging
from typing import Optional

from app.domain.filter import FilterService
from app.domain.models import ParseResult, UserPreferences
from app.domain.prompt import PromptBuilder
from app.llm.client import LLMClient
from app.llm.engine import RecommendationEngine
from app.llm.parser import LLMResponseParser

logger = logging.getLogger(__name__)


class RecommendationOrchestrator:
    """Orchestrates filter → prompt → LLM → parse flow."""

    def __init__(
        self,
        filter_service: FilterService,
        llm_client: Optional[LLMClient] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        parser: Optional[LLMResponseParser] = None,
    ) -> None:
        self._engine = RecommendationEngine(
            filter_service=filter_service,
            llm_client=llm_client,
            prompt_builder=prompt_builder,
            parser=parser,
        )

    def recommend(self, preferences: UserPreferences) -> ParseResult:
        """Run the end-to-end recommendation flow."""
        logger.info("Recommendation orchestration started for city=%s", preferences.location)
        return self._engine.recommend(preferences)
