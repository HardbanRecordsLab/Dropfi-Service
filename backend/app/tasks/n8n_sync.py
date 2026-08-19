"""Celery task for async n8n webhook dispatch (retry-safe, non-blocking)."""
import logging

import httpx
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="app.tasks.n8n_sync.dispatch_n8n_event", autoretry_for=(httpx.TransportError,), retry_backoff=30, max_retries=2)
def dispatch_n8n_event(url: str, body: str, signature: str) -> dict:
    try:
        resp = httpx.post(
            url,
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Dropify-Signature": signature,
                "User-Agent": "DROPIFY/1.0",
            },
            timeout=5.0,
        )
        return {"ok": True, "status": resp.status_code}
    except Exception as exc:
        logger.warning("n8n dispatch failed %s: %s", url, exc)
        raise
