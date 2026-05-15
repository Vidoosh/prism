"""Application configuration from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    sanity_project_id: str = Field(default="", alias="SANITY_PROJECT_ID")
    sanity_studio_project_id: str = Field(default="", alias="SANITY_STUDIO_PROJECT_ID")
    sanity_dataset: str = Field(default="production", alias="SANITY_DATASET")
    sanity_api_token: str = Field(default="", alias="SANITY_API_TOKEN")

    hubspot_access_token: str = Field(default="", alias="HUBSPOT_ACCESS_TOKEN")

    apify_api_token: str = Field(default="", alias="APIFY_API_TOKEN")

    backend_url: str = Field(default="http://localhost:8000", alias="BACKEND_URL")
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")

    gemini_model: str = Field(default="gemini-2.5-flash-lite", alias="GEMINI_MODEL")
    # Model for Gemini + Google Search grounding (google-genai SDK)
    gemini_google_search_model: str = Field(
        default="gemini-2.5-flash-lite",
        alias="GEMINI_GOOGLE_SEARCH_MODEL",
    )

    sanity_studio_url: str = Field(default="", alias="SANITY_STUDIO_URL")
    hubspot_portal_id: str = Field(default="", alias="HUBSPOT_PORTAL_ID")

    failed_writes_dir: str = Field(default="failed_writes", alias="FAILED_WRITES_DIR")
    storage_dir: str = Field(default="storage", alias="STORAGE_DIR")

    # Max concurrent pipeline runs in batch
    batch_concurrency: int = Field(default=3, alias="BATCH_CONCURRENCY")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
