from httpx import ASGITransport, AsyncClient

from backend.app.main import app


async def test_create_demo_request(
        override_database,
):
    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/demo/requests",
            json={
                "content": (
                    "Critical production incident detected. "
                    "Database service is unavailable."
                ),
            },
        )

    assert response.status_code == 202

    created = response.json()

    assert created["id"] is not None
    assert created["source"] == "public-live-demo"
    assert (
            created["content"]
            == (
                "Critical production incident detected. "
                "Database service is unavailable."
            )
    )
    assert created["status"] == "queued"
    assert created["celery_task_id"] is not None


async def test_demo_request_rejects_short_content(
        override_database,
):
    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/demo/requests",
            json={
                "content": "short",
            },
        )

    assert response.status_code == 422


async def test_demo_request_rejects_long_content(
        override_database,
):
    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/demo/requests",
            json={
                "content": "x" * 1001,
            },
        )

    assert response.status_code == 422