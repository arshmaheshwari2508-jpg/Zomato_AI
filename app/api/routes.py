"""API endpoints for restaurant recommendations (Phase 4)."""

from __future__ import annotations

import logging
from typing import Any
from fastapi import APIRouter, HTTPException, Request

from app.domain.filter import FilterService
from app.domain.models import DatasetHints, ParseResult, UserPreferences
from app.domain.orchestrator import RecommendationOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def health_check(request: Request) -> dict[str, Any]:
    """Liveness probe and dataset check."""
    repo = getattr(request.app.state, "repository", None)
    is_loaded = repo is not None and repo.count > 0
    return {
        "status": "healthy" if is_loaded else "unhealthy",
        "dataset_loaded": is_loaded,
        "total_restaurants": repo.count if is_loaded else 0,
    }


@router.get("/dataset/stats", response_model=DatasetHints)
def get_dataset_stats(request: Request) -> DatasetHints:
    """Retrieve hints (valid cities, cuisines, budget tiers) from the dataset."""
    repo = getattr(request.app.state, "repository", None)
    if repo is None:
        raise HTTPException(
            status_code=503,
            detail="System is starting up. Dataset repository is not yet initialized.",
        )
    
    filter_service = FilterService(repo)
    return filter_service.get_dataset_hints()


@router.post("/recommendations", response_model=ParseResult)
def get_recommendations(request: Request, preferences: UserPreferences) -> ParseResult:
    """Get ranked and explained restaurant recommendations based on user preferences."""
    repo = getattr(request.app.state, "repository", None)
    if repo is None:
        raise HTTPException(
            status_code=503,
            detail="System is starting up. Dataset repository is not yet initialized.",
        )

    filter_service = FilterService(repo)
    llm_client = getattr(request.app.state, "llm_client", None)
    
    orchestrator = RecommendationOrchestrator(
        filter_service=filter_service,
        llm_client=llm_client,
    )
    
    try:
        return orchestrator.recommend(preferences)
    except Exception as exc:
        logger.error("Failed to generate recommendations: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while generating recommendations: {exc}",
        )
