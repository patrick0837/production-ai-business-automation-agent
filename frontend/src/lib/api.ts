const BACKEND_BASE_URL =
    process.env.BACKEND_BASE_URL ??
    "http://127.0.0.1:8000";

export type HealthResponse = {
    status: string;
    service?: string;
    version?: string;
    environment?: string;
};

export type ReadyResponse = {
    status: string;
    [key: string]: unknown;
};

export type BusinessRequest = {
    id: string;
    source: string;
    content: string;
    status: string;
    celery_task_id?: string | null;
    category?: string | null;
    priority?: string | null;
    intent?: string | null;
    requires_human_approval?: boolean | null;
    recommended_action?: string | null;
    created_at: string;
    updated_at: string;
};

export type AgentAction = {
    id: string;
    business_request_id: string;
    tool_call_id?: string | null;
    tool_name: string;
    arguments: Record<string, unknown>;
    status: string;
    requires_approval: boolean;
    result?: Record<string, unknown> | null;
    created_at: string;
    updated_at: string;
};

export type AuditEvent = {
    id: string;
    event_sequence: number;
    business_request_id?: string | null;
    agent_action_id?: string | null;
    event_type: string;
    actor_type: string;
    actor_id?: string | null;
    details: Record<string, unknown>;
    created_at: string;
};

async function fetchJson<T>(
    path: string,
): Promise<T> {
    const response = await fetch(
        `${BACKEND_BASE_URL}${path}`,
        {
            cache: "no-store",
        },
    );

    if (!response.ok) {
        throw new Error(
            `${path} returned ${response.status}`,
        );
    }

    return response.json() as Promise<T>;
}

export async function getDashboardData() {
    const [
        healthResult,
        readyResult,
        requestsResult,
        actionsResult,
        auditResult,
    ] = await Promise.allSettled([
        fetchJson<HealthResponse>("/health"),
        fetchJson<ReadyResponse>("/ready"),
        fetchJson<BusinessRequest[]>(
            "/api/v1/requests",
        ),
        fetchJson<AgentAction[]>(
            "/api/v1/agent-actions?status=pending_approval",
        ),
        fetchJson<AuditEvent[]>(
            "/api/v1/audit-events",
        ),
    ]);

    return {
        health:
            healthResult.status === "fulfilled"
                ? healthResult.value
                : null,

        ready:
            readyResult.status === "fulfilled"
                ? readyResult.value
                : null,

        requests:
            requestsResult.status === "fulfilled"
                ? requestsResult.value
                : [],

        pendingActions:
            actionsResult.status === "fulfilled"
                ? actionsResult.value
                : [],

        auditEvents:
            auditResult.status === "fulfilled"
                ? auditResult.value
                : [],
    };
}