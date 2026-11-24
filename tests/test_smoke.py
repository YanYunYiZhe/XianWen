"""Smoke tests for the project foundation."""

from fastapi.testclient import TestClient

import xianwen


def test_package_importable() -> None:
    assert xianwen.__version__ == "0.1.0"


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "xianwen"}
