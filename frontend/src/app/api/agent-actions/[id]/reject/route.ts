const BACKEND_BASE_URL =
    process.env.BACKEND_BASE_URL ??
    "http://127.0.0.1:8000";

type Context = {
    params: Promise<{
        id: string;
    }>;
};

type RejectBody = {
    reason?: string;
};

export async function POST(
    request: Request,
    context: Context,
) {
    const { id } = await context.params;

    const body =
        (await request.json()) as RejectBody;

    const reason = body.reason?.trim();

    if (!reason) {
        return Response.json(
            {
                detail:
                    "Rejection reason is required",
            },
            {
                status: 400,
            },
        );
    }

    try {
        const response = await fetch(
            `${BACKEND_BASE_URL}/api/v1/agent-actions/${id}/reject`,
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json",
                },
                body: JSON.stringify({
                    reason,
                }),
                cache: "no-store",
            },
        );

        const responseBody =
            await response.text();

        return new Response(responseBody, {
            status: response.status,
            headers: {
                "Content-Type":
                    response.headers.get(
                        "Content-Type",
                    ) ?? "application/json",
            },
        });
    } catch {
        return Response.json(
            {
                detail:
                    "Backend rejection service unavailable",
            },
            {
                status: 502,
            },
        );
    }
}