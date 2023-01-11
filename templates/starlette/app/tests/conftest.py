import typing as t

import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> t.Generator:
    with TestClient(app) as c:
        yield c
