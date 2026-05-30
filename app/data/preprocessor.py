"""Clean and normalize raw Zomato dataset rows into canonical Restaurant records."""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

import pandas as pd

from app.domain.models import BudgetTier, Restaurant

logger = logging.getLogger(__name__)

# Raw Hugging Face column names
COL_NAME = "name"
COL_CUISINES = "cuisines"
COL_RATE = "rate"
COL_COST = "approx_cost(for two people)"
COL_LISTED_AREA = "listed_in(city)"
COL_AREA = "location"
COL_ADDRESS = "address"
COL_VOTES = "votes"
COL_REST_TYPE = "rest_type"
COL_ONLINE_ORDER = "online_order"
COL_BOOK_TABLE = "book_table"
COL_DISH_LIKED = "dish_liked"
COL_URL = "url"

CITY_ALIASES: dict[str, str] = {
    "bengaluru": "Bangalore",
    "bangalore": "Bangalore",
    "banglore": "Bangalore",
    "bengalore": "Bangalore",
    "new delhi": "New Delhi",
    "delhi": "New Delhi",
    "gurgaon": "Gurgaon",
    "gurugram": "Gurgaon",
    "mumbai": "Mumbai",
    "bombay": "Mumbai",
    "kolkata": "Kolkata",
    "calcutta": "Kolkata",
    "chennai": "Chennai",
    "madras": "Chennai",
    "hyderabad": "Hyderabad",
    "pune": "Pune",
    "ahmedabad": "Ahmedabad",
    "jaipur": "Jaipur",
    "lucknow": "Lucknow",
    "chandigarh": "Chandigarh",
    "indore": "Indore",
    "goa": "Goa",
    "kochi": "Kochi",
    "cochin": "Kochi",
    "noida": "Noida",
    "ghaziabad": "Ghaziabad",
    "faridabad": "Faridabad",
}

# Known metro names for validation when parsing addresses
KNOWN_METROS = set(CITY_ALIASES.values())


def _normalize_city(raw: str | None) -> str | None:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    text = str(raw).strip()
    if not text or text.lower() in ("nan", "none", "-", "delivery only", "india"):
        return None
    key = text.lower().strip()
    if key in CITY_ALIASES:
        return CITY_ALIASES[key]
    # Strip trailing metro from strings like "BTM Bangalore"
    for metro in KNOWN_METROS:
        if text.lower().endswith(metro.lower()):
            return metro
    if text.title() in KNOWN_METROS:
        return text.title()
    return None


def _city_from_address(address: Any) -> str | None:
    """Extract metro city from address (comma segments, then full-text scan)."""
    if address is None or (isinstance(address, float) and pd.isna(address)):
        return None
    text = str(address).strip()
    if not text:
        return None

    parts = [p.strip() for p in text.split(",") if p.strip()]
    for segment in reversed(parts[-3:] if parts else []):
        city = _normalize_city(segment)
        if city:
            return city

    lowered = text.lower()
    for alias, canonical in sorted(CITY_ALIASES.items(), key=lambda x: -len(x[0])):
        if alias in lowered:
            return canonical
    for metro in KNOWN_METROS:
        if metro.lower() in lowered:
            return metro
    return None


def _normalize_cuisine(raw: str | None) -> str:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return "Unknown"
    text = str(raw).strip()
    if not text or text.lower() in ("nan", "none"):
        return "Unknown"
    return text


def _parse_rating(raw: Any) -> float:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return 0.0
    text = str(raw).strip()
    if not text or text.lower() in ("nan", "none", "new", "-"):
        return 0.0
    match = re.search(r"(\d+\.?\d*)", text)
    if not match:
        return 0.0
    value = float(match.group(1))
    if "/5" in text.lower() or value <= 5.0:
        return min(max(value, 0.0), 5.0)
    if value <= 10.0:
        return min(max(value / 2.0, 0.0), 5.0)
    return min(max(value, 0.0), 5.0)


def _parse_cost(raw: Any) -> float | None:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    text = str(raw).strip().lower()
    if not text or text in ("nan", "none", "-"):
        return None
    numbers = re.findall(r"\d+", text.replace(",", ""))
    if not numbers:
        return None
    if len(numbers) >= 2 and ("-" in text or "to" in text):
        low, high = int(numbers[0]), int(numbers[1])
        value = (low + high) / 2.0
    else:
        value = float(numbers[0])
    if value <= 0:
        return None
    return value


def _stable_id(name: str, city: str, area: str = "") -> str:
    key = f"{name.strip().lower()}|{city.strip().lower()}|{area.strip().lower()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def assign_budget_tiers(costs: pd.Series) -> pd.Series:
    """Assign low / medium / high from percentile ranks of valid costs."""
    tiers = pd.Series(BudgetTier.UNKNOWN.value, index=costs.index, dtype=object)
    valid = costs.dropna()
    if valid.empty:
        return tiers
    if len(valid) == 1:
        tiers.loc[valid.index] = BudgetTier.MEDIUM.value
        return tiers
    p33 = valid.quantile(0.33)
    p66 = valid.quantile(0.66)
    for idx, value in valid.items():
        if value <= p33:
            tiers.loc[idx] = BudgetTier.LOW.value
        elif value <= p66:
            tiers.loc[idx] = BudgetTier.MEDIUM.value
        else:
            tiers.loc[idx] = BudgetTier.HIGH.value
    return tiers


def preprocess_dataframe(df: pd.DataFrame) -> tuple[list[Restaurant], dict[str, Any]]:
    """
    Transform raw dataset DataFrame into validated Restaurant models.

    Returns restaurants and ingestion statistics.
    """
    if df.empty:
        raise ValueError("Dataset is empty")

    stats: dict[str, Any] = {
        "input_rows": len(df),
        "dropped_missing_name": 0,
        "dropped_missing_city": 0,
        "dropped_duplicates": 0,
    }

    work = df.copy()

    # Metro city from address; `listed_in(city)` in this dataset is area/neighborhood
    if COL_ADDRESS in work.columns:
        work["_city"] = work[COL_ADDRESS].apply(_city_from_address)
    else:
        work["_city"] = None
    if COL_LISTED_AREA in work.columns:
        work["_listed_area"] = work[COL_LISTED_AREA].astype(str).str.strip()
    else:
        work["_listed_area"] = ""

    missing_name_mask = work[COL_NAME].isna() | (work[COL_NAME].astype(str).str.strip() == "")
    stats["dropped_missing_name"] = int(missing_name_mask.sum())
    work = work[~missing_name_mask]

    stats["dropped_missing_city"] = int(work["_city"].isna().sum())
    work = work[work["_city"].notna()]

    work["_area"] = (
        work[COL_AREA].astype(str).str.strip()
        if COL_AREA in work.columns
        else ""
    )
    work["_cuisine"] = work[COL_CUISINES].apply(_normalize_cuisine) if COL_CUISINES in work.columns else "Unknown"
    work["_rating"] = work[COL_RATE].apply(_parse_rating) if COL_RATE in work.columns else 0.0
    work["_cost"] = (
        work[COL_COST].apply(_parse_cost) if COL_COST in work.columns else None
    )

    before_dedup = len(work)
    work["_id"] = work.apply(
        lambda r: _stable_id(str(r[COL_NAME]), str(r["_city"]), str(r.get("_area", ""))),
        axis=1,
    )
    work = work.drop_duplicates(subset=["_id"], keep="first")
    stats["dropped_duplicates"] = before_dedup - len(work)

    work["_budget_tier"] = assign_budget_tiers(work["_cost"])
    # Rows without cost get medium tier so all records are filterable (Phase 1 acceptance)
    unknown_mask = work["_budget_tier"] == BudgetTier.UNKNOWN.value
    work.loc[unknown_mask, "_budget_tier"] = BudgetTier.MEDIUM.value

    restaurants: list[Restaurant] = []
    for _, row in work.iterrows():
        metadata: dict[str, Any] = {}
        if COL_ADDRESS in work.columns and pd.notna(row.get(COL_ADDRESS)):
            metadata["address"] = str(row[COL_ADDRESS]).strip()
        if COL_AREA in work.columns and pd.notna(row.get(COL_AREA)):
            metadata["area"] = str(row[COL_AREA]).strip()
        if "_listed_area" in work.columns and row.get("_listed_area"):
            listed = str(row["_listed_area"]).strip()
            if listed and listed.lower() not in ("nan", "none"):
                metadata["listed_area"] = listed
        if COL_VOTES in work.columns and pd.notna(row.get(COL_VOTES)):
            try:
                metadata["votes"] = int(row[COL_VOTES])
            except (TypeError, ValueError):
                pass
        if COL_REST_TYPE in work.columns and pd.notna(row.get(COL_REST_TYPE)):
            metadata["rest_type"] = str(row[COL_REST_TYPE]).strip()
        if COL_ONLINE_ORDER in work.columns and pd.notna(row.get(COL_ONLINE_ORDER)):
            metadata["online_order"] = str(row[COL_ONLINE_ORDER]).strip()
        if COL_BOOK_TABLE in work.columns and pd.notna(row.get(COL_BOOK_TABLE)):
            metadata["book_table"] = str(row[COL_BOOK_TABLE]).strip()
        if COL_DISH_LIKED in work.columns and pd.notna(row.get(COL_DISH_LIKED)):
            metadata["dish_liked"] = str(row[COL_DISH_LIKED]).strip()
        if COL_URL in work.columns and pd.notna(row.get(COL_URL)):
            metadata["url"] = str(row[COL_URL]).strip()

        restaurants.append(
            Restaurant(
                id=str(row["_id"]),
                name=str(row[COL_NAME]).strip(),
                location=str(row["_city"]),
                cuisine=str(row["_cuisine"]),
                rating=float(row["_rating"]),
                cost_for_two=row["_cost"] if pd.notna(row["_cost"]) else None,
                budget_tier=BudgetTier(str(row["_budget_tier"])),
                metadata=metadata,
            )
        )

    stats["output_rows"] = len(restaurants)
    stats["cities"] = sorted({r.location for r in restaurants})
    stats["city_count"] = len(stats["cities"])
    stats["cuisine_samples"] = sorted({r.cuisine for r in restaurants})[:20]
    stats["budget_tier_counts"] = {
        tier.value: sum(1 for r in restaurants if r.budget_tier == tier)
        for tier in BudgetTier
    }

    logger.info(
        "Preprocessed %d -> %d restaurants (%d cities)",
        stats["input_rows"],
        stats["output_rows"],
        stats["city_count"],
    )
    return restaurants, stats


def preprocess_dataset(df: pd.DataFrame) -> list[Restaurant]:
    """Convenience wrapper returning only restaurants."""
    restaurants, _ = preprocess_dataframe(df)
    return restaurants
