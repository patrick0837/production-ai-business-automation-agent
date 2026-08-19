from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "Production-Ready AI Business Automation Agent"
    assert data["version"] == "0.1.0"
    assert data["environment"] == "development"