import pytest
from fastapi.testclient import TestClient

from relay.main import create_app


@pytest.fixture
def app(tmp_path):
    return create_app(tmp_path / "test.sqlite")


@pytest.fixture
def client(app):
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        yield client


def login(client, role="agent"):
    response = client.post("/api/v1/demo/session", json={"role": role})
    assert response.status_code == 200, response.text
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    return response.json()


@pytest.fixture
def logged(client):
    login(client)
    return client
