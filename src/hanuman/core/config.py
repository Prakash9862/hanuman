from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from hanuman.core.logging import get_logger

logger = get_logger(__name__)


class Settings(BaseSettings):
    # === Base ===
    app_env: str = "dev"
    debug: bool = False
    log_level: str = "DEBUG"
    log_dir: str = "logs"
    log_to_file: bool = True
    enable_api_docs: bool = True

    # === 🔐 Secrets obligatoires ===
    notion_token: SecretStr = Field(default=..., alias="NOTION_TOKEN")
    github_token: SecretStr = Field(default=..., alias="GITHUB_TOKEN")
    openai_api_key: SecretStr = Field(default=..., alias="OPENAI_API_KEY")

    # === 🔐 Secrets spécifiques (Google) ===
    google_client_id: str = Field(default=..., alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default=..., alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(default=..., alias="GOOGLE_REDIRECT_URI")

    # === ⚙️ Configs spécifiques ===
    openai_model: str = "gpt-4o"
    notion_base_url: str = "https://api.notion.com/v1"
    github_api_url: str = "https://api.github.com/"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=True
    )


settings = Settings()
