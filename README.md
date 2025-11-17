# Messenger Automation Blueprint

This document captures the technical plan for building a full-stack automation layer that answers Facebook Messenger inquiries using AI and an existing knowledge base.

## System Goals
- Identify target Facebook Pages, response-time SLAs, tone/voice, and escalation rules before implementation.
- Ensure compliance with Meta messaging policies, privacy requirements, and internal data-handling standards.

## Architecture Overview
- **Frontend Admin Console**: SPA (React/Vue) for knowledge uploads, live conversation monitoring, manual overrides, and analytics; protected via SSO/OAuth.
- **Backend API**: Node/Express or FastAPI service that exposes REST/GraphQL endpoints, handles auth/rate limiting/logging, and hosts the Messenger webhook.
- **Data Layer**:
  - Postgres for users, conversations, message logs, and escalation tickets.
  - Vector store (pgvector, Pinecone, Weaviate) containing embedded knowledge snippets.
  - Object storage (S3/GCS) for raw documents and transcripts.

## Messenger Integration
1. Create a Facebook App + Page; request `pages_manage_metadata`, `pages_messaging`, `pages_read_engagement`.
2. Implement webhook endpoint (`/meta/webhook`) to receive message events and verification handshakes.
3. Store the Page Access Token securely (KMS/Secrets Manager) and refresh when required.
4. Send replies via Graph API `/<PAGE_ID>/messages`.

## AI & Response Pipeline
1. Webhook event enqueues a job (SQS/RabbitMQ) for durability.
2. Classifier or rule engine routes to auto-answer vs. human escalation vs. spam.
3. Retrieval step queries the vector store using embeddings (OpenAI/Cohere) filtered by metadata.
4. LLM call (GPT-4o, Claude, or self-hosted) with a system prompt defining tone/voice and guardrails.
5. Post-processing enforces length limits, policy filters, and toxicity checks.
6. Send Messenger reply, log metadata, confidence scores, and source snippets.
7. Trigger human handoff when confidence is low or user requests an agent; push ticket + transcript into CRM or internal queue.

## Admin Console Features
- Knowledge management: upload FAQs/PDFs and trigger embedding jobs.
- Conversation monitor: live feed with takeover controls for agents.
- Analytics: automation %, median response time, escalation reasons.
- Settings: prompt editor, business hours, escalation recipients, compliance toggles.

## Infrastructure & Operations
- Deploy backend/workers via containers (Docker/Kubernetes) or serverless (Lambda) with low-latency webhook handling.
- Enforce HTTPS (ACM/Let’s Encrypt), structured logging, metrics (Prometheus), and alerting for Graph API/webhook failures.
- Respect Meta’s 24-hour messaging window, encrypt PII, maintain audit logs of responses and knowledge citations.
- Run CI/CD with linting, unit/integration tests, and golden Q&A regression tests; back up databases and vector store regularly.

## Future Enhancements
- Continuous ingestion from resolved human tickets to update the knowledge base.
- Multi-language detection plus translation layer.
- Proactive outreach flows (e.g., Click-to-Messenger ads) feeding into the automation pipeline.


## Component,Best Tool
Backend,Python 
Vector DB,Chroma (local) or Qdrant Cloud
LLM,Grok API (witty) or GPT-4o (reliable)
Hosting,Render.com (free tier + easy deploys)
Knowledge Ingestion,"Unstructured.io (PDFs, docs → text)"

---

## Implementation Snapshot

This repository now includes a FastAPI backend (Python) that wires together the blueprint components:

- **Webhook + Admin API**: `app/main.py` boots the FastAPI service, mounts `/meta/webhook` for Messenger events, `/admin/knowledge/*` for knowledge uploads, and `/admin/conversations` for observability.
- **Data Layer**: `app/models.py` captures users, conversations, message logs, and escalation tickets using SQLAlchemy. Configure Postgres via `DATABASE_URL`; SQLite can be used for local tinkering.
- **Vector DB**: `app/ai/vector_store.py` persists embeddings inside a local Chroma instance under `data/vectorstore`.
- **LLM Pipeline**: `app/ai/pipeline.py` performs retrieval + Grok drafting (via the xAI chat completions API) and opens escalation tickets whenever confidence drops below the set threshold.
- **Knowledge Ingestion**: `app/ingestion/service.py` leans on Unstructured.io to parse uploads before chunking and embedding content.
- **Messenger Delivery**: `app/messenger/graph.py` wraps the Graph API, enforcing Meta’s policies before replying and logging metadata for analytics/escalations.

## Getting Started

1. **Install dependencies** (Python 3.11 recommended; several dependencies lack 3.13 wheels.)

   ```bash
   pyenv install 3.11.8 --skip-existing
   pyenv local 3.11.8  # optional but avoids Python 3.13 build failures
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment** – copy `.env.example` → `.env` and populate:

   - `DATABASE_URL` pointing at Postgres (Render.com free tier works for hosting).
   - `GROK_API_KEY` for the Messenger response LLM (`LLM_MODEL` defaults to `grok-2`).
   - `OPENAI_API_KEY` + `EMBEDDING_PROVIDER=openai` if you want managed embeddings.
   - Set `EMBEDDING_PROVIDER=local` (optional) to avoid OpenAI entirely; this uses a deterministic hash-based embedding that runs fully offline. Tune `LOCAL_EMBEDDING_DIMENSION` if you need larger vectors.
   - `PAGE_ID`, `PAGE_ACCESS_TOKEN`, and `VERIFY_TOKEN` from your Meta app.
   - `CHROMA_PATH` if you prefer a non-default vector store directory.
   - `ANSWER_TONE` listing permitted tone strings (semicolon-delimited) that the admin assist endpoint can use.

3. **Run database migrations** (optional for local dev):

   ```bash
   alembic upgrade head  # migrations not provided yet; use SQLAlchemy metadata.create_all for now
   ```

4. **Launch the API**

   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

   - `GET /healthz` → readiness probe.
   - `POST /admin/knowledge/text` → manual snippets.
   - `POST /admin/knowledge/file` → upload PDFs/docs (Unstructured.io → Chroma embeddings).

5. **Wire the webhook**

   - Point the Meta webhook URL to `https://<host>/meta/webhook`.
   - Verify with the same token as `VERIFY_TOKEN`.
   - Incoming messages queue through `AutomationPipeline`, which either:
     - Responds automatically using Grok + Chroma context.
     - Opens an escalation ticket when retrieval confidence is low (ready for human takeover in your CRM or custom UI).

6. **Knowledge + Admin Console**

   - `POST /admin/knowledge/file` handles PDF/Doc ingestion using Unstructured.io.
   - `GET /admin/conversations` returns the latest 50 threads, their statuses, and confidence scores for a lightweight monitoring view that a future React/Vue console can consume.

7. **Testing**

   ```bash
   pytest
   ```

## Deployment Notes

- Containerize the FastAPI app and deploy to Render.com’s free tier; mount persistent disks for `data/vectorstore`.
- Use Render cron/worker services for dedicated ingestion jobs if you expect large documents.
- Configure Secrets Manager (Render environment vars or AWS Secrets Manager) for access tokens + API keys.
- Set up CI/CD to run `pytest`, linting, and golden Q&A regression suites before deploying.

## Next Steps

- Build the React/Vue Admin Console that consumes the `/admin` endpoints for uploads, live monitoring, and analytics dashboards.
- Expand the queueing layer (SQS, RabbitMQ, or Celery) so webhook handling stays sub-second even under heavy load.
- Add automated PII redaction + translation services before embeddings to comply with global privacy requirements.
