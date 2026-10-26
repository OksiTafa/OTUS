from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from config.app import AppConfig
from config.database import DatabaseConfig

CONFIG_DIR = Path(__file__).resolve().parent
ENVS_DIR = CONFIG_DIR / "envs"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_prefix="BLOG_APP__",  # suffix: two underscore chars
        env_nested_delimiter="__",  # two underscore chars
        env_file=(
            ENVS_DIR / ".env.template",
            ENVS_DIR / ".env",
        ),
    )

    app: AppConfig
    db: DatabaseConfig


settings = Settings()
