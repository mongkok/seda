from falcon import testing


def test_resources(client: testing.TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
