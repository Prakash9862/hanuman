import pytest
from fastapi.testclient import TestClient

from hanuman.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-token", "Content-Type": "application.json"}
