# tests/test_env_loaded.py

from fastapi.testclient import TestClient

from hanuman.core.config import get_env_var
from hanuman.main import app

client = TestClient(app)


def test_env_variable_accessible() -> None:
    """
    Vérifie que la variable NOTION_TOKEN est bien présente si DEBUG=true.
    """
    debug_mode = get_env_var("DEBUG", "false") == "true"
    expected_preview = get_env_var("NOTION_TOKEN", "")[:6] + "..."

    response = client.get("/status")
    json = response.json()

    if debug_mode:
        assert "notion_token_preview" in json
        assert json["notion_token_preview"] == expected_preview
    else:
        assert "notion_token_preview" not in json
