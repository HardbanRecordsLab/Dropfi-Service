"""Sprint 4 e-commerce integrations (#9-#11, doku/PLAN_20_FUNKCJI_PONAD_KONKURENCJA.md).

WooCommerce (#9) needs no code here: the plugin at integrations/woocommerce/
calls the existing White-Label API (routes/developer.py::partner_create_job)
directly with its own partner key — DROPIFY never needs to hold WooCommerce
credentials. This file covers the two integrations where DROPIFY has to call
OUT to the merchant's own platform using a token they provide:

- Shopify (#10 "Auto-Ship Studio"): a merchant creates a Shopify Custom App
  (Settings -> Apps -> Develop apps) and pastes its Admin API access token —
  no Shopify Partner account / app-store review needed to use this.
- BaseLinker (#11): a single API token that itself aggregates Allegro,
  WooCommerce and Shopify order/product sync on BaseLinker's side, per
  doku/N8N_AUTOMACJE.md's integration notes — the pragmatic way to reach
  Allegro without a direct OAuth2 integration.
"""
import base64
import hashlib
import hmac
import logging
from datetime import date, datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, StoreConnection, Listing
from app.utils.jobs import create_job_and_match
from app.utils.n8n import notify_n8n

router = APIRouter(prefix="/integrations", tags=["E-commerce Integrations"])
logger = logging.getLogger(__name__)


@router.get("/mine")
def my_store_connections(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conns = db.query(StoreConnection).filter(StoreConnection.user_id == user.id).order_by(StoreConnection.created_at.desc()).all()
    return [
        {
            "id": c.id, "platform": c.platform, "label": c.label,
            "active": c.active, "last_synced_at": c.last_synced_at, "created_at": c.created_at,
        }
        for c in conns
    ]


@router.delete("/{connection_id}")
def disconnect_store(connection_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conn = db.get(StoreConnection, connection_id)
    if not conn or conn.user_id != user.id:
        raise HTTPException(status_code=404, detail="Store connection not found")
    conn.active = False
    db.commit()
    return {"message": "Disconnected"}


# ---------------------------------------------------------------------------
# Shopify
# ---------------------------------------------------------------------------

@router.post("/shopify/connect")
def connect_shopify(
    shop_domain: str = Body(..., embed=True),
    access_token: str = Body(..., embed=True),
    webhook_secret: str = Body("", embed=True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conn = StoreConnection(
        user_id=user.id, platform="shopify",
        label=shop_domain.strip().replace("https://", "").replace("http://", "").rstrip("/"),
        access_token=access_token, webhook_secret=webhook_secret or None,
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return {"id": conn.id, "platform": "shopify", "label": conn.label}


def _verify_shopify_hmac(secret: str, body: bytes, hmac_header: str) -> bool:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    computed = base64.b64encode(digest).decode()
    return hmac.compare_digest(computed, hmac_header or "")


@router.post("/shopify/webhook/{connection_id}")
async def shopify_webhook(connection_id: str, request: Request, db: Session = Depends(get_db)):
    """Inbound: point a Shopify 'products/create' webhook at this URL to
    auto-create a DROPIFY job requesting AI-generated fulfillment content."""
    conn = db.get(StoreConnection, connection_id)
    if not conn or conn.platform != "shopify" or not conn.active:
        raise HTTPException(status_code=404, detail="Unknown or inactive store connection")

    raw_body = await request.body()
    if conn.webhook_secret:
        hmac_header = request.headers.get("x-shopify-hmac-sha256", "")
        if not _verify_shopify_hmac(conn.webhook_secret, raw_body, hmac_header):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payload")

    product_title = payload.get("title") or "New Shopify product"
    product_body = (payload.get("body_html") or "").strip()

    job = create_job_and_match(
        db,
        title=f"Fulfillment content for: {product_title}",
        description=product_body or f"Auto-created from a Shopify product sync ({product_title}). "
                                     "Needs AI-generated listing copy and fulfillment plan.",
        budget=500,
        deadline=date.today() + timedelta(days=7),
        category="E-commerce",
        client_id=conn.user_id,
        source="shopify-sync",
    )
    conn.last_synced_at = datetime.now(timezone.utc)
    db.commit()
    return {"job_id": job.id, "status": "created"}


@router.post("/shopify/{connection_id}/push-listing")
def push_listing_to_shopify(
    connection_id: str,
    product_id: str = Body(..., embed=True),
    listing_id: str = Body(..., embed=True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Push an AI Listing Factory (#F1) draft back into the Shopify product."""
    conn = db.get(StoreConnection, connection_id)
    if not conn or conn.user_id != user.id or conn.platform != "shopify":
        raise HTTPException(status_code=404, detail="Store connection not found")
    listing = db.get(Listing, listing_id)
    if not listing or listing.user_id != user.id:
        raise HTTPException(status_code=404, detail="Listing not found")

    content = listing.content or {}
    try:
        resp = httpx.put(
            f"https://{conn.label}/admin/api/2024-01/products/{product_id}.json",
            headers={"X-Shopify-Access-Token": conn.access_token, "Content-Type": "application/json"},
            json={"product": {
                "id": product_id,
                "title": content.get("title"),
                "body_html": content.get("description", ""),
            }},
            timeout=15,
        )
        resp.raise_for_status()
    except Exception as exc:
        logger.warning("Shopify push failed for connection %s (%s)", connection_id, exc)
        raise HTTPException(status_code=502, detail="Shopify API error — check the store's access token")
    return {"status": "pushed", "product_id": product_id}


# ---------------------------------------------------------------------------
# BaseLinker (Allegro + WooCommerce + Shopify order/product aggregation)
# ---------------------------------------------------------------------------

@router.post("/baselinker/connect")
def connect_baselinker(
    access_token: str = Body(..., embed=True),
    label: str = Body("BaseLinker account", embed=True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conn = StoreConnection(user_id=user.id, platform="baselinker", label=label[:255], access_token=access_token)
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return {"id": conn.id, "platform": "baselinker", "label": conn.label}


@router.post("/baselinker/{connection_id}/sync")
def sync_baselinker_orders(
    connection_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pulls recent BaseLinker orders (Allegro/WooCommerce/Shopify — whatever
    the merchant connected on BaseLinker's side) and creates a DROPIFY job
    for each one that needs a fulfillment service."""
    conn = db.get(StoreConnection, connection_id)
    if not conn or conn.user_id != user.id or conn.platform != "baselinker":
        raise HTTPException(status_code=404, detail="Store connection not found")

    try:
        resp = httpx.post(
            "https://api.baselinker.com/connector.php",
            headers={"X-BLToken": conn.access_token},
            data={"method": "getOrders", "parameters": "{}"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("BaseLinker sync failed for connection %s (%s)", connection_id, exc)
        raise HTTPException(status_code=502, detail="BaseLinker API error — check the access token")

    if data.get("status") != "SUCCESS":
        raise HTTPException(status_code=502, detail=data.get("error_message", "BaseLinker API error"))

    created = 0
    for order in (data.get("orders") or [])[:20]:
        create_job_and_match(
            db,
            title=f"Fulfillment for order #{order.get('order_id', '?')}",
            description=f"Auto-synced from BaseLinker. {len(order.get('products', []) or [])} item(s) to fulfill.",
            budget=300,
            deadline=date.today() + timedelta(days=5),
            category="E-commerce",
            client_id=conn.user_id,
            source="baselinker-sync",
        )
        created += 1

    conn.last_synced_at = datetime.now(timezone.utc)
    db.commit()
    if created:
        notify_n8n("baselinker-sync", {"connection_id": conn.id, "orders_synced": created})
    return {"orders_synced": created}
