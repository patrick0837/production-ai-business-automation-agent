from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_create_business_request_rejects_empty_source():
    response = client.post(
        "/api/v1/requests",
        json={
            "source": "",
            "content": "Test business request",
        },
    )

    assert response.status_code == 422


def test_create_business_request_rejects_empty_content():
    response = client.post(
        "/api/v1/requests",
        json={
            "source": "website",
            "content": "",
        },
    )

    assert response.status_code == 422