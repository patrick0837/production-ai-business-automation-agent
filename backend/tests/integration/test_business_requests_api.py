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
        create_response = await client.post(
            "/api/v1/requests",
            json={
                "source": "integration-test",
                "content": (
                    "Test enterprise automation request"
                ),
            },
        )

        assert create_response.status_code == 202

        created = create_response.json()

        assert created["id"] is not None
        assert created["source"] == "integration-test"
        assert (
                created["content"]
                == "Test enterprise automation request"
        )
        assert created["status"] == "queued"
        assert created["celery_task_id"] is not None

        list_response = await client.get(
            "/api/v1/requests"
        )

        assert list_response.status_code == 200

        requests = list_response.json()

        assert len(requests) == 1
        assert requests[0]["id"] == created["id"]
        assert (
                requests[0]["source"]
                == "integration-test"
        )
        assert (
                requests[0]["content"]
                == "Test enterprise automation request"
        )
        assert requests[0]["status"] == "queued"
        assert (
                requests[0]["celery_task_id"]
                == created["celery_task_id"]
        )


async def test_business_request_is_failed_when_dispatch_fails(
        override_database,
        override_failing_task_dispatcher,
):
    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        create_response = await client.post(
            "/api/v1/requests",
            json={
                "source": "integration-test",
                "content": "Simulate broker failure",
            },
        )

        assert create_response.status_code == 503

        detail = create_response.json()["detail"]

        assert detail["status"] == "failed"
        assert detail["request_id"] is not None

        list_response = await client.get(
            "/api/v1/requests"
        )

        assert list_response.status_code == 200

        requests = list_response.json()

        assert len(requests) == 1
        assert requests[0]["status"] == "failed"
        assert requests[0]["celery_task_id"] is not None


async def test_get_business_request_by_id(
        override_database,
):
    transport = ASGITransport(app=app)

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        create_response = await client.post(
            "/api/v1/requests",
            json={
                "source": "status-test",
                "content": (
                    "Retrieve this request "
                    "by its ID"
                ),
            },
        )

        assert create_response.status_code == 202

        created = create_response.json()

        get_response = await client.get(
            f"/api/v1/requests/{created['id']}"
        )

        assert get_response.status_code == 200

        retrieved = get_response.json()

        assert retrieved["id"] == created["id"]
        assert retrieved["source"] == "status-test"
        assert (
                retrieved["content"]
                == "Retrieve this request by its ID"
        )
        assert retrieved["status"] == "queued"
        assert (
                retrieved["celery_task_id"]
                == created["celery_task_id"]
        )


async def test_get_missing_business_request_returns_404(
        override_database,
):
    transport = ASGITransport(app=app)

    missing_request_id = (
        "00000000-0000-0000-0000-000000000001"
    )

    async with AsyncClient(
            transport=transport,
            base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/requests/"
            f"{missing_request_id}"
        )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Business request not found"
    }