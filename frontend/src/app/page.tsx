import ApprovalCard from "@/components/approval-card";
import { getDashboardData } from "@/lib/api";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-IE", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function StatusBadge({
                       value,
                     }: {
  value: string;
}) {
  const className = value
      .replaceAll("_", "-")
      .toLowerCase();

  return (
      <span className={`badge badge-${className}`}>
      {value.replaceAll("_", " ")}
    </span>
  );
}

export default async function Home() {
  const {
    health,
    ready,
    requests,
    pendingActions,
    auditEvents,
  } = await getDashboardData();

  const recentRequests = requests.slice(0, 8);
  const recentAuditEvents = [...auditEvents]
      .sort(
          (a, b) =>
              b.event_sequence - a.event_sequence,
      )
      .slice(0, 8);

  return (
      <main className="dashboard">
        <header className="hero">
          <div>
            <p className="eyebrow">
              Production AI Operations
            </p>

            <h1>
              Business Automation Agent
            </h1>

            <p className="subtitle">
              Live operations dashboard for
              AI-assisted request processing,
              RAG, agent actions, human approval,
              and auditability.
            </p>
          </div>

          <div className="environment-chip">
            {health?.environment ??
                "backend unavailable"}
          </div>
        </header>

        <section className="metrics-grid">
          <article className="metric-card">
            <span>API Health</span>

            <strong>
              {health?.status ?? "offline"}
            </strong>

            <small>
              {health?.version ?? "No response"}
            </small>
          </article>

          <article className="metric-card">
            <span>Readiness</span>

            <strong>
              {ready?.status ?? "offline"}
            </strong>

            <small>
              Dependencies
            </small>
          </article>

          <article className="metric-card">
            <span>Business Requests</span>

            <strong>
              {requests.length}
            </strong>

            <small>
              Persisted requests
            </small>
          </article>

          <article className="metric-card">
            <span>Pending Approvals</span>

            <strong>
              {pendingActions.length}
            </strong>

            <small>
              Human decisions required
            </small>
          </article>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">
                Request Processing
              </p>

              <h2>
                Recent Business Requests
              </h2>
            </div>

            <span className="count">
            {requests.length} total
          </span>
          </div>

          <div className="table-wrapper">
            <table>
              <thead>
              <tr>
                <th>Status</th>
                <th>Source</th>
                <th>Category</th>
                <th>Priority</th>
                <th>Intent</th>
                <th>Created</th>
              </tr>
              </thead>

              <tbody>
              {recentRequests.map(
                  (request) => (
                      <tr key={request.id}>
                        <td>
                          <StatusBadge
                              value={request.status}
                          />
                        </td>

                        <td>
                          {request.source}
                        </td>

                        <td>
                          {request.category ?? "—"}
                        </td>

                        <td>
                          {request.priority ?? "—"}
                        </td>

                        <td>
                          {request.intent ?? "—"}
                        </td>

                        <td>
                          {formatDate(
                              request.created_at,
                          )}
                        </td>
                      </tr>
                  ),
              )}
              </tbody>
            </table>

            {recentRequests.length === 0 && (
                <p className="empty-state">
                  No business requests found.
                </p>
            )}
          </div>
        </section>

        <section className="two-column-grid">
          <article className="panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">
                  Human-in-the-loop
                </p>

                <h2>
                  Pending Agent Actions
                </h2>
              </div>

              <span className="count">
              {pendingActions.length}
            </span>
            </div>

            <div className="stack">
              {pendingActions.map((action) => (
                  <ApprovalCard
                      key={action.id}
                      action={action}
                  />
              ))}

              {pendingActions.length === 0 && (
                  <p className="empty-state">
                    No approvals currently waiting.
                  </p>
              )}
            </div>
          </article>

          <article className="panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">
                  Auditability
                </p>

                <h2>
                  Recent Audit Events
                </h2>
              </div>

              <span className="count">
              {auditEvents.length}
            </span>
            </div>

            <div className="stack">
              {recentAuditEvents.map(
                  (event) => (
                      <div
                          className="list-card"
                          key={event.id}
                      >
                        <div>
                          <strong>
                            #{event.event_sequence}{" "}
                            {event.event_type}
                          </strong>

                          <p>
                            {event.actor_type} ·{" "}
                            {formatDate(
                                event.created_at,
                            )}
                          </p>
                        </div>
                      </div>
                  ),
              )}

              {recentAuditEvents.length === 0 && (
                  <p className="empty-state">
                    No audit events found.
                  </p>
              )}
            </div>
          </article>
        </section>
      </main>
  );
}