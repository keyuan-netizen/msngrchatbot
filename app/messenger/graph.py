"""Thin wrapper around the Messenger Graph API."""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from ..config import get_settings


class MessengerGraphClient:
    """Send messages and perform webhook verification."""

    def __init__(self, page_access_token: Optional[str] = None) -> None:
        settings = get_settings()
        self.page_access_token = page_access_token or settings.page_access_token
        self.base_url = str(settings.graph_api_base_url).rstrip("/")

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Validate the verification token."""
        settings = get_settings()
        if mode == "subscribe" and token == settings.verify_token:
            return challenge
        return None

    def send_message(self, recipient_id: str, text: str) -> Dict[str, Any]:
        """Send an outbound message via Graph API."""
        if not self.page_access_token:
            raise RuntimeError("PAGE_ACCESS_TOKEN is not configured.")
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text},
            "messaging_type": "RESPONSE",
        }
        url = f"{self.base_url}/me/messages"
        params = {"access_token": self.page_access_token}
        response = httpx.post(url, params=params, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
