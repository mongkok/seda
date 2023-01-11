from starlette import status
from starlette.testclient import TestClient


def test_endpoints(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
