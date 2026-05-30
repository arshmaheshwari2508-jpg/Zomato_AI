from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    hf_dataset_name: str = "ManikaSaini/zomato-restaurant-recommendation"
    data_cache_path: Path = PROJECT_ROOT / "data" / "cache" / "restaurants.parquet"
    force_refresh_dataset: bool = False

    llm_provider: str = "groq"
    llm_api_key: str = ""
    groq_api_key: str = ""  # alias; LLM_API_KEY takes precedence when set
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 1500
    llm_timeout_seconds: float = 60.0

    max_candidates: int = 30
    default_top_k: int = 5


settings = Settings()
