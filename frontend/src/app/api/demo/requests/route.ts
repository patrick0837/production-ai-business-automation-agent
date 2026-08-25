const BACKEND_BASE_URL =
    process.env.BACKEND_BASE_URL ??
    "http://127.0.0.1:8000";

type DemoRequestBody = {
    content?: string;
};

export async function POST(
    request: Request,
) {
    let body: DemoRequestBody;

    try {
        body =
            (await request.json()) as DemoRequestBody;
    } catch {
        return Response.json(
            {
                detail: "Invalid JSON body",
            },
            {
                status: 400,
            },
        );
    }

    const content = body.content?.trim();

    if (!content) {
        return Response.json(
            {
                detail: "Demo request content is required",
            },
            {
                status: 400,
            },
        );
    }

    try {
        const response = await fetch(
            `${BACKEND_BASE_URL}/api/v1/demo/requests`,
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/json",
                },
                body: JSON.stringify({
                    content,
                }),
                cache: "no-store",
            },
        );

        const responseBody =
            await response.text();

        return new Response(
            responseBody,
            {
                status: response.status,
                headers: {
                    "Content-Type":
                        response.headers.get(
                            "Content-Type",
                        ) ??
                        "application/json",
                },
            },
        );
    } catch {
        return Response.json(
            {
                detail:
                    "Public demo backend unavailable",
            },
            {
                status: 502,
            },
        );
    }
}