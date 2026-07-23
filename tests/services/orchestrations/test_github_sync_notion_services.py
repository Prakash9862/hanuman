import importlib

from dotenv import load_dotenv

load_dotenv()


def test_module_importable() -> None:
    m = importlib.import_module("hanuman.services.orchestrations.github_sync_notion_services")
    assert m is not None
