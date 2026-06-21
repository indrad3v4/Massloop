from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    suno_api_key: str = ""
    suno_base_url: str = "https://api.cometapi.com"
    openai_api_key: str = ""
    deepseek_api_key: str = ""

    data_dir: str = "data"
    cors_origins: str = "*"

    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_endpoint: str = ""
    r2_bucket_name: str = ""
    r2_public_url: str = ""

    daily_budget_eur: float = 10.0
    max_track_cost_eur: float = 3.0
    default_track_duration_s: int = 30
    max_polling_time_s: int = 120
    log_level: str = "INFO"
    use_mock_generation: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
