# Production-Ready AI Business Automation Agent

A production-style AI business automation platform built with FastAPI, PostgreSQL, pgvector, Redis, Celery, Ollama, n8n, Next.js, Docker, AWS, and GitHub Actions.

The system accepts business requests, processes them asynchronously, uses an AI agent to analyze the request and call tools, retrieves relevant internal knowledge through RAG, requires human approval before protected actions, and records an ordered audit trail for traceability.

---

## Overview

This project demonstrates how an AI agent can be integrated into a production-style backend system rather than used as a standalone chatbot.

The platform supports:

- Business request intake through REST APIs and authenticated webhooks
- Asynchronous processing with Celery and Redis
- Local AI inference with Ollama
- AI-driven business request classification
- Agent tool calling
- Retrieval-Augmented Generation (RAG)
- PostgreSQL + pgvector semantic search
- Human-in-the-Loop approval for protected actions
- Ordered audit trail
- n8n business workflow orchestration
- Next.js operations dashboard
- Dockerized services
- AWS deployment
- GitHub Actions CI

---

## End-to-End Workflow

A validated AWS end-to-end workflow:

```text
Business Request
        ↓
n8n
        ↓
FastAPI
        ↓
PostgreSQL
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

In the AWS validation flow, the agent searched for an internal incident-response policy and retrieved the relevant knowledge chunk with a semantic similarity of approximately `0.821`.

The agent then requested the protected `escalate_incident` tool. The action was blocked until a human approved it.

The audit trail recorded:

```text
agent_tool_requested
tool_executed
agent_tool_requested
approval_required
action_approved
tool_executed
```

---

## Architecture

```text
                     ┌─────────────────────┐
                     │      Next.js UI     │
                     │ Operations Dashboard│
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │      FastAPI        │
                     │ REST / Webhooks     │
                     └──────────┬──────────┘
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
             ▼                  ▼                  ▼
   ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
   │   PostgreSQL    │ │      Redis      │ │      n8n        │
   │    pgvector     │ │ Celery Broker   │ │ Orchestration   │
   └────────┬────────┘ └────────┬────────┘ └─────────────────┘
            │                   │
            │                   ▼
            │        ┌─────────────────────┐
            │        │   Celery Worker     │
            │        └──────────┬──────────┘
            │                   │
            │                   ▼
            │        ┌─────────────────────┐
            │        │   Ollama / Qwen3    │
            │        │ AI Analysis + Agent │
            │        └──────────┬──────────┘
            │                   │
            │                   ▼
            │        ┌─────────────────────┐
            └───────►│ RAG / Tool Calling  │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │ Human-in-the-Loop   │
                     │ Approval / Reject   │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │   Audit Trail       │
                     └─────────────────────┘
```

---

## Core Components

### FastAPI Backend

The backend provides:

- Business request APIs
- Authenticated webhook intake
- Agent action APIs
- Human approval / rejection endpoints
- Audit event APIs
- Health and readiness endpoints

Example endpoints:

```text
POST /api/v1/requests
POST /api/v1/webhooks/business-requests
POST /api/v1/agent-actions/{action_id}/approve
POST /api/v1/agent-actions/{action_id}/reject
```

---

## Async Processing

Business requests are processed asynchronously using:

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

---

## AI Provider

The system uses Ollama for local/self-hosted AI inference.

Current production-style deployment uses:

```text
Model:
qwen3:4b-instruct

Embedding Model:
nomic-embed-text:v1.5
```

This allows the project to run without relying on paid external AI APIs.

---

## Retrieval-Augmented Generation

The RAG pipeline supports:

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

A validated AWS retrieval returned:

```text
Document:
Incident Response Policy

Source:
internal-policy

Similarity:
~0.821
```

---

## AI Agent

The AI agent can select and execute registered tools.

Current tools include:

```text
search_knowledge_base
escalate_incident
```

The agent uses the knowledge-base search tool when business-specific policy or guidance is needed.

High-impact tools such as `escalate_incident` require explicit human approval.

---

## Human-in-the-Loop

Protected agent actions are never executed immediately.

The workflow is:

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

The n8n workflow provides a human approval form that allows an operator to approve or reject the proposed action.

---

## Audit Trail

Every important agent action is persisted as an ordered audit event.

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

---

## n8n Orchestration

n8n is used as the business orchestration layer rather than as the core application backend.

The workflow handles:

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

---

## Frontend

The Next.js frontend acts as an operations dashboard.

It displays:

- Backend health
- Readiness status
- Business request counts
- Business requests
- Pending approvals
- Audit events

The frontend uses a server-side backend integration pattern rather than directly exposing internal service URLs to the browser.

---

## AWS Deployment

The complete stack has been deployed and validated on AWS EC2.

AWS deployment components:

```text
PostgreSQL + pgvector
Redis
FastAPI
Celery Worker
Ollama
n8n
Next.js
```

All services run through Docker Compose.

Internal infrastructure services such as PostgreSQL, Redis, and Ollama are not exposed publicly.

During development and validation, the application services were accessed securely through SSH tunnels instead of opening application ports directly to the internet.

Example development access pattern:

```text
Local Browser
      ↓
SSH Tunnel
      ↓
AWS EC2
      ↓
Next.js / FastAPI / n8n
```

---

## Docker

Production-style containerization includes:

- Backend Docker image
- Next.js standalone production image
- PostgreSQL + pgvector
- Redis
- Ollama
- n8n

The frontend uses the Next.js standalone build output to reduce the production image footprint.

---

## CI

GitHub Actions validates the application on pushes and pull requests.

Current CI pipeline includes:

```text
Backend Tests
Frontend Lint
Frontend Production Build
Docker Build
```

The project currently implements CI.

Automated production deployment is intentionally not claimed as completed CD.

---

## Testing

The backend test suite includes `61 passing tests`.

Test coverage includes areas such as:

- API behavior
- Business request lifecycle
- Agent actions
- Human approval
- Webhooks
- RAG behavior
- Audit trail behavior

---

## Reliability Features

The project includes:

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

Implemented security-related controls include:

- Webhook shared-secret authentication
- Protected agent actions requiring human approval
- Internal Docker service networking
- Database / Redis / Ollama not publicly exposed
- Secrets stored outside Git
- n8n encryption key stored in runtime environment
- AWS infrastructure accessed through SSH

Public production exposure is intentionally not enabled yet.

Before public deployment, the next security layer would include:

- Application authentication
- Authorization / roles
- HTTPS
- Secure reverse proxy or load balancer
- Public-domain configuration
- Additional rate limiting and security hardening

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
├── alembic/
├── .github/
│   └── workflows/
├── compose.aws.yaml
└── README.md
```

---

## Local Development

The project is designed to run through Docker-based infrastructure combined with local application development.

Required services include:

- PostgreSQL
- Redis
- Ollama

Environment configuration is provided through local environment variables.

Secrets must never be committed to Git.

---

## Production-Style Design Decisions

This project intentionally avoids unnecessary architectural complexity.

The system does not use Kubernetes, Kafka, or large-scale microservice decomposition because they are not required for the current workload.

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

The goal is to demonstrate production-oriented engineering decisions rather than simply maximize the number of technologies used.

---

## Project Status

Core application and AWS end-to-end workflow are complete.

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
- n8n workflow
- Next.js frontend
- Docker deployment
- AWS deployment
- GitHub Actions CI

Remaining work is primarily presentation, security hardening for public exposure, and optional deployment automation.

---

## Why This Project

The purpose of this project is to demonstrate the integration of modern AI capabilities with traditional software engineering practices.

Rather than building a simple chatbot, the system combines:

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
