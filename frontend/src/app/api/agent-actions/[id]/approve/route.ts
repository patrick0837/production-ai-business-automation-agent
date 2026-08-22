const BACKEND_BASE_URL =
    process.env.BACKEND_BASE_URL ??
    "http://127.0.0.1:8000";

type Context = {
    params: Promise<{
        id: string;
    }>;
};

export async function POST(
    _request: Request,
    context: Context,
) {
    const { id } = await context.params;

    try {
        const response = await fetch(
            `${BACKEND_BASE_URL}/api/v1/agent-actions/${id}/approve`,
            {
                method: "POST",
                cache: "no-store",
            },
        );

        const body = await response.text();

        return new Response(body, {
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
                    "Backend approval service unavailable",
            },
            {
                status: 502,
            },
        );
    }
}