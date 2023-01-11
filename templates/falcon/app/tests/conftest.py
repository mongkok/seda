import pytest
from falcon import testing

from app.main import app


@pytest.fixture(scope="module")
def client() -> testing.TestClient:
    return testing.TestClient(app)
