from httpx import ASGITransport, AsyncClient

from backend.app.api.v1 import webhooks
from backend.app.main import app


TEST_WEBHOOK_SECRET = "integration-test-webhook-secret"


class FakeWebhookSettings:
    webhook_secret = TEST_WEBHOOK_SECRET


def configure_webhook_secret(
        monkeypatch,
) -> None:
    monkeypatch.setattr(
        webhooks,
        "get_settings",
        lambda: FakeWebhookSettings(),
    )


async def test_webhook_rejects_missing_secret(
        override_database,
        monkeypatch,
):
    configure_webhook_secret(
        monkeypatch
    )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/webhooks/business-requests",
            json={
                "source": "webhook-test",
                "content": (
                    "Webhook request without "
                    "authentication"
                ),
            },
        )

    assert response.status_code == 401

    assert (
            response.json()["detail"]
            == "Invalid webhook secret"
    )


async def test_webhook_rejects_invalid_secret(
        override_database,
        monkeypatch,
):
    configure_webhook_secret(
        monkeypatch
    )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/webhooks/business-requests",
            headers={
                "X-Webhook-Secret": (
                    "wrong-secret"
                ),
            },
            json={
                "source": "webhook-test",
                "content": (
                    "Webhook request with "
                    "invalid authentication"
                ),
            },
        )

    assert response.status_code == 401

    assert (
            response.json()["detail"]
            == "Invalid webhook secret"
    )


async def test_webhook_creates_business_request(
        override_database,
        monkeypatch,
):
    configure_webhook_secret(
        monkeypatch
    )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/webhooks/business-requests",
            headers={
                "X-Webhook-Secret": (
                    TEST_WEBHOOK_SECRET
                ),
            },
            json={
                "source": "n8n-test",
                "content": (
                    "Process this webhook "
                    "business request"
                ),
            },
        )

        assert response.status_code == 202

        created = response.json()

        assert created["id"] is not None
        assert created["source"] == "n8n-test"

        assert (
                created["content"]
                == "Process this webhook "
                   "business request"
        )

        assert created["status"] == "queued"

        assert (
                created["celery_task_id"]
                is not None
        )

        list_response = await client.get(
            "/api/v1/requests"
        )

        assert (
                list_response.status_code
                == 200
        )

        requests = (
            list_response.json()
        )

        assert len(requests) == 1

        assert (
                requests[0]["id"]
                == created["id"]
        )

        assert (
                requests[0]["status"]
                == "queued"
        )


async def test_webhook_marks_request_failed_when_dispatch_fails(
        override_database,
        override_failing_task_dispatcher,
        monkeypatch,
):
    configure_webhook_secret(
        monkeypatch
    )

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/webhooks/business-requests",
            headers={
                "X-Webhook-Secret": (
                    TEST_WEBHOOK_SECRET
                ),
            },
            json={
                "source": "n8n-test",
                "content": (
                    "Simulate webhook "
                    "dispatch failure"
                ),
            },
        )

        assert response.status_code == 503

        detail = (
            response.json()["detail"]
        )

        assert detail["status"] == "failed"

        assert (
                detail["request_id"]
                is not None
        )

        list_response = await client.get(
            "/api/v1/requests"
        )

        assert (
                list_response.status_code
                == 200
        )

        requests = (
            list_response.json()
        )

        assert len(requests) == 1

        assert (
                requests[0]["status"]
                == "failed"
        )

        assert (
                requests[0][
                    "celery_task_id"
                ]
                is not None
        )