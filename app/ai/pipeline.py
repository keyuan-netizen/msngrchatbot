"""High-level automation pipeline that wires retrieval + drafting logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy.orm import Session

from ..config import Settings, get_settings
from ..models import Conversation, EscalationTicket, MessageLog, User
from .vector_store import LocalVectorStore, VectorDocument


@dataclass
class DraftResponse:
    """Container for pipeline results."""

    conversation_id: int
    answer: str
    confidence: float
    citations: List[dict]


class AutomationPipeline:
    """Coordinates retrieval, drafting, and escalation decisions."""

    def __init__(
        self,
        vector_store: Optional[LocalVectorStore] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.vector_store = vector_store or LocalVectorStore(self.settings.chroma_path)

    def ensure_conversation(
        self, session: Session, messenger_id: str, incoming_text: str
    ) -> Conversation:
        """Fetch or create a conversation for the sender."""
        user = session.query(User).filter_by(messenger_id=messenger_id).one_or_none()
        if not user:
            user = User(messenger_id=messenger_id, display_name=None)
            session.add(user)
            session.flush()

        conversation = (
            session.query(Conversation)
            .filter_by(user_id=user.id, status="open")
            .order_by(Conversation.updated_at.desc())
            .first()
        )
        if not conversation:
            conversation = Conversation(user_id=user.id, status="open")
            session.add(conversation)
            session.flush()

        session.add(
            MessageLog(
                conversation_id=conversation.id,
                role="user",
                content=incoming_text,
                metadata_json={},
            )
        )
        conversation.last_message_preview = incoming_text[:500]
        return conversation

    def draft_reply(self, message: str, conversation_id: Optional[int] = None) -> DraftResponse:
        """Simulate retrieval + drafting for a Messenger reply."""
        contexts = self.vector_store.similarity_search(
            message, limit=self.settings.max_context_snippets
        )
        confidence = 0.35 + 0.1 * len(contexts)
        answer = self._call_llm(message, contexts)
        citations = [
            {"doc_id": ctx.doc_id, "metadata": ctx.metadata} for ctx in contexts
        ]
        return DraftResponse(
            conversation_id=conversation_id or -1,
            answer=answer,
            confidence=min(confidence, 0.95),
            citations=citations,
        )

    def _call_llm(self, message: str, contexts: List[VectorDocument]) -> str:
        tone = self.settings.answer_tone[0] if self.settings.answer_tone else "helpful"
        summary_parts = [ctx.text[:200] for ctx in contexts]
        context_block = "\n---\n".join(summary_parts) if summary_parts else "No prior knowledge."
        return (
            f"[Tone: {tone}] Based on the knowledge base I found:\n"
            f"{context_block}\n\n"
            f"My reply to the customer would be: "
            f"Thanks for reaching out! {message.strip()} (contextualized above)."
        )

    def record_assistant_reply(
        self, session: Session, conversation: Conversation, draft: DraftResponse
    ) -> None:
        conversation.confidence = draft.confidence
        session.add(
            MessageLog(
                conversation_id=conversation.id,
                role="assistant",
                content=draft.answer,
                metadata_json={"citations": draft.citations},
            )
        )
        session.flush()

    def escalate(
        self,
        session: Session,
        conversation: Conversation,
        reason: str,
        payload: Optional[dict] = None,
    ) -> EscalationTicket:
        ticket = EscalationTicket(
            conversation_id=conversation.id,
            reason=reason,
            payload=payload or {},
        )
        conversation.status = "escalated"
        session.add(ticket)
        session.flush()
        return ticket
