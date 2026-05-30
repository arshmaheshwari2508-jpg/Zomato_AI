from __future__ import annotations

import re
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from config.settings import settings


class BudgetTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class UserBudget(str, Enum):
    """Budget values accepted from user input."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


ANY_CUISINE_VALUES = frozenset({"any", "all", ""})


class Restaurant(BaseModel):
    id: str
    name: str
    location: str
    cuisine: str
    rating: float = Field(ge=0.0, le=5.0)
    cost_for_two: Optional[float] = None
    budget_tier: BudgetTier
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def estimated_cost(self) -> str:
        if self.cost_for_two is not None:
            return f"₹{int(self.cost_for_two)} for two"
        return "Price not available"


class UserPreferences(BaseModel):
    """Validated user dining preferences (Phase 2)."""

    location: str = Field(..., min_length=1, description="City name, e.g. Bangalore")
    budget: UserBudget
    cuisine: str = Field(default="Any", description='Cuisine or "Any" to skip cuisine filter')
    min_rating: float = Field(default=0.0, ge=0.0, le=5.0)
    additional_preferences: list[str] = Field(default_factory=list)
    top_k: int = Field(default_factory=lambda: settings.default_top_k)

    model_config = {"extra": "ignore"}

    @field_validator("location")
    @classmethod
    def strip_location(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Location is required.")
        return text

    @field_validator("cuisine")
    @classmethod
    def strip_cuisine(cls, value: str) -> str:
        return value.strip() if value else "Any"

    @field_validator("min_rating", mode="before")
    @classmethod
    def coerce_rating(cls, value: Any) -> float:
        if value is None:
            return 0.0
        return float(value)

    @field_validator("top_k", mode="before")
    @classmethod
    def coerce_top_k(cls, value: Any) -> int:
        if value is None:
            return settings.default_top_k
        return int(float(value))

    @field_validator("additional_preferences")
    @classmethod
    def normalize_additional_preferences(cls, values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for raw in values:
            text = re.sub(r"[\x00-\x1f\x7f]", "", str(raw).strip())
            text = re.sub(r"<[^>]+>", "", text)
            if not text:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(text[:500])
        return result

    @model_validator(mode="after")
    def clamp_top_k(self) -> "UserPreferences":
        if self.top_k < 1:
            raise ValueError("Please request at least 1 recommendation.")
        if self.top_k > 10:
            object.__setattr__(self, "top_k", 10)
        return self

    @property
    def cuisine_filter_active(self) -> bool:
        return self.cuisine.strip().lower() not in ANY_CUISINE_VALUES

    def to_budget_tier(self) -> BudgetTier:
        return BudgetTier(self.budget.value)


class DatasetHints(BaseModel):
    """Valid values from the loaded dataset for UI dropdowns."""

    cities: list[str] = Field(default_factory=list)
    location_options: list[str] = Field(default_factory=list)
    cuisines: list[str] = Field(default_factory=list)
    budget_tiers: list[str] = Field(default_factory=list)


class FilterResult(BaseModel):
    """Output of deterministic filtering before LLM (Phase 2)."""

    candidates: list[Restaurant] = Field(default_factory=list)
    total_matched: int = 0
    capped: bool = False
    is_empty: bool = False
    message: Optional[str] = None
    suggestions: list[str] = Field(default_factory=list)
    resolved_location: Optional[str] = None
    location_suggestions: list[str] = Field(default_factory=list)
    preferences: Optional[UserPreferences] = None

    @property
    def should_call_llm(self) -> bool:
        return not self.is_empty and len(self.candidates) > 0


class LLMRecommendationItem(BaseModel):
    """Single ranked item from LLM JSON output."""

    restaurant_id: str
    rank: int = Field(ge=1)
    explanation: str = ""


class LLMResponseSchema(BaseModel):
    """Expected JSON shape from the LLM."""

    summary: Optional[str] = None
    recommendations: list[LLMRecommendationItem] = Field(default_factory=list)


class Recommendation(BaseModel):
    """Final recommendation merged with authoritative dataset fields."""

    restaurant_id: str
    name: str
    cuisine: str
    rating: float
    estimated_cost: str
    location: str
    rank: int
    explanation: str
    budget_tier: BudgetTier
    metadata: dict[str, Any] = Field(default_factory=dict)



class ParseResult(BaseModel):
    """Output of LLM response parsing (Phase 3)."""

    success: bool
    recommendations: list[Recommendation] = Field(default_factory=list)
    summary: Optional[str] = None
    dropped_ids: list[str] = Field(default_factory=list)
    error: Optional[str] = None
    used_fallback: bool = False
