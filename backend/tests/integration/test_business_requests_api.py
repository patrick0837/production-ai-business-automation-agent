from httpx import ASGITransport, AsyncClient

from backend.app.main import app


async def test_create_and_list_business_request(
        override_database,
):
    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        # Create a business request.
        create_response = await client.post(
            "/api/v1/requests",
            json={
                "source": "integration-test",
                "content": "Test enterprise automation request",
            },
        )

        assert create_response.status_code == 202

        created = create_response.json()

        assert created["id"] is not None
        assert created["source"] == "integration-test"
        assert created["content"] == "Test enterprise automation request"
        assert created["status"] == "queued"
        assert created["celery_task_id"] is not None

        # List business requests.
        list_response = await client.get(
            "/api/v1/requests"
        )

        assert list_response.status_code == 200

        requests = list_response.json()

        assert len(requests) == 1
        assert requests[0]["id"] == created["id"]
        assert requests[0]["source"] == "integration-test"
        assert (
                requests[0]["content"]
                == "Test enterprise automation request"
        )
        assert requests[0]["status"] == "queued"
        assert (
                requests[0]["celery_task_id"]
                == created["celery_task_id"]
        )