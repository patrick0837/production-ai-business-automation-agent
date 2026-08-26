const BACKEND_BASE_URL =
    process.env.BACKEND_BASE_URL ??
    "http://127.0.0.1:8000";

type DemoRequestBody = {
    content?: string;
};

const RATE_LIMIT_WINDOW_MS = 60_000;
const RATE_LIMIT_MAX_REQUESTS = 1;

type RateLimitEntry = {
    count: number;
    windowStart: number;
};

const rateLimitStore =
    new Map<string, RateLimitEntry>();

function getClientIp(
    request: Request,
): string {
    const forwardedFor =
        request.headers.get("x-forwarded-for");

    if (forwardedFor) {
        return forwardedFor
            .split(",")[0]
            .trim();
    }

    return (
        request.headers.get(
            "x-real-ip",
        ) ?? "unknown"
    );
}

function isRateLimited(
    clientIp: string,
): boolean {
    const now = Date.now();

    const existing =
        rateLimitStore.get(clientIp);

    if (
        !existing ||
        now - existing.windowStart >=
        RATE_LIMIT_WINDOW_MS
    ) {
        rateLimitStore.set(
            clientIp,
            {
                count: 1,
                windowStart: now,
            },
        );

        return false;
    }

    if (
        existing.count >=
        RATE_LIMIT_MAX_REQUESTS
    ) {
        return true;
    }

    existing.count += 1;

    return false;
}

export async function POST(
    request: Request,
) {
    const clientIp =
        getClientIp(request);

    if (isRateLimited(clientIp)) {
        return Response.json(
            {
                detail:
                    "Public demo rate limit exceeded. Please try again in one minute.",
            },
            {
                status: 429,
                headers: {
                    "Retry-After": "60",
                },
            },
        );
    }

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

    const content =
        body.content?.trim();

    if (!content) {
        return Response.json(
            {
                detail:
                    "Demo request content is required",
            },
            {
                status: 400,
            },
        );
    }

    if (content.length > 1000) {
        return Response.json(
            {
                detail:
                    "Demo request content must not exceed 1000 characters",
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