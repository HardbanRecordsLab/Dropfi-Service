"""n8n integration: fire platform events to self-hosted n8n webhooks (HMAC-signed).

Events are dispatched asynchronously via Celery when available, otherwise inline.
All events are fire-and-forget: failures never break platform flows.
"""
import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

EVENT_TIMEOUT = 5.0


def _post(url: str, body: str, signature: str) -> dict:
    try:
        resp = httpx.post(
            url,
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Dropify-Signature": signature,
                "User-Agent": "DROPIFY/1.0",
            },
            timeout=EVENT_TIMEOUT,
        )
        logger.info("n8n event %s -> HTTP %s", url, resp.status_code)
        return {"ok": True, "status": resp.status_code}
    except Exception as exc:
        logger.warning("n8n event failed %s: %s", url, exc)
        return {"error": str(exc)}


def notify_n8n(event: str, payload: dict) -> None:
    """Send a signed event to n8n webhook: <N8N_WEBHOOK_URL>/dropify-<event>."""
    if not settings.N8N_WEBHOOK_URL or not settings.N8N_WEBHOOK_SECRET:
        return

    url = f"{settings.N8N_WEBHOOK_URL.rstrip('/')}/dropify-{event}"
    body = json.dumps(
        {
            "event": f"dropify-{event}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload,
        },
        ensure_ascii=False,
        default=str,
    )
    signature = "sha256=" + hmac.new(
        settings.N8N_WEBHOOK_SECRET.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    try:
        from app.tasks.n8n_sync import dispatch_n8n_event
        dispatch_n8n_event.delay(url, body, signature)
    except Exception:
        _post(url, body, signature)
