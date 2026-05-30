"""Load Zomato dataset from Hugging Face or local Parquet cache."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from datasets import load_dataset

from config.settings import settings

logger = logging.getLogger(__name__)


def load_raw_dataset(
    dataset_name: str | None = None,
    use_cache: bool = True,
    cache_path: Path | None = None,
    force_refresh: bool | None = None,
) -> pd.DataFrame:
    """
    Load raw restaurant data.

    Uses Parquet cache when available unless force_refresh is True.
    """
    name = dataset_name or settings.hf_dataset_name
    path = cache_path or settings.data_cache_path
    refresh = force_refresh if force_refresh is not None else settings.force_refresh_dataset

    if use_cache and not refresh and path.exists():
        logger.info("Loading dataset from cache: %s", path)
        return pd.read_parquet(path)

    logger.info("Downloading dataset from Hugging Face: %s", name)
    hf_dataset = load_dataset(name, split="train")
    df = hf_dataset.to_pandas()

    if use_cache:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".parquet.tmp")
        df.to_parquet(tmp, index=False)
        tmp.replace(path)
        logger.info("Cached raw dataset to %s (%d rows)", path, len(df))

    return df


def ingest_and_preprocess(
    force_refresh: bool | None = None,
) -> tuple[pd.DataFrame, list]:
    """Load raw data and run preprocessor; used by CLI."""
    from app.data.preprocessor import preprocess_dataframe

    df = load_raw_dataset(force_refresh=force_refresh)
    return df, preprocess_dataframe(df)


def main() -> None:
    """CLI entry: python -m app.data.loader"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    _, (restaurants, stats) = ingest_and_preprocess(
        force_refresh=settings.force_refresh_dataset,
    )
    from app.data.repository import RestaurantRepository

    repo = RestaurantRepository(restaurants)

    print("\n=== Ingestion complete ===")
    print(f"Input rows:      {stats['input_rows']}")
    print(f"Output rows:     {stats['output_rows']}")
    print(f"Dropped (name):  {stats['dropped_missing_name']}")
    print(f"Dropped (city):  {stats['dropped_missing_city']}")
    print(f"Dropped (dupes): {stats['dropped_duplicates']}")
    print(f"Cities:          {stats['city_count']}")
    print(f"Sample cities:   {', '.join(stats['cities'][:8])}")
    print(f"Budget tiers:    {stats['budget_tier_counts']}")

    bangalore = repo.get_by_city("Bangalore")
    print(f"\nRestaurants in Bangalore: {len(bangalore)}")
    if bangalore:
        sample = bangalore[0]
        print(f"Sample: {sample.name} | {sample.cuisine} | {sample.rating} | {sample.budget_tier.value}")


if __name__ == "__main__":
    main()
