from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    suno_api_key: str = ""
    data_dir: str = "data"
    cors_origins: str = "*"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()
