"""FastAPI entrypoint for the Messenger automation backend."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from .ai.pipeline import AutomationPipeline, DraftResponse
from .ai.vector_store import LocalVectorStore
from .config import get_settings
from .db import engine, get_session
from .ingestion.service import IngestionService
from .messenger.graph import MessengerGraphClient
from .models import Base, Conversation, MessageLog


logger = logging.getLogger("webhook")


def bootstrap_app() -> FastAPI:
    settings = get_settings()
    Base.metadata.create_all(bind=engine)

    vector_store = LocalVectorStore(settings.chroma_path)
    pipeline = AutomationPipeline(vector_store=vector_store, settings=settings)
    ingestion = IngestionService(vector_store=vector_store)
    messenger_client = MessengerGraphClient(page_access_token=settings.page_access_token)

    app = FastAPI(
        title="Messenger Automation Backend",
        version="0.1.0",
        description="Automation pipeline integrating Messenger webhook, knowledge ingestion, and AI drafting.",
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        body = await request.body()
        body_text = body.decode("utf-8", errors="ignore")
        logger.info(
            "HTTP %s %s headers=%s body=%s",
            request.method,
            request.url.path,
            dict(request.headers),
            body_text,
        )
        request._body = body
        return await call_next(request)

    @app.get("/healthz")
    def healthz() -> Dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    @app.get("/meta/webhook", response_class=PlainTextResponse)
    def verify_webhook(
        mode: str = Query(..., alias="hub.mode"),
        token: str = Query(..., alias="hub.verify_token"),
        challenge: str = Query(..., alias="hub.challenge"),
    ) -> str:
        verified = messenger_client.verify_webhook(mode, token, challenge)
        if not verified:
            raise HTTPException(status_code=403, detail="Verification failed")
        return verified

    @app.post("/meta/webhook")
    async def ingest_event(
        request: Request, session: Session = Depends(get_session)
    ) -> Dict[str, str]:
        raw_body = await request.body()
        body_text = raw_body.decode("utf-8", errors="ignore")
        logger.info("Webhook hit raw=%s", body_text)
        try:
            payload: Dict[str, Any] = json.loads(body_text or "{}")
        except json.JSONDecodeError as exc:
            logger.warning("Invalid JSON received: %s", exc)
            raise HTTPException(status_code=400, detail="Invalid payload")

        entry = payload.get("entry", [{}])[0]
        messaging = entry.get("messaging", [{}])[0]
        sender_id = messaging.get("sender", {}).get("id")
        message_text = messaging.get("message", {}).get("text")
        if not sender_id or not message_text:
            raise HTTPException(status_code=400, detail="Invalid Messenger payload")

        conversation = pipeline.ensure_conversation(
            session=session, messenger_id=sender_id, incoming_text=message_text
        )
        draft = pipeline.draft_reply(message_text, conversation_id=conversation.id)
        pipeline.record_assistant_reply(session, conversation, draft)
        session.commit()
        return {"status": "queued"}

    @app.post("/admin/knowledge/text")
    async def upload_text_snippet(
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        title = payload.get("title")
        text = payload.get("text")
        metadata = payload.get("metadata") or {}
        if not title or not text:
            raise HTTPException(status_code=422, detail="Missing title or text payload")
        doc_ids = ingestion.ingest_text(title=title, text=text, metadata=metadata)
        return {"ingested": len(doc_ids), "doc_ids": doc_ids}

    @app.post("/admin/knowledge/file")
    async def upload_file_snippet(
        file: UploadFile = File(...),
    ) -> Dict[str, Any]:
        doc_ids = await ingestion.ingest_file(file)
        return {"ingested": len(doc_ids), "doc_ids": doc_ids}

    @app.get("/admin/conversations")
    def list_conversations(
        limit: int = Query(50, ge=1, le=200),
        session: Session = Depends(get_session),
    ) -> Dict[str, Any]:
        conversations: List[Conversation] = (
            session.query(Conversation)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .all()
        )
        data = []
        for convo in conversations:
            last_message: Optional[MessageLog] = (
                session.query(MessageLog)
                .filter_by(conversation_id=convo.id)
                .order_by(MessageLog.created_at.desc())
                .first()
            )
            data.append(
                {
                    "id": convo.id,
                    "status": convo.status,
                    "confidence": convo.confidence,
                    "preview": convo.last_message_preview,
                    "last_message": last_message.content if last_message else None,
                    "updated_at": convo.updated_at.isoformat(),
                }
            )
        return {"items": data, "count": len(data)}

    return app


app = bootstrap_app()
