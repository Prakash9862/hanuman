from pydantic import SecretStr

from hanuman.core.config import settings

if __name__ == "__main__":
    for key, value in settings.model_dump().items():
        if hasattr(value, "get_secret_value"):
            value = value.get_secret_value()
        print(f"{key}: {value}")


def test_settings_contains_expected_fields() -> None:
    data = settings.model_dump()

    assert data["app_env"] == settings.app_env
    assert isinstance(data["notion_token"], SecretStr)
    assert isinstance(data["github_token"], SecretStr)
    assert isinstance(data["openai_api_key"], SecretStr)


def test_settings_secret_values_accessible() -> None:
    assert isinstance(settings.notion_token.get_secret_value(), str)
    assert isinstance(settings.github_token.get_secret_value(), str)
    assert isinstance(settings.openai_api_key.get_secret_value(), str)
