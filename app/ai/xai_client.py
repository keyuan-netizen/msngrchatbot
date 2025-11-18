"""Client for interacting with the xAI chat completions API."""

from __future__ import annotations

from typing import Iterable, List, Optional

import httpx

from ..config import get_settings
from .vector_store import VectorDocument


class XAIClient:
    """Lightweight wrapper around the xAI Grok API."""

    API_URL = "https://api.x.ai/v1/chat/completions"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.xai_api_key
        self.model = model or settings.llm_model

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.model)

    async def generate_answer(
        self, question: str, contexts: Iterable[VectorDocument], tone: str = "concise"
    ) -> str:
        if not self.is_configured:
            raise RuntimeError("XAI_API_KEY or model missing.")

        snippets: List[str] = []
        for ctx in contexts:
            snippets.append(f"- {ctx.text}")
        knowledge_block = "\n".join(snippets) if snippets else "No stored knowledge available."
        system_prompt = (
            "You are a helpful assistant answering customer questions for a Facebook Page. "
            "Use the provided knowledge snippets when possible. Keep replies concise and natural."
        )
        user_prompt = (
            f"Answer the customer's question succinctly.\n\n"
            f"Question: {question}\n\n"
            f"Relevant knowledge:\n{knowledge_block}\n\n"
            f"Reply tone: {tone}."
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(self.API_URL, json=payload, headers=headers)
            response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
