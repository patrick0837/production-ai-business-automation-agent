# Production-Ready AI Business Automation Agent

A production-style AI business automation platform that combines **FastAPI, PostgreSQL + pgvector, Redis, Celery, Ollama, n8n, Next.js, Docker, AWS EC2, Cloudflare Tunnel, and GitHub Actions**.

The system accepts business requests, processes them asynchronously, uses an AI agent to analyze requests and call tools, retrieves internal policy through RAG, pauses protected actions for human approval, records ordered audit events for traceability, and exposes a demo-safe interactive workflow through the Next.js operations dashboard.

> **Live Demo:** [https://agent.edmondbeaumont.com](https://agent.edmondbeaumont.com)
>
> The public demo is served over HTTPS through a Cloudflare Named Tunnel to the AWS EC2 production stack. The EC2 instance can be started or stopped independently without changing the public hostname.

---

## Key Highlights

- **AI Agent Tool Calling** — the agent can select and invoke registered tools based on request context.
- **Retrieval-Augmented Generation** — semantic search over internal knowledge using Ollama embeddings and PostgreSQL + pgvector.
- **Human-in-the-Loop Governance** — protected actions require explicit human approval before execution.
- **Async Processing** — Redis + Celery decouple request intake from long-running AI processing.
- **Workflow Orchestration** — n8n coordinates request submission, polling, timeout handling, approval, and protected action execution.
- **Interactive Public Demo** — a demo-safe Next.js workflow is publicly reachable at `agent.edmondbeaumont.com` and can submit simulated business incidents, surface request state, approvals, protected action execution, and audit evidence.
- **Operations Dashboard** — Next.js UI surfaces health, readiness, requests, pending approvals, and audit events.
- **Public Demo Hardening** — demo request rate limiting, loopback-only host port bindings, secret isolation, and Cloudflare Tunnel reduce unnecessary public exposure.
- **AWS Deployment** — the full Docker Compose stack is deployed on AWS EC2 with Cloudflare Tunnel providing the fixed HTTPS public entry point.
- **Auditability** — ordered persistent audit events capture tool requests, approvals, rejections, and execution results.
- **CI Validation** — GitHub Actions runs backend tests, frontend lint/build checks, and Docker build validation.
- **64 Passing Backend Tests** — covering core API, workflow, agent, webhook, approval, RAG, audit, and demo-request behavior.

---

## Architecture

![Production-Ready AI Business Automation Agent Architecture](docs/images/architecture.png)

---

## Operations Dashboard

The operations dashboard provides a live view of request processing, pending human approvals, and ordered audit events.

![Operations Dashboard](docs/images/dashboard-full.png)

---

## Interactive Public Demo

The frontend includes a demo-safe interactive business incident flow designed to demonstrate the full request lifecycle without exposing internal service URLs directly to the browser.

**Public URL:** [https://agent.edmondbeaumont.com](https://agent.edmondbeaumont.com)

A simulated incident can be submitted from the dashboard and followed through the real backend workflow:

```text
Public Browser
        ↓
Cloudflare HTTPS / Named Tunnel
        ↓
Next.js Demo Submission
        ↓
FastAPI
        ↓
PostgreSQL
        ↓
Redis / Celery
        ↓
Ollama AI Analysis
        ↓
RAG / pgvector Retrieval
        ↓
Agent Tool Calling
        ↓
Protected Agent Action
        ↓
Awaiting Approval
        ↓
Browser Human Approve / Reject
        ↓
Protected Tool Execution
        ↓
Completed
        ↓
Ordered Audit Trail
```

The demo uses the real application workflow while restricting public intake to a demo-safe endpoint. Request rate limiting is applied at the Next.js server layer before requests are forwarded to the FastAPI demo API.

The validated browser flow produced:

```text
public-live-demo → Completed
Pending Approvals → 0
action_approved
tool_executed
```

![Interactive Public Demo](docs/images/public-live-demo.png)

The same lifecycle was validated on the AWS EC2 production stack, including AI analysis, RAG retrieval, Human-in-the-Loop approval, protected tool execution, request completion, and ordered persistent audit events.

![AWS Production Public Demo Validation](docs/images/aws-public-demo-complete.png)

The final public path is independent of the EC2 public IPv4 address:

```text
agent.edmondbeaumont.com
        ↓
Cloudflare Named Tunnel
        ↓
cloudflared (Docker Compose)
        ↓
frontend:3000
        ↓
api:8000
```

The tunnel and application stack were also validated after Docker Compose restart, and the public hostname remained unchanged across EC2 stop/start operations.

---

## n8n Human-in-the-Loop Workflow

This workflow orchestrates business request processing, polling, timeout handling, human approval, and protected action execution inside n8n.

![n8n Human-in-the-Loop Workflow](docs/images/n8n-hitl-workflow.png)

---

## AWS RAG and Audit Evidence

A validated AWS end-to-end run shows the agent retrieving the relevant internal incident-response policy, requesting a protected escalation action, waiting for human approval, and recording the complete ordered audit trail.

![AWS RAG and Audit Evidence](docs/images/aws-rag-audit-evidence.png)

---

## Validated End-to-End Flow

```text
Business Request
        ↓
n8n
        ↓
FastAPI
        ↓
Redis / Celery
        ↓
Ollama Qwen3
        ↓
AI Analysis
        ↓
Agent Tool Calling
        ↓
search_knowledge_base
        ↓
Ollama Embeddings
        ↓
PostgreSQL + pgvector
        ↓
Relevant Internal Policy
        ↓
Protected Agent Action
        ↓
Human Approval
        ↓
Tool Execution
        ↓
Ordered Audit Trail
```

A real AWS validation run retrieved:

```text
Document: Incident Response Policy
Source: internal-policy
Similarity: ~0.821
```

The same run then produced the following ordered audit sequence:

```text
agent_tool_requested
tool_executed
agent_tool_requested
approval_required
action_approved
tool_executed
```

---

## Core Components

### FastAPI Backend

The backend provides:

- Business request APIs
- Demo-safe request submission API
- Authenticated webhook intake
- Agent action APIs
- Human approval / rejection endpoints
- Audit event APIs
- Health and readiness endpoints

Example endpoints:

```text
POST /api/v1/requests
POST /api/v1/demo/requests
POST /api/v1/webhooks/business-requests
POST /api/v1/agent-actions/{action_id}/approve
POST /api/v1/agent-actions/{action_id}/reject
```

### Async Processing

Business requests are processed asynchronously through:

```text
FastAPI
→ Redis
→ Celery Worker
```

The worker handles:

- AI request analysis
- Agent execution
- RAG retrieval
- Tool calling
- Approval-required state transitions
- Retryable dependency failures

The AWS deployment uses a resource-conscious Celery configuration with worker concurrency limited to one process.

### AI Provider

The system uses Ollama for local/self-hosted AI inference.

```text
Model:
qwen3:4b-instruct

Embedding Model:
nomic-embed-text:v1.5
```

This allows the project to run without relying on paid external AI APIs.

### Retrieval-Augmented Generation

The RAG pipeline follows:

```text
Knowledge Document
        ↓
Text Chunking
        ↓
Embedding Generation
        ↓
PostgreSQL + pgvector
        ↓
Query Embedding
        ↓
Cosine Similarity Search
        ↓
Relevant Knowledge Chunk
```

Embeddings use `768` dimensions.

### AI Agent

The current registered tools include:

```text
search_knowledge_base
escalate_incident
```

The agent uses `search_knowledge_base` when a request depends on business-specific policy or guidance.

High-impact tools such as `escalate_incident` require human approval.

### Human-in-the-Loop

Protected actions are not executed immediately.

```text
Agent requests protected action
        ↓
approval_required
        ↓
Human reviews request
        ↓
Approve / Reject
        ↓
Protected tool execution
```

### Audit Trail

Important agent and approval activity is persisted as ordered audit events.

Examples:

```text
agent_tool_requested
tool_executed
approval_required
action_approved
action_rejected
```

This provides traceability for:

- What the agent requested
- Which tools were executed
- Which actions required approval
- What decision the human made
- What result the protected action produced

### n8n Orchestration

n8n is used as the orchestration layer rather than the core application backend.

```text
Submit Business Request
        ↓
Poll Request Status
        ↓
Awaiting Approval?
        ↓
Get Pending Agent Action
        ↓
Human Approval
        ↓
Approve / Reject
```

The workflow includes:

- Polling
- Processing timeout protection
- Completed-state handling
- Failure handling
- Unexpected-state handling
- Human approval forms

AWS polling timeout: `300 seconds`.

### Frontend

The Next.js operations dashboard displays:

- Backend health
- Readiness status
- Business request counts
- Business requests
- Pending approvals
- Audit events
- Interactive demo-safe business incident submission
- Live workflow state visibility

The frontend uses a server-side backend integration pattern rather than exposing internal service URLs directly to the browser.

---

## AWS Deployment

The complete stack has been deployed and validated on AWS EC2.

Deployment components:

```text
PostgreSQL + pgvector
Redis
FastAPI
Celery Worker
Ollama
n8n
Next.js
cloudflared
```

All services run through Docker Compose on **Amazon Linux 2023**.

The public application entry point is:

```text
https://agent.edmondbeaumont.com
        ↓
Cloudflare HTTPS
        ↓
Cloudflare Named Tunnel
        ↓
cloudflared
        ↓
Next.js frontend
        ↓
FastAPI backend
```

The Cloudflare connector is managed by `compose.aws.yaml` with `restart: unless-stopped`, so it starts with the rest of the stack instead of relying on a manually launched tunnel process. The Cloudflare route targets `http://frontend:3000` over the Docker network.

Public host bindings are intentionally restricted:

```text
Frontend  → 127.0.0.1:3000
FastAPI   → 127.0.0.1:8000
n8n       → 127.0.0.1:5678
```

PostgreSQL, Redis, and Ollama are not published on host ports. Public browser traffic reaches the application through Cloudflare Tunnel rather than direct application-port exposure.

The fixed hostname is independent of the EC2 public IPv4 address, allowing the instance to be stopped and restarted without changing the public demo URL.

---

## Docker

Production-style containerization includes:

- Backend Docker image
- Next.js standalone production image
- PostgreSQL + pgvector
- Redis
- Ollama
- n8n

The frontend uses the Next.js standalone build output for its production container.

---

## CI

GitHub Actions validates the application on pushes and pull requests.

Current CI checks include:

```text
Backend Tests
Frontend Lint
Frontend Production Build
Docker Build
```

The project currently implements **CI**.

Automated production deployment is not claimed as completed CD.

---

## Testing

The backend test suite currently has:

```text
64 passing tests
```

Coverage includes:

- API behavior
- Business request lifecycle
- Demo request submission
- Agent actions
- Human approval
- Webhooks
- RAG behavior
- Audit trail behavior

---

## Reliability and Observability

Implemented reliability and observability features include:

- Health endpoint
- Readiness endpoint
- Structured logging
- Request IDs
- Async processing
- Retryable dependency handling
- Processing timeout protection
- Persistent audit events
- Human approval gates
- Docker health checks

---

## Security Design

Implemented controls include:

- Webhook shared-secret authentication
- Protected agent actions requiring human approval
- Internal Docker service networking
- PostgreSQL / Redis / Ollama not publicly exposed
- Frontend, FastAPI, and n8n host bindings restricted to `127.0.0.1`
- Public HTTPS ingress through a Cloudflare Named Tunnel
- Demo request rate limiting before backend dispatch
- Secrets stored outside Git
- Cloudflare Tunnel token supplied at runtime through environment configuration
- n8n encryption key provided at runtime
- AWS infrastructure administration through SSH

The public hostname exposes the demo-safe frontend workflow rather than internal infrastructure services. The browser does not receive internal Docker service URLs.

For a broader multi-user production deployment, additional controls would still be appropriate, such as:

- End-user authentication
- Authorization / roles
- Stronger distributed rate limiting and abuse controls
- Centralized secret management
- Automated security monitoring and alerting

---

## Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- Celery
- Redis
- PostgreSQL
- pgvector

### AI / RAG

- Ollama
- Qwen3
- nomic-embed-text
- Agent Tool Calling
- RAG
- Vector Search

### Automation

- n8n
- Webhooks
- Human-in-the-Loop

### Frontend

- Next.js
- React
- TypeScript

### Infrastructure

- Docker
- Docker Compose
- AWS EC2
- Cloudflare Tunnel
- Cloudflare DNS / HTTPS
- GitHub Actions

---

## Repository Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   ├── ai/
│   │   ├── api/
│   │   ├── db/
│   │   ├── embeddings/
│   │   ├── models/
│   │   ├── rag/
│   │   └── worker/
│   └── Dockerfile
│
├── frontend/
│   ├── app/
│   ├── components/
│   └── Dockerfile
│
├── n8n/
│   └── workflows/
│       └── business-request-hitl.json
│
├── docs/
│   └── images/
│       ├── architecture.png
│       ├── dashboard-full.png
│       ├── public-live-demo.png
│       ├── aws-public-demo-complete.png
│       ├── n8n-hitl-workflow.png
│       └── aws-rag-audit-evidence.png
│
├── alembic/
├── .github/
│   └── workflows/
├── compose.aws.yaml
└── README.md
```

---

## Local Development

The project is designed to run through Docker-based infrastructure combined with local application development.

Required infrastructure services include:

- PostgreSQL
- Redis
- Ollama

Environment configuration is provided through local environment variables.

Secrets must never be committed to Git.

---

## Production-Style Design Decisions

This project intentionally avoids unnecessary architectural complexity.

Kubernetes, Kafka, large-scale microservice decomposition, and multi-agent orchestration were not added simply to increase the technology count.

Instead, the design focuses on:

- Clear service boundaries
- Async background processing
- Reliable persistence
- AI tool governance
- RAG
- Human approval
- Auditability
- Containerization
- Cloud deployment
- Secure public ingress
- Observability

The goal is to demonstrate production-oriented engineering decisions rather than maximize architectural complexity.

---

## Project Status

Core application functionality, the AWS end-to-end workflow, and the public interactive demo are complete and validated.

Validated:

- FastAPI backend
- PostgreSQL + pgvector
- Redis
- Celery
- Ollama AI inference
- Embeddings
- RAG ingestion
- RAG semantic retrieval
- Agent tool calling
- Human-in-the-Loop
- Ordered audit trail
- n8n orchestration
- Next.js frontend
- Interactive Public Demo
- Local demo end-to-end workflow
- AWS browser demo end-to-end workflow
- Fixed public hostname: `agent.edmondbeaumont.com`
- Cloudflare Named Tunnel
- HTTPS public access
- Demo request rate limiting
- Loopback-only host bindings for frontend / FastAPI / n8n
- Docker Compose-managed `cloudflared` service
- Docker Compose restart recovery
- EC2 stop/start recovery without changing the public hostname
- Docker deployment
- AWS deployment
- GitHub Actions CI

The main remaining work is optional operational hardening and optional deployment automation. Automated production deployment is not claimed as completed CD.

---

## Why This Project

The project demonstrates how modern AI capabilities can be integrated with conventional software engineering practices.

Rather than building a standalone chatbot, it combines:

```text
AI
+
Backend Engineering
+
Database Design
+
Async Processing
+
RAG
+
Agent Tool Governance
+
Human Approval
+
Workflow Automation
+
Cloud Deployment
+
Observability
```

into one end-to-end application.

